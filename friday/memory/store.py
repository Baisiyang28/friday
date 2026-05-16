"""SQLite 会话记忆存储"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import get_config


class MessageStore:
    """基于 SQLite 的对话历史存储"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = get_config().memory.db_path

        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                meta TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_time
            ON conversations(session_id, created_at)
        """)
        self.conn.commit()

        # 确保旧表有 meta 列（兼容升级）
        try:
            self.conn.execute("ALTER TABLE conversations ADD COLUMN meta TEXT")
            self.conn.commit()
        except Exception:
            pass

    def add_message(self, session_id: str, role: str, content: str | None = None,
                     tool_calls: list[dict] | None = None, tool_call_id: str | None = None,
                     name: str | None = None):
        """添加一条消息到历史"""
        meta = {}
        if tool_calls:
            meta["tool_calls"] = tool_calls
        if tool_call_id:
            meta["tool_call_id"] = tool_call_id
        if name:
            meta["name"] = name

        meta_json = json.dumps(meta, ensure_ascii=False) if meta else None
        self.conn.execute(
            "INSERT INTO conversations (session_id, role, content, meta) VALUES (?, ?, ?, ?)",
            (session_id, role, content or "", meta_json),
        )
        self.conn.commit()
        self._trim_history(session_id)

    def _trim_history(self, session_id: str):
        """保留最近 N 轮对话"""
        max_turns = get_config().memory.max_turns
        # 计算需要删除的消息数（每轮至少 2 条: user + assistant）
        keep_count = max_turns * 2
        self.conn.execute("""
            DELETE FROM conversations
            WHERE session_id = ? AND id NOT IN (
                SELECT id FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
        """, (session_id, session_id, keep_count))
        self.conn.commit()

    def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """获取对话历史，每条消息包含 role、content 和可选的 tool_calls/tool_call_id"""
        cursor = self.conn.execute(
            "SELECT role, content, meta FROM conversations WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit),
        )
        result = []
        for row in cursor.fetchall():
            msg = {"role": row[0], "content": row[1]}
            if row[2]:
                try:
                    meta = json.loads(row[2])
                    for key in ("tool_calls", "tool_call_id", "name"):
                        if key in meta:
                            msg[key] = meta[key]
                except json.JSONDecodeError:
                    pass
            result.append(msg)
        return result

    def clear_session(self, session_id: str):
        """清除指定会话的历史"""
        self.conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
