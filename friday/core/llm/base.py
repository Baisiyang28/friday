"""LLM 后端抽象基类"""

from abc import ABC, abstractmethod
from typing import Any


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        stream: bool = True,
    ) -> Any:
        """发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            tools: 工具定义列表（tool use 格式）
            system: system prompt
            stream: 是否流式输出

        Returns:
            stream=True 时返回迭代器，逐块产出 str
            stream=False 时返回完整响应字符串
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查后端是否可用（API 连通性 / 本地模型是否加载）"""
        ...

    def get_tool_call_result(self, response_chunks) -> dict | None:
        """从流式响应中提取 tool_use 结果

        Returns:
            {"id": "...", "name": "...", "input": {...}} | None
        """
        return None
