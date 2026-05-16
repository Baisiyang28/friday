"""Tool 基类定义"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """工具基类 — 所有工具继承此接口"""

    # 工具名称（供 LLM 调用时使用）
    name: str = ""
    # 工具描述
    description: str = ""

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具并返回结果

        Returns:
            工具执行结果的文本描述
        """
        ...

    def to_openai_tool(self) -> dict:
        """返回 OpenAI 格式的 tool 定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters(),
            },
        }

    @abstractmethod
    def parameters(self) -> dict:
        """返回 JSON Schema 格式的参数定义"""
        ...
