"""Ollama 本地 LLM 后端"""

from typing import Any, Iterator

import requests

from config import get_config
from core.llm.base import LLMBackend


class LocalBackend(LLMBackend):
    """基于 Ollama 的本地模型后端"""

    name = "local"

    def __init__(self):
        cfg = get_config().llm.local
        self.base_url = cfg.base_url.rstrip("/")
        self.model = cfg.model

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
        stream: bool = True,
    ) -> Iterator[str] | str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if system:
            payload["system"] = system

        # Ollama 原生不支持 OpenAI 格式的 tools，简化处理
        if tools:
            payload["tools"] = tools

        url = f"{self.base_url}/api/chat"
        resp = requests.post(url, json=payload, stream=stream, timeout=60)
        resp.raise_for_status()

        if stream:
            return self._stream_response(resp)

        data = resp.json()
        return data.get("message", {}).get("content", "")

    def _stream_response(self, resp: requests.Response) -> Iterator[str]:
        for line in resp.iter_lines():
            if not line:
                continue
            import json
            try:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
                if data.get("done"):
                    break
            except json.JSONDecodeError:
                continue

    def is_available(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return False
            models = resp.json().get("models", [])
            return any(m["name"].startswith(self.model.split(":")[0]) for m in models)
        except Exception:
            return False


__all__ = ["LocalBackend"]
