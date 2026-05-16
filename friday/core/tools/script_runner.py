"""脚本执行工具 — 安全沙箱执行 Python/Shell 脚本"""

import subprocess
import tempfile
from pathlib import Path

from core.tools.base import Tool


class RunPythonTool(Tool):
    name = "run_python"
    description = "在临时沙箱中执行 Python 代码并返回输出。谨慎使用，不要执行不可信代码。"

    def execute(self, code: str, timeout: int = 30) -> str:
        # 写入临时文件
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        )
        tmp.write(code)
        tmp.close()

        try:
            result = subprocess.run(
                ["python", tmp.name],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout = result.stdout.strip() or "(无输出)"
            stderr = result.stderr.strip()
            out = stdout
            if stderr:
                out += f"\n\n[stderr]\n{stderr}"
            return out[:5000]  # 截断过长输出
        except subprocess.TimeoutExpired:
            return f"执行超时（>{timeout}秒），已终止"
        except FileNotFoundError:
            return "未找到 Python 解释器"
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码"},
                "timeout": {"type": "integer", "description": "超时秒数，默认 30"},
            },
            "required": ["code"],
        }


class RunShellTool(Tool):
    name = "run_shell"
    description = "执行 Shell 命令并返回输出。命令会被审查，危险操作需要确认。"

    # 危险模式列表（需要用户确认）
    DANGEROUS_PATTERNS = [
        "rm -rf", "rm -r", "del /f", "format",
        "> /dev/sda", "dd if=", "mkfs.",
        "DROP", "DELETE FROM", "TRUNCATE",
        "shutdown", "reboot", "halt",
        "curl.*|.*sh", "wget.*|.*sh",
        "chmod 777", "sudo ", "su ",
    ]

    def execute(self, command: str, confirm: bool = False, timeout: int = 60) -> str:
        cmd_lower = command.lower()

        # 检查危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                if not confirm:
                    return (
                        f"⚠️ 此命令可能具有破坏性:\n  `{command}`\n\n"
                        "如果确认要执行，请设置 confirm=True 再次调用。"
                    )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout = result.stdout.strip() or "(无输出)"
            stderr = result.stderr.strip()
            out = f"[exit code: {result.returncode}]\n{stdout}"
            if stderr:
                out += f"\n\n[stderr]\n{stderr}"
            return out[:5000]
        except subprocess.TimeoutExpired:
            return f"命令执行超时（>{timeout}秒），已终止"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的 Shell 命令"},
                "confirm": {"type": "boolean", "description": "确认执行危险命令，默认 false"},
                "timeout": {"type": "integer", "description": "超时秒数，默认 60"},
            },
            "required": ["command"],
        }
