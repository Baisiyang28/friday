#!/usr/bin/env python3
"""Yokino CLI — 个人 AI 助理终端入口"""

import io
import sys
from pathlib import Path

# 修复 Windows 控制台中文编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.panel import Panel

from config import load_config
from core.engine import Agent
from core.tools.file_ops import ReadFileTool, WriteFileTool, SearchFilesTool
from core.tools.web_search import WebSearchTool
from core.tools.reminder import SetReminderTool, ListRemindersTool
from core.tools.note import CreateNoteTool, ReadNotesTool
from core.tools.weather import WeatherTool
from core.tools.knowledge_base import SearchKnowledgeTool, AddKnowledgeTool, ListKnowledgeTool
from core.tools.script_runner import RunPythonTool, RunShellTool
from core.tools.workflow import WorkflowTool, ListWorkflowsTool
from core.tools.user_memory import RememberUserTool, ForgetUserTool, ListUserFactsTool

console = Console()


def check_connectivity(cfg) -> bool:
    """启动自检：ping API 和 Ollama，返回是否有任一端可用"""
    import requests

    console.print()
    console.print("[bold]🔍 启动自检...[/bold]")

    all_ok = True

    # 1. 检查 API 后端
    provider = cfg.llm.api.provider
    if provider == "deepseek":
        key = cfg.llm.api.deepseek.api_key
        base = cfg.llm.api.deepseek.base_url
        model = cfg.llm.api.deepseek.model
        try:
            resp = requests.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                console.print(f"  ✅ DeepSeek API ([green]{base}[/green]) — 模型: {model}")
            else:
                console.print(f"  ⚠️  DeepSeek API 返回 HTTP {resp.status_code}: {resp.text[:100]}")
                all_ok = False
        except requests.ConnectionError:
            console.print(f"  ❌ DeepSeek API ([red]无法连接[/red]) — 请检查网络/代理")
            all_ok = False
        except requests.Timeout:
            console.print(f"  ❌ DeepSeek API ([red]连接超时[/red])")
            all_ok = False
        except Exception as e:
            console.print(f"  ❌ DeepSeek API ([red]{e}[/red])")
            all_ok = False

    elif provider == "claude":
        key = cfg.llm.api.claude.api_key
        model = cfg.llm.api.claude.model
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            # 发一个极短的请求验证连通性
            resp = client.messages.create(
                model=model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            console.print(f"  ✅ Claude API ([green]Anthropic[/green]) — 模型: {model}")
        except Exception as e:
            console.print(f"  ❌ Claude API ([red]{e}[/red])")
            all_ok = False

    # 2. 检查 Ollama 本地后端
    local_base = cfg.llm.local.base_url
    local_model = cfg.llm.local.model
    try:
        resp = requests.get(f"{local_base}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            if any(local_model.split(":")[0] in m for m in models):
                console.print(f"  ✅ Ollama ([green]{local_base}[/green]) — 模型: {local_model} 已就绪")
            else:
                console.print(f"  ⚠️  Ollama 已运行，但未找到模型 [yellow]{local_model}[/yellow]。可用模型: {models or '(无)'}")
                console.print(f"     运行 [dim]ollama pull {local_model}[/dim] 拉取模型")
                all_ok = False
        else:
            console.print(f"  ⚠️  Ollama 返回 HTTP {resp.status_code}")
            all_ok = False
    except requests.ConnectionError:
        console.print(f"  ⚠️  Ollama ([yellow]未运行[/yellow]) — API 不可用时将无法降级")
    except Exception as e:
        console.print(f"  ⚠️  Ollama ([yellow]{e}[/yellow])")

    console.print()
    return all_ok


def register_tools(agent: Agent):
    """注册所有内置工具"""
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    agent.register_tool(SearchFilesTool())
    agent.register_tool(WebSearchTool())
    agent.register_tool(SetReminderTool())
    agent.register_tool(ListRemindersTool())
    agent.register_tool(CreateNoteTool())
    agent.register_tool(ReadNotesTool())
    agent.register_tool(WeatherTool())
    agent.register_tool(SearchKnowledgeTool())
    agent.register_tool(AddKnowledgeTool())
    agent.register_tool(ListKnowledgeTool())
    agent.register_tool(RunPythonTool())
    agent.register_tool(RunShellTool())
    agent.register_tool(WorkflowTool())
    agent.register_tool(ListWorkflowsTool())
    agent.register_tool(RememberUserTool())
    agent.register_tool(ForgetUserTool())
    agent.register_tool(ListUserFactsTool())


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════╗
║            Yokino — 你的 AI 助理         ║
║        你的个人 AI 助理，随时在线        ║
╚══════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print("输入你的问题开始对话，输入以下命令进行操作：", style="dim")
    console.print("  /clear  — 清空对话历史")
    console.print("  /tools  — 查看可用工具")
    console.print("  /status — 查看当前后端状态")
    console.print("  /exit   — 退出", style="dim")
    console.print()


@click.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="配置文件路径 (默认: config.yaml)",
)
def main(config: str):
    """Yokino - 个人 AI 生活学习工作助理"""
    # 加载配置
    cfg = load_config(config)
    console.print(f"[dim]配置文件: {config}[/dim]")

    if not cfg.llm.api.deepseek.api_key and not cfg.llm.api.claude.api_key:
        console.print(
            "⚠️  [yellow]未配置 API Key。请在 config.yaml 中设置 DeepSeek 或 Claude 的 API Key。[/yellow]\n"
            "   同时请确保 Ollama 已安装并已拉取 qwen2.5:7b 模型，否则本地备用后端也无法使用。",
        )
        return

    # 启动自检：ping API 和 Ollama
    check_connectivity(cfg)

    # 初始化 Agent 并注册工具
    agent = Agent()
    register_tools(agent)

    print_banner()

    # 主循环
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]你[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n👋 再见！")
            break

        # 处理命令
        if user_input.startswith("/"):
            handle_command(user_input, agent)
            continue

        if not user_input.strip():
            continue

        # 流式输出回复
        console.print()
        with console.status("[bold green]Yokino 思考中...[/bold green]", spinner="dots"):
            full_response = ""
            for chunk in agent.chat(user_input):
                full_response += chunk

        # 用 Markdown 渲染回复
        if full_response:
            md = Markdown(full_response.strip())
            console.print(Panel(md, border_style="green", title="[bold green]Yokino[/bold green]"))
        console.print()


def handle_command(cmd: str, agent: Agent):
    """处理 / 命令"""
    cmd = cmd.strip().lower()

    if cmd == "/clear":
        agent.clear_history()
        console.print("[green]✅ 对话历史已清空[/green]")

    elif cmd == "/tools":
        if agent.tools:
            console.print("[bold]已注册的工具:[/bold]")
            for name, tool in agent.tools.items():
                console.print(f"  • [cyan]{name}[/cyan] — {tool.description}")
        else:
            console.print("[yellow]当前没有注册任何工具。[/yellow]")

    elif cmd == "/status":
        from core.llm.api_backend import APIBackend
        from core.llm.local_backend import LocalBackend

        api = APIBackend()
        local = LocalBackend()

        console.print("[bold]后端状态:[/bold]")
        console.print(f"  • API ({api.provider}): {'✅ 可用' if api.is_available() else '❌ 不可用'}")
        console.print(f"  • 本地 ({local.model}): {'✅ 可用' if local.is_available() else '❌ 不可用'}")

    elif cmd in ("/exit", "/quit"):
        console.print("👋 再见！")
        sys.exit(0)

    else:
        console.print(f"[yellow]未知命令: {cmd}[/yellow]")


if __name__ == "__main__":
    main()
