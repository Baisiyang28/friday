"""联网搜索工具"""

import json
from urllib.parse import quote

import requests

from core.tools.base import Tool


class WebSearchTool(Tool):
    name = "web_search"
    description = "联网搜索信息，返回摘要结果"

    def execute(self, query: str, num: int = 5) -> str:
        # 使用 DuckDuckGo 的 Instant Answer API（无需 API Key）
        try:
            results = self._search_duckduckgo(query, num)
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._search_bing(query, num)
            if results:
                return results
        except Exception:
            pass

        return f"搜索 '{query}' 失败：所有搜索引擎均不可用"

    def _search_duckduckgo(self, query: str, num: int) -> str | None:
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        parts = []
        if data.get("AbstractText"):
            parts.append(data["AbstractText"])
        if data.get("Answer"):
            parts.append(f"答案: {data['Answer']}")

        related = data.get("RelatedTopics", [])
        for topic in related[:num]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"• {topic['Text']}")
            elif isinstance(topic, str):
                parts.append(f"• {topic}")

        return "\n\n".join(parts) if parts else None

    def _search_bing(self, query: str, num: int) -> str | None:
        # 抓取 Bing 搜索结果页（备选，可能不稳定）
        url = f"https://www.bing.com/search?q={quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        # 简单提取 <title>
        import re
        titles = re.findall(r'<h2[^>]*>.*?<a[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        if not titles:
            return None
        return "搜索结果:\n" + "\n".join(f"• {t.strip()}" for t in titles[:num])

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "num": {"type": "integer", "description": "返回结果数量，默认 5"},
            },
            "required": ["query"],
        }
