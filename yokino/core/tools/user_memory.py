"""用户记忆工具 — 让 AI 记住和读取用户事实"""

from core.tools.base import Tool
from memory.user_profile import UserProfile


class RememberUserTool(Tool):
    name = "remember_user"
    description = "记住一条关于用户的信息或偏好，跨会话持久保留"

    def execute(self, fact: str) -> str:
        profile = UserProfile()
        return profile.add_fact(fact)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "要记住的用户信息，如「用户喜欢用 tab 缩进」「用户在学 Rust」"},
            },
            "required": ["fact"],
        }


class ForgetUserTool(Tool):
    name = "forget_user"
    description = "删除一条已记住的用户信息（按序号）"

    def execute(self, index: int) -> str:
        profile = UserProfile()
        return profile.remove_fact(index)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "要删除的信息序号，从 list_user_facts 的结果中获取"},
            },
            "required": ["index"],
        }


class ListUserFactsTool(Tool):
    name = "list_user_facts"
    description = "列出所有已记住的关于用户的信息"

    def execute(self) -> str:
        profile = UserProfile()
        facts = profile.get_facts()
        if not facts:
            return "还没有记住任何关于用户的信息。你可以对 Yokino 说「记住我喜欢...」来添加。"
        lines = ["关于你的信息:"]
        for i, fact in enumerate(facts, 1):
            lines.append(f"  {i}. {fact}")
        return "\n".join(lines)

    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}
