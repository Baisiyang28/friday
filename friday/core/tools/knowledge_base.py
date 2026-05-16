"""知识库检索工具"""

from core.tools.base import Tool
from memory.knowledge import KnowledgeBase


class SearchKnowledgeTool(Tool):
    name = "search_knowledge"
    description = "在个人知识库中搜索相关文档，返回匹配结果和摘要"

    def execute(self, query: str, limit: int = 5) -> str:
        kb = KnowledgeBase()
        results = kb.search(query, limit=limit)

        if not results:
            return f"知识库中未找到与 '{query}' 相关的文档。使用 add_knowledge 添加新文档。"

        lines = [f"搜索 '{query}' 找到 {len(results)} 个结果:"]
        for r in results:
            lines.append(f"\n### {r['title']} ({r['path']})")
            lines.append(f"> {r['preview']}")
        return "\n".join(lines)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "返回结果数量，默认 5"},
            },
            "required": ["query"],
        }


class AddKnowledgeTool(Tool):
    name = "add_knowledge"
    description = "向知识库添加一篇文档（Markdown 格式）"

    def execute(self, title: str, content: str, category: str = "notes") -> str:
        kb = KnowledgeBase()
        filepath = kb.add(title, content, category)
        return f"文档已添加到知识库: {filepath}"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "文档标题"},
                "content": {"type": "string", "description": "文档内容（Markdown 格式）"},
                "category": {
                    "type": "string",
                    "description": "分类: notes（笔记）, bookmarks（书签）, reference（参考）",
                    "enum": ["notes", "bookmarks", "reference"],
                },
            },
            "required": ["title", "content"],
        }


class ListKnowledgeTool(Tool):
    name = "list_knowledge"
    description = "列出知识库中的所有文档"

    def execute(self, category: str = "") -> str:
        kb = KnowledgeBase()
        cat = category if category else None
        items = kb.list_all(category=cat)

        if not items:
            return f"知识库中还没有{'『' + category + '』分类的' if category else ''}文档。使用 add_knowledge 添加。"

        lines = [f"知识库共 {kb.count()} 篇文档:"]
        for item in items:
            lines.append(f"  • [{item['path']}] {item['title']}")
        return "\n".join(lines)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "按分类过滤（可选）"},
            },
            "required": [],
        }
