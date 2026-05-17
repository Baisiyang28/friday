"""提醒工具 — 设置和管理提醒"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from core.tools.base import Tool

REMINDERS_FILE = Path("data/reminders.json")


class SetReminderTool(Tool):
    name = "set_reminder"
    description = "设置一个提醒，在指定时间通知用户"

    def execute(self, message: str, time: str) -> str:
        """
        Args:
            message: 提醒内容
            time: ISO 时间字符串，如 2026-05-16T15:00:00
                  也支持相对时间: "30m", "1h", "2h30m"
        """
        # 解析时间
        try:
            trigger_time = self._parse_time(time)
        except ValueError as e:
            return f"时间解析失败: {e}"

        if trigger_time <= datetime.now():
            return "提醒时间不能早于当前时间"

        reminder = {
            "message": message,
            "trigger_time": trigger_time.isoformat(),
            "created_at": datetime.now().isoformat(),
            "fired": False,
        }

        self._save(reminder)
        return f"✅ 提醒已设置: 「{message}」— 将于 {trigger_time.strftime('%Y-%m-%d %H:%M:%S')} 触发"

    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串，支持 ISO 格式和相对时间"""
        # 先尝试 ISO 格式
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            pass

        # 尝试相对时间: 30m, 1h, 2h30m, 1d
        import re
        match = re.fullmatch(r"(\d+d)?\s*(\d+h)?\s*(\d+m)?", time_str.strip())
        if not match or not time_str.strip():
            raise ValueError(f"无法解析时间: {time_str}。请使用 ISO 格式 (如 2026-05-16T15:00) 或相对时间 (如 30m, 1h, 2h30m)")

        delta = timedelta()
        if match.group(1):
            delta += timedelta(days=int(match.group(1).rstrip("d")))
        if match.group(2):
            delta += timedelta(hours=int(match.group(2).rstrip("h")))
        if match.group(3):
            delta += timedelta(minutes=int(match.group(3).rstrip("m")))

        if delta.total_seconds() == 0:
            raise ValueError(f"无法解析时间: {time_str}")

        return datetime.now() + delta

    def _save(self, reminder: dict):
        REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        reminders = self._load_all()
        reminders.append(reminder)
        REMINDERS_FILE.write_text(json.dumps(reminders, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _load_all() -> list:
        if not REMINDERS_FILE.exists():
            return []
        try:
            return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "提醒内容"},
                "time": {"type": "string", "description": "提醒时间，ISO 格式 (2026-05-16T15:00) 或相对时间 (30m, 1h, 2h30m, 1d)"},
            },
            "required": ["message", "time"],
        }


class ListRemindersTool(Tool):
    name = "list_reminders"
    description = "列出所有未触发的提醒"

    def execute(self) -> str:
        reminders = SetReminderTool._load_all()
        pending = [r for r in reminders if not r.get("fired")]
        if not pending:
            return "当前没有待触发的提醒"

        lines = ["待触发提醒:"]
        for i, r in enumerate(pending, 1):
            t = datetime.fromisoformat(r["trigger_time"])
            lines.append(f"  {i}. 「{r['message']}」— {t.strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)

    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}
