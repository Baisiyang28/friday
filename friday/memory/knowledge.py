"""知识库管理 — 本地 Markdown 文件索引与检索"""

import re
from pathlib import Path

from config import get_config


class KnowledgeBase:
    """本地知识库，基于 Markdown 文件的全文检索"""

    def __init__(self, base_dir: str | None = None):
        if base_dir is None:
            base_dir = "knowledge"
        self.base = Path(base_dir).resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        for sub in ("notes", "bookmarks", "reference"):
            (self.base / sub).mkdir(parents=True, exist_ok=True)

    def add(self, title: str, content: str, category: str = "notes") -> Path:
        """添加一篇知识库文档"""
        safe_name = self._safe_filename(title) + ".md"
        filepath = self.base / category / safe_name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full = f"# {title}\n\n> 创建于 {ts} | 分类: {category}\n\n{content}\n"
        filepath.write_text(full, encoding="utf-8")
        return filepath

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """全文搜索知识库，返回匹配的文档列表"""
        results = []
        query_lower = query.lower()
        terms = query_lower.split()

        for md_file in self.base.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # 计算匹配分数：标题匹配权重最高，内容匹配次之
            score = 0
            content_lower = content.lower()

            # 文件名词匹配
            if any(t in md_file.stem.lower() for t in terms):
                score += 3

            # 标题匹配（h1 行）
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem
            if any(t in title.lower() for t in terms):
                score += 5

            # 内容匹配
            for term in terms:
                score += content_lower.count(term)

            if score > 0:
                # 取内容前 300 字符作为摘要
                preview = content[:300].replace("\n", " ")
                if len(content) > 300:
                    preview += "..."
                results.append({
                    "path": str(md_file.relative_to(self.base)),
                    "title": title,
                    "score": score,
                    "preview": preview,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def list_all(self, category: str | None = None) -> list[dict]:
        """列出所有文档"""
        search_dir = self.base / category if category else self.base
        if not search_dir.exists():
            return []

        results = []
        for md_file in sorted(search_dir.rglob("*.md"), reverse=True):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem
            results.append({
                "path": str(md_file.relative_to(self.base)),
                "title": title,
            })
        return results

    def count(self) -> int:
        return len(list(self.base.rglob("*.md")))

    @staticmethod
    def _safe_filename(name: str) -> str:
        for c in '<>:"/\\|?*':
            name = name.replace(c, "_")
        return name.strip()[:100]
