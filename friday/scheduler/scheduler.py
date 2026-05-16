"""APScheduler 定时任务管理器 — 每日简报、提醒检查、主动推送"""

import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("friday.scheduler")

REMINDERS_FILE = Path("data/reminders.json")


class FridayScheduler:
    """Friday 任务调度器"""

    def __init__(self, send_callback: Callable | None = None):
        """
        Args:
            send_callback: 消息推送回调 (chat_id, text) -> None
        """
        self._scheduler = BackgroundScheduler()
        self._send = send_callback or (lambda chat_id, text: None)
        self._jobs = {}

    def start(self):
        """启动调度器"""
        # 提醒检查：每 30 秒检查一次到期提醒
        self._scheduler.add_job(
            self._check_reminders,
            IntervalTrigger(seconds=30),
            id="reminder_check",
            name="提醒检查",
        )
        self._scheduler.start()
        logger.info("调度器已启动")

    def stop(self):
        self._scheduler.shutdown(wait=False)
        logger.info("调度器已停止")

    def schedule_daily_briefing(self, chat_id: str, hour: int = 8, minute: int = 0):
        """设置每日简报定时任务

        Args:
            chat_id: 目标飞书 chat_id
            hour: 推送时间（小时，默认 8:00）
            minute: 推送时间（分钟）
        """
        job_id = f"briefing_{chat_id}"
        self._scheduler.add_job(
            lambda: self._send_daily_briefing(chat_id),
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"每日简报 ({chat_id})",
            replace_existing=True,
        )
        logger.info(f"每日简报已设置: {chat_id} @ {hour:02d}:{minute:02d}")

    def _send_daily_briefing(self, chat_id: str):
        """生成并发送每日简报"""
        today = datetime.now().strftime("%Y-%m-%d")
        briefing = self._build_briefing()
        self._send(chat_id, briefing)
        logger.info(f"每日简报已推送: {chat_id}")

    def _build_briefing(self) -> str:
        """构建每日简报内容"""
        today = datetime.now().strftime("%Y年%m月%d日 %A")
        weekdays = {"Monday": "一", "Tuesday": "二", "Wednesday": "三", "Thursday": "四",
                    "Friday": "五", "Saturday": "六", "Sunday": "日"}
        for en, cn in weekdays.items():
            today = today.replace(en, f"周{cn}")

        # 获取待处理的提醒
        reminders = self._get_pending_reminders()
        today_reminders = [r for r in reminders if r["trigger_time"][:10] == datetime.now().strftime("%Y-%m-%d")]

        lines = [
            f"☀️ **早安！{today}**",
            "",
            "📋 **今日提醒**:",
        ]
        if today_reminders:
            for r in today_reminders:
                t = datetime.fromisoformat(r["trigger_time"])
                lines.append(f"  • {t.strftime('%H:%M')} — {r['message']}")
        else:
            lines.append("  今天没有待处理的提醒")

        return "\n".join(lines)

    def _check_reminders(self):
        """检查到期提醒并推送"""
        reminders = self._get_pending_reminders()
        now = datetime.now()
        fired = []

        for i, r in enumerate(reminders):
            trigger_time = datetime.fromisoformat(r["trigger_time"])
            if trigger_time <= now:
                # 推送提醒（推送到默认 chat_id，如果配置了的话）
                self._send("", f"⏰ **提醒**: {r['message']}")
                fired.append(i)
                logger.info(f"提醒已触发: {r['message']}")

        if fired:
            self._mark_fired(fired)

    @staticmethod
    def _get_pending_reminders() -> list[dict]:
        if not REMINDERS_FILE.exists():
            return []
        try:
            data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
            return [r for r in data if not r.get("fired")]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    @staticmethod
    def _mark_fired(indices: list[int]):
        """标记提醒为已触发"""
        if not REMINDERS_FILE.exists():
            return
        try:
            data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
            for i in indices:
                if i < len(data):
                    data[i]["fired"] = True
            REMINDERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("标记提醒失败")
