#!/usr/bin/env python3
"""Yokino Bot 服务入口 — 启动飞书 Bot"""

import io
import sys
from pathlib import Path

# 修复 Windows 控制台中文编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from core.engine import Agent
from interfaces.feishu import FeishuBot

# 注册工具
from core.tools.file_ops import ReadFileTool, WriteFileTool, SearchFilesTool
from core.tools.web_search import WebSearchTool
from core.tools.reminder import SetReminderTool, ListRemindersTool
from core.tools.note import CreateNoteTool, ReadNotesTool
from core.tools.weather import WeatherTool
from core.tools.knowledge_base import SearchKnowledgeTool, AddKnowledgeTool, ListKnowledgeTool
from core.tools.script_runner import RunPythonTool, RunShellTool
from core.tools.workflow import WorkflowTool, ListWorkflowsTool
from core.tools.user_memory import RememberUserTool, ForgetUserTool, ListUserFactsTool


def main():
    cfg = load_config("config.yaml")

    feishu = cfg.feishu
    if not feishu.app_id or not feishu.app_secret:
        print("⚠️ 未配置飞书 app_id / app_secret。请在 config.yaml 中填写。")
        return

    # 初始化 Agent
    agent = Agent()
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    agent.register_tool(SearchFilesTool())
    agent.register_tool(WebSearchTool())
    agent.register_tool(SetReminderTool())
    agent.register_tool(ListRemindersTool())
    agent.register_tool(CreateNoteTool())
    agent.register_tool(ReadNotesTool())
    agent.register_tool(WeatherTool())
    agent.register_tool(SearchKnowledgeTool())
    agent.register_tool(AddKnowledgeTool())
    agent.register_tool(ListKnowledgeTool())
    agent.register_tool(RunPythonTool())
    agent.register_tool(RunShellTool())
    agent.register_tool(WorkflowTool())
    agent.register_tool(ListWorkflowsTool())
    agent.register_tool(RememberUserTool())
    agent.register_tool(ForgetUserTool())
    agent.register_tool(ListUserFactsTool())

    # 初始化飞书 Bot
    bot = FeishuBot(app_id=feishu.app_id, app_secret=feishu.app_secret)

    def handle_message(chat_id: str, message: str) -> str:
        full_reply = ""
        for chunk in agent.chat(message):
            full_reply += chunk
        return full_reply.strip()

    bot.on_message(handle_message)
    bot.start()

    # 初始化调度器（主动推送）
    from scheduler.scheduler import YokinoScheduler

    def push_notification(chat_id: str, text: str):
        if chat_id:
            bot.send_message(chat_id, text)
        else:
            bot.broadcast(text)

    sched = YokinoScheduler(send_callback=push_notification)
    # 为已知聊天设置每日简报（启动后动态添加）
    import time
    time.sleep(3)  # 等 Bot 建立连接
    for chat_id in bot.known_chats:
        sched.schedule_daily_briefing(chat_id)
    sched.start()

    print("🤖 Yokino Bot 已启动，等待飞书消息...")
    print("  • 消息回复: ✅")
    print("  • 提醒检查: 每 30 秒")
    print("  • 每日简报: 每天 8:00")
    print("按 Ctrl+C 退出")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sched.stop()
        bot.stop()
        print("\n👋 Bot 已停止")


if __name__ == "__main__":
    main()
