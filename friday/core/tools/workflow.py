"""工作流工具 — 多步骤自动化任务"""

import json
from pathlib import Path

from core.tools.base import Tool

WORKFLOWS_DIR = Path("workflows")


class WorkflowTool(Tool):
    name = "run_workflow"
    description = "执行一个预设的多步骤工作流"

    def execute(self, name: str, params: dict | None = None) -> str:
        params = params or {}

        # 加载工作流定义
        wf_file = WORKFLOWS_DIR / f"{name}.json"
        if not wf_file.exists():
            available = self._list_available()
            msg = f"工作流 '{name}' 不存在。\n可用的工作流: {', '.join(available) if available else '(无)'}"
            return msg

        try:
            definition = json.loads(wf_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return f"工作流文件损坏: {wf_file}"

        # 执行步骤
        steps = definition.get("steps", [])
        if not steps:
            return f"工作流 '{name}' 没有定义步骤"

        results = []
        for i, step in enumerate(steps, 1):
            step_type = step.get("type", "unknown")
            desc = step.get("description", f"步骤 {i}")

            if step_type == "print":
                msg = step.get("message", "").format(**params)
                results.append(f"[{i}] {msg}")

            elif step_type == "file_write":
                path = Path(step.get("path", "")).expanduser()
                content = step.get("content", "").format(**params)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                results.append(f"[{i}] 已写入: {path}")

            elif step_type == "file_read":
                path = Path(step.get("path", "")).expanduser()
                if path.exists():
                    text = path.read_text(encoding="utf-8")
                    results.append(f"[{i}] {path.name}:\n{text[:500]}")
                else:
                    results.append(f"[{i}] 文件不存在: {path}")

            else:
                results.append(f"[{i}] 未知步骤类型: {step_type}")

        return f"工作流 '{name}' 执行完成 ({len(steps)} 步):\n" + "\n".join(results)

    @staticmethod
    def _list_available() -> list[str]:
        if not WORKFLOWS_DIR.exists():
            return []
        return [f.stem for f in sorted(WORKFLOWS_DIR.glob("*.json"))]

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "工作流名称（对应 workflows/ 目录下的文件名）"},
                "params": {"type": "object", "description": "传入工作流的参数（可选）"},
            },
            "required": ["name"],
        }


class ListWorkflowsTool(Tool):
    name = "list_workflows"
    description = "列出所有可用的工作流"

    def execute(self) -> str:
        available = WorkflowTool._list_available()
        if not available:
            return "还没有自定义工作流。在 workflows/ 目录下创建 JSON 文件来定义工作流。"

        lines = ["可用工作流:"]
        for name in available:
            wf_file = WORKFLOWS_DIR / f"{name}.json"
            try:
                data = json.loads(wf_file.read_text(encoding="utf-8"))
                desc = data.get("description", "(无描述)")
                steps = len(data.get("steps", []))
                lines.append(f"  • {name} — {desc} ({steps} 步)")
            except Exception:
                lines.append(f"  • {name}")
        return "\n".join(lines)

    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}
