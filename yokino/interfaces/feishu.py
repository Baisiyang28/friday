"""飞书 Bot 接口 — 通过 Feishu WebSocket 接收和回复消息"""

import json
import logging
import threading
from typing import Callable

logger = logging.getLogger("yokino.feishu")


class FeishuBot:
    """飞书 Bot，使用 WebSocket 长连接接收消息事件"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_token: str | None = None
        self._ws_client = None
        self._message_handler: Callable | None = None
        self._running = False
        self._chat_ids: set[str] = set()

    def on_message(self, handler: Callable[[str, str], str]):
        """注册消息处理回调

        handler(chat_id: str, message: str) -> str: 返回回复内容
        """
        self._message_handler = handler

    def start(self):
        """启动 Bot（在新线程中运行 WebSocket 连接）"""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        logger.info("飞书 Bot 已启动")

    def _run(self):
        """主运行循环"""
        try:
            from lark_oapi.ws import Client
        except ImportError:
            logger.error("请安装 lark-oapi: pip install lark-oapi")
            return

        self._running = True

        def on_event(ws_client, event):
            self._handle_event(event)

        # WebSocket 客户端会自动重连
        ws_client = Client(
            app_id=self.app_id,
            app_secret=self.app_secret,
            event_handler=on_event,
        )
        self._ws_client = ws_client
        ws_client.start()

    def _handle_event(self, event):
        """处理收到的飞书事件"""
        try:
            header = event.header
            if header.event_type != "im.message.receive_v1":
                return

            event_data = event.event
            msg_type = event_data.message.message_type
            chat_id = event_data.message.chat_id

            # 只处理文本消息
            if msg_type != "text":
                return

            # 提取消息内容
            content_str = event_data.message.content
            content = json.loads(content_str)
            text = content.get("text", "")

            if not text.strip():
                return

            logger.info(f"收到消息: chat_id={chat_id}, text={text[:50]}...")
            self._chat_ids.add(chat_id)

            if self._message_handler:
                reply = self._message_handler(chat_id, text)
                self.send_message(chat_id, reply)

        except Exception:
            logger.exception("处理飞书事件失败")

    def send_message(self, chat_id: str, content: str):
        """发送消息到飞书聊天"""
        try:
            from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
            from lark_oapi.client import ClientBuilder
            from lark_oapi import FEISHU_DOMAIN

            client = (ClientBuilder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .domain(FEISHU_DOMAIN)
                .build())

            body = (CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": content}))
                .build())

            request = (CreateMessageRequest.builder()
                .receive_id_type("chat_id")
                .request_body(body)
                .build())

            client.im.v1.message.create(request)
        except Exception:
            logger.exception("发送飞书消息失败")

    def broadcast(self, content: str):
        """向所有已知聊天推送消息"""
        for chat_id in list(self._chat_ids):
            self.send_message(chat_id, content)

    @property
    def known_chats(self) -> list[str]:
        return list(self._chat_ids)

    def stop(self):
        self._running = False
