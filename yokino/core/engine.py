"""Yokino Agent 主循环引擎"""

import logging
from typing import Any, Iterator

from config import get_config
from core.llm.base import LLMBackend
from core.llm.api_backend import APIBackend
from core.llm.local_backend import LocalBackend
from core.tools.base import Tool
from memory.store import MessageStore
from memory.user_profile import UserProfile

logger = logging.getLogger("yokino")


class Agent:
    """Agent 主循环"""

    # System prompt 定义 Yokino 的身份和能力
    SYSTEM_PROMPT = """你是 Yokino，一个贴心的个人 AI 生活学习工作助理。
你像伙伴一样和用户对话，语气自然亲切，但保持专业。

能力说明：
- 你的知识来自训练的 LLM，联网搜索请使用搜索工具
- 你可以读写文件、管理笔记、设置提醒
- 你会记住对话历史，但每次重启后只保留最近的对话
- 用户在中国，注意使用中国大陆可访问的服务

回复风格：
- 日常对话简短自然，不要过于正式
- 需要展示信息时用清晰的格式
- 不确定的事直接说不知道，不要编造"""

    def __init__(self):
        self.store = MessageStore()
        self.backends: list[LLMBackend] = [APIBackend(), LocalBackend()]
        self.tools: dict[str, Tool] = {}

        # 加载用户长期记忆
        self._user_profile = UserProfile()
        user_facts = self._user_profile.to_prompt()
        if user_facts:
            self.SYSTEM_PROMPT = self.SYSTEM_PROMPT + "\n\n====\n" + user_facts + "\n===="

        # Session ID（暂时用固定值，后续支持多会话）
        self.session_id = "default"

    def register_tool(self, tool: Tool):
        """注册一个工具"""
        self.tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")

    def _get_active_backend(self) -> LLMBackend | None:
        """获取可用的 LLM 后端（优先 API，失败切本地）"""
        for backend in self.backends:
            if backend.is_available():
                return backend
        return None

    def _build_tool_defs(self) -> list[dict] | None:
        """构建 OpenAI 格式的 tool 定义列表"""
        if not self.tools:
            return None
        return [t.to_openai_tool() for t in self.tools.values()]

    def chat(self, message: str) -> Iterator[str]:
        """发送消息，返回流式回复

        流程：
        1. 保存用户消息到历史
        2. 获取可用后端（API → 本地）
        3. 构建 messages（system + 历史）
        4. 调用 LLM（含 tool defs）
        5. 处理 stream 输出和 tool_use
        6. 若 tool_use → 执行工具 → 继续循环
        7. 返回最终回复
        """
        self.store.add_message(self.session_id, role="user", content=message)

        backend = self._get_active_backend()
        if backend is None:
            yield "⚠️ 没有可用的 LLM 后端。请检查 API 配置或确保 Ollama 正在运行。"
            return

        yield from self._chat_loop(backend)

    def _chat_loop(self, backend: LLMBackend) -> Iterator[str]:
        """Agent 循环：调用 LLM → 处理工具 → 继续直到得到文字回复"""
        tool_defs = self._build_tool_defs()
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # 构建消息（system prompt 由后端处理）
            messages = self.store.get_history(self.session_id)

            # 调用 LLM
            try:
                response = backend.chat(
                    messages=messages,
                    tools=tool_defs,
                    system=self.SYSTEM_PROMPT,
                    stream=True,
                )
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                # 尝试降级到下一个后端
                fallback = self._get_fallback_backend(backend)
                if fallback:
                    logger.info(f"降级到后端: {fallback.name}")
                    yield f"\n[API 不可用，切换到 {fallback.name} 模式]\n"
                    yield from self._chat_loop(fallback)
                    return
                yield f"\n❌ 发生错误: {e}"
                return

            # 收集流式输出
            collected_content = ""
            for chunk in response:
                if isinstance(chunk, str):
                    collected_content += chunk
                    yield chunk

            # 流结束后再检查 tool calls
            tool_call_data = backend.get_tool_call_result(None)

            # 检查 tool calls
            if tool_call_data:
                yield "\n\n"  # 分隔 LLM 输出和执行结果
                tool_call_details, tool_results = self._execute_tools(tool_call_data)

                # 保存 assistant 消息（含 tool_calls，OpenAI 格式）
                self.store.add_message(
                    self.session_id,
                    role="assistant",
                    content=collected_content if collected_content else None,
                    tool_calls=tool_call_details,
                )
                # 保存 tool 结果消息
                for tr in tool_results:
                    self.store.add_message(
                        self.session_id, role="tool",
                        content=tr["content"],
                        tool_call_id=tr["tool_call_id"],
                    )

                # 继续循环 — LLM 基于 tool 结果继续回复
                continue
            else:
                # 纯文字回复，保存并结束
                if collected_content:
                    self.store.add_message(self.session_id, role="assistant", content=collected_content)
                return

        yield "\n\n⚠️ 已达到最大迭代次数，停止。"
        return

    def _get_fallback_backend(self, current: LLMBackend) -> LLMBackend | None:
        """获取 current 之后的第一个可用后端"""
        found_current = False
        for backend in self.backends:
            if backend is current:
                found_current = True
                continue
            if found_current and backend.is_available():
                return backend
        return None

    def _execute_tools(self, tool_call_data: dict) -> tuple[list[dict], list[dict]]:
        """执行工具调用，返回 (tool_call_details, tool_results)

        tool_call_details: OpenAI 格式 tool_calls 列表
        tool_results: [{"tool_call_id": "...", "content": "..."}]
        """
        import json
        details = []
        results = []
        for choice in tool_call_data.get("choices", []):
            tool_name = choice.get("name", "")
            tool_input = choice.get("input", {})
            tool_id = choice.get("id", "")

            # 构建 OpenAI 格式的 tool_call
            details.append({
                "id": tool_id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(tool_input, ensure_ascii=False),
                },
            })

            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name].execute(**tool_input)
                    results.append({"tool_call_id": tool_id, "content": result})
                    logger.info(f"工具执行成功: {tool_name}")
                except Exception as e:
                    error_msg = f"工具 [{tool_name}] 执行失败: {e}"
                    results.append({"tool_call_id": tool_id, "content": error_msg})
                    logger.error(error_msg)
            else:
                results.append({"tool_call_id": tool_id, "content": f"未知工具: {tool_name}"})
        return details, results

    def clear_history(self):
        """清空当前会话历史"""
        self.store.clear_session(self.session_id)
