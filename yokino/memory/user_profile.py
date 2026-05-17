"""用户长期记忆 — 跨会话保留的用户事实"""

import json
from datetime import datetime
from pathlib import Path

USER_PROFILE_FILE = Path("data/user_profile.json")


class UserProfile:
    """管理用户长期记忆，以 JSON 文件持久化"""

    def __init__(self, path: Path | None = None):
        self._path = path or USER_PROFILE_FILE
        self._data: dict = {"facts": [], "updated_at": ""}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                self._data = {"facts": [], "updated_at": ""}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data["updated_at"] = datetime.now().isoformat()
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_fact(self, fact: str) -> str:
        """添加一条用户事实"""
        self._data["facts"].append(fact)
        self._save()
        return f"已记住: {fact}"

    def remove_fact(self, index: int) -> str:
        """删除指定序号的事实（1-based）"""
        facts = self._data["facts"]
        if index < 1 or index > len(facts):
            return f"序号无效: {index}（共 {len(facts)} 条）"
        removed = facts.pop(index - 1)
        self._save()
        return f"已忘记: {removed}"

    def get_facts(self) -> list[str]:
        return self._data["facts"]

    def to_prompt(self) -> str:
        """拼接到 system prompt 的片段"""
        facts = self._data["facts"]
        if not facts:
            return ""
        lines = [
            "以下是你对用户的了解（长期记忆，跨会话保留）：",
        ]
        for i, fact in enumerate(facts, 1):
            lines.append(f"- {fact}")
        return "\n".join(lines)
