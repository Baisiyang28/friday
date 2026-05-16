"""文件操作工具 — 读、写、搜索文件"""

from pathlib import Path

from core.tools.base import Tool


class ReadFileTool(Tool):
    name = "read_file"
    description = "读取指定文件的内容"

    def execute(self, path: str) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"文件不存在: {p}"
        if p.is_dir():
            return f"目标路径是目录而非文件: {p}"
        try:
            content = p.read_text(encoding="utf-8")
            # 截断过长内容
            if len(content) > 5000:
                content = content[:5000] + "\n\n[... 内容过长已截断 ...]"
            return content
        except UnicodeDecodeError:
            return "无法以 UTF-8 编码读取此文件（可能是二进制文件）"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要读取的文件路径"}
            },
            "required": ["path"],
        }


class WriteFileTool(Tool):
    name = "write_file"
    description = "将内容写入文件（会覆盖已有内容）"

    def execute(self, path: str, content: str) -> str:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"已写入文件: {p} ({len(content)} 字符)"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要写入的文件路径"},
                "content": {"type": "string", "description": "要写入的文件内容"},
            },
            "required": ["path", "content"],
        }


class SearchFilesTool(Tool):
    name = "search_files"
    description = "在指定目录下搜索包含关键词的文件名和内容"

    def execute(self, keyword: str, directory: str = ".") -> str:
        base = Path(directory).expanduser().resolve()
        if not base.exists():
            return f"目录不存在: {base}"

        results = []
        for f in base.rglob("*"):
            if f.is_file() and not self._is_binary(f):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if keyword.lower() in f.name.lower() or keyword.lower() in content.lower():
                        results.append(str(f.relative_to(base)))
                except Exception:
                    continue
            if len(results) >= 20:
                break

        if not results:
            return f"未找到包含 '{keyword}' 的文件"
        return f"搜索到 {len(results)} 个文件:\n" + "\n".join(f"  • {r}" for r in results)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"},
                "directory": {"type": "string", "description": "搜索目录，默认为当前目录"},
            },
            "required": ["keyword"],
        }

    @staticmethod
    def _is_binary(path: Path) -> bool:
        """简单判断是否为二进制文件"""
        binary_exts = {".exe", ".dll", ".so", ".pyc", ".pyd", ".zip", ".tar", ".gz",
                       ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".pdf", ".db"}
        return path.suffix.lower() in binary_exts
