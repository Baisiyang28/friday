"""笔记工具 — 创建和检索笔记"""

from datetime import datetime
from pathlib import Path

from core.tools.base import Tool

NOTES_DIR = Path("knowledge/notes")


class CreateNoteTool(Tool):
    name = "create_note"
    description = "创建一篇新笔记（Markdown 格式）"

    def execute(self, title: str, content: str) -> str:
        NOTES_DIR.mkdir(parents=True, exist_ok=True)

        # 用标题生成安全文件名
        safe_name = self._safe_filename(title) + ".md"
        filepath = NOTES_DIR / safe_name

        # 添加元数据头
        full_content = f"# {title}\n\n> 创建于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}\n"

        filepath.write_text(full_content, encoding="utf-8")
        return f"笔记已创建: {filepath}"

    @staticmethod
    def _safe_filename(name: str) -> str:
        """去除不安全字符"""
        unsafe = '<>:"/\\|?*'
        for c in unsafe:
            name = name.replace(c, "_")
        return name.strip()[:100]

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "笔记标题"},
                "content": {"type": "string", "description": "笔记内容（Markdown 格式）"},
            },
            "required": ["title", "content"],
        }


class ReadNotesTool(Tool):
    name = "read_notes"
    description = "搜索并读取笔记，可按关键词过滤"

    def execute(self, keyword: str = "") -> str:
        if not NOTES_DIR.exists():
            NOTES_DIR.mkdir(parents=True, exist_ok=True)
            return "还没有任何笔记。使用 create_note 创建第一篇吧。"

        notes = list(NOTES_DIR.rglob("*.md"))
        if not notes:
            return "还没有任何笔记。"

        keyword_lower = keyword.lower() if keyword else ""

        results = []
        for fp in sorted(notes, reverse=True):
            content = fp.read_text(encoding="utf-8")
            if keyword_lower and keyword_lower not in content.lower():
                continue
            # 只取前 300 字符作为摘要
            preview = content[:300] + ("..." if len(content) > 300 else "")
            results.append(f"### {fp.stem}\n{preview}\n")

        if keyword and not results:
            return f"未找到包含 '{keyword}' 的笔记"

        return "\n---\n".join(results) if results else "还没有任何笔记。"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词（可选，留空则列出所有笔记）"},
            },
            "required": [],
        }
