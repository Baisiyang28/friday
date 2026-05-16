"""API LLM 后端 — 支持 DeepSeek 和 Claude"""

from typing import Any, Iterator

from openai import OpenAI

from config import get_config
from core.llm.base import LLMBackend


class APIBackend(LLMBackend):
    """API 后端，支持 DeepSeek (OpenAI 兼容) 和 Claude"""

    name = "api"

    def __init__(self):
        cfg = get_config().llm.api
        self.provider = cfg.provider
        self.model = ""
        self._client = None
        self._pending_tool_calls: dict = {}

        if self.provider == "deepseek":
            dcfg = cfg.deepseek
            self.model = dcfg.model or "deepseek-chat"
            if dcfg.api_key:
                self._client = OpenAI(
                    api_key=dcfg.api_key,
                    base_url=dcfg.base_url,
                )
        elif self.provider == "claude":
            ccfg = cfg.claude
            self.model = ccfg.model or "claude-sonnet-4-20250514"
            import anthropic
            if ccfg.api_key:
                self._anthropic_client = anthropic.Anthropic(api_key=ccfg.api_key)
                self._anthropic_model = ccfg.model

    def _get_deepseek_messages(self, messages: list[dict], system: str | None) -> list[dict]:
        """DeepSeek 格式：system 放在 messages 第一帧，tool_calls 作为单独字段"""
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})

        for m in messages:
            # 跳过 system（已在上面处理）
            if m.get("role") == "system":
                continue

            msg: dict = {"role": m["role"]}

            # tool 消息格式
            if m["role"] == "tool":
                msg["content"] = m.get("content", "")
                msg["tool_call_id"] = m.get("tool_call_id", "")
                # 可选：工具名
                if "name" in m:
                    msg["name"] = m["name"]
            # assistant 消息可能有 tool_calls
            elif m["role"] == "assistant" and m.get("tool_calls"):
                msg["content"] = m.get("content") or None
                msg["tool_calls"] = m["tool_calls"]
            else:
                msg["content"] = m.get("content", "")

            msgs.append(msg)
        return msgs

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        stream: bool = True,
    ) -> Iterator[str] | str:
        if self.provider == "deepseek":
            return self._chat_deepseek(messages, tools, system, stream)
        elif self.provider == "claude":
            return self._chat_claude(messages, tools, system, stream)
        raise ValueError(f"Unsupported provider: {self.provider}")

    def _chat_deepseek(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        stream: bool = True,
    ) -> Iterator[str] | str:
        msgs = self._get_deepseek_messages(messages, system)
        kwargs = dict(
            model=self.model,
            messages=msgs,
            stream=stream,
        )
        if tools:
            kwargs["tools"] = tools

        response = self._client.chat.completions.create(**kwargs)

        if stream:
            return self._stream_deepseek(response)
        return response.choices[0].message.content or ""

    def _stream_deepseek(self, response) -> Iterator[str]:
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            # 保存 tool_use 信息
            if chunk.choices and chunk.choices[0].delta.tool_calls:
                self._accumulate_tool_call(chunk)

    def _accumulate_tool_call(self, chunk):
        """累积 tool calls 片段（DeepSeek 流式返回 tool calls 是增量的）"""
        tc = chunk.choices[0].delta.tool_calls
        if not tc:
            return
        for t in tc:
            idx = t.index
            if idx not in self._pending_tool_calls:
                self._pending_tool_calls[idx] = {
                    "id": t.id or "",
                    "function": {"name": "", "arguments": ""},
                }
            if t.id:
                self._pending_tool_calls[idx]["id"] = t.id
            if t.function:
                if t.function.name:
                    self._pending_tool_calls[idx]["function"]["name"] = t.function.name
                if t.function.arguments:
                    self._pending_tool_calls[idx]["function"]["arguments"] += t.function.arguments

    def get_tool_call_result(self, response_chunks) -> dict | None:
        """从流式响应中提取 tool_use"""
        if not self._pending_tool_calls:
            return None
        calls = list(self._pending_tool_calls.values())
        self._pending_tool_calls.clear()

        import json
        result = []
        for c in calls:
            result.append({
                "id": c["id"],
                "name": c["function"]["name"],
                "input": json.loads(c["function"]["arguments"]),
            })
        return {"choices": result}

    def _convert_tools_anthropic(self, tools: list[dict]) -> list[dict]:
        """将 OpenAI 格式的 tools 转为 Anthropic 格式"""
        converted = []
        for t in tools:
            func = t.get("function", t)
            converted.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
            })
        return converted

    def _chat_claude(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        stream: bool = True,
    ) -> Iterator[str] | str:
        if not hasattr(self, '_anthropic_client'):
            raise RuntimeError("Claude API key not configured")

        # 将 OpenAI 格式的 messages 转为 Anthropic 格式
        anthropic_messages = []
        pending_tool_results = []  # 收集 tool_result，合并到一条 user 消息

        for m in messages:
            if m["role"] == "system":
                continue
            elif m["role"] == "tool":
                pending_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id", ""),
                    "content": m.get("content", ""),
                })
            elif m["role"] == "assistant":
                content_blocks = []
                # 文本部分
                text = m.get("content")
                if text:
                    content_blocks.append({"type": "text", "text": text})
                # tool_use 部分
                if m.get("tool_calls"):
                    import json
                    for tc in m["tool_calls"]:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"]),
                        })
                anthropic_messages.append({"role": "assistant", "content": content_blocks})
                # 如果有待处理的 tool_result，合并到一条 user 消息
                if pending_tool_results:
                    anthropic_messages.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
            elif m["role"] == "user":
                # 如果有待处理的 tool_result，合并到 user 消息末尾
                if pending_tool_results:
                    anthropic_messages.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
                content = m.get("content", "")
                anthropic_messages.append({"role": "user", "content": [{"type": "text", "text": content}]})

        # 兜底：未附加的 tool_result
        if pending_tool_results:
            anthropic_messages.append({"role": "user", "content": pending_tool_results})

        kwargs = dict(
            model=self._anthropic_model,
            messages=anthropic_messages,
            max_tokens=4096,
            stream=stream,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools_anthropic(tools)

        response = self._anthropic_client.messages.create(**kwargs)

        if stream:
            return self._stream_claude(response)
        return response.content[0].text if response.content else ""

    def _stream_claude(self, response) -> Iterator[str]:
        blocks: dict[int, dict] = {}  # index → {id, name, arguments}

        for event in response:
            # 追踪 content block 的创建
            if event.type == "content_block_start":
                block = event.content_block
                if block.type == "tool_use":
                    blocks[event.index] = {
                        "id": block.id,
                        "name": block.name,
                        "arguments": "",
                    }

            # 累积 delta
            elif event.type == "content_block_delta":
                delta = event.delta
                if delta.type == "text_delta" and delta.text:
                    yield delta.text
                elif delta.type == "input_json_delta":
                    if event.index in blocks and delta.partial_json:
                        blocks[event.index]["arguments"] += delta.partial_json

        # 流结束后存入 _pending_tool_calls（与 DeepSeek 兼容的格式）
        for idx, block in blocks.items():
            self._pending_tool_calls[idx] = {
                "id": block["id"],
                "function": {
                    "name": block["name"],
                    "arguments": block["arguments"],
                },
            }

    def is_available(self) -> bool:
        try:
            if self.provider == "deepseek":
                return bool(get_config().llm.api.deepseek.api_key)
            return bool(get_config().llm.api.claude.api_key)
        except Exception:
            return False


# 快捷导入名
__all__ = ["APIBackend"]
