#!/usr/bin/env python3
"""Friday Web UI — 基于 Streamlit 的网页界面"""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import streamlit as st

from config import load_config, get_config
from core.engine import Agent
from core.tools.file_ops import ReadFileTool, WriteFileTool, SearchFilesTool
from core.tools.web_search import WebSearchTool
from core.tools.reminder import SetReminderTool, ListRemindersTool
from core.tools.note import CreateNoteTool, ReadNotesTool
from core.tools.weather import WeatherTool
from core.tools.knowledge_base import SearchKnowledgeTool, AddKnowledgeTool, ListKnowledgeTool
from core.tools.script_runner import RunPythonTool, RunShellTool
from core.tools.workflow import WorkflowTool, ListWorkflowsTool

st.set_page_config(
    page_title="Friday — AI 助理",
    page_icon="🤖",
    layout="wide",
)


@st.cache_resource
def init_agent():
    load_config("config.yaml")
    agent = Agent()
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
    return agent


def main():
    agent = init_agent()
    cfg = get_config()

    # Sidebar
    with st.sidebar:
        st.title("🤖 Friday")
        st.caption("你的个人 AI 助理")

        st.divider()
        st.subheader("⚙️ 状态")

        api_provider = cfg.llm.api.provider
        local_model = cfg.llm.local.model
        st.write(f"API: `{api_provider}`")
        st.write(f"本地: `{local_model}`")

        from core.llm.api_backend import APIBackend
        from core.llm.local_backend import LocalBackend
        api = APIBackend()
        local = LocalBackend()
        st.write(f"API 可用: {'✅' if api.is_available() else '❌'}")
        st.write(f"本地可用: {'✅' if local.is_available() else '❌'}")

        st.divider()
        st.subheader("🛠 工具")
        for name, tool in agent.tools.items():
            st.caption(f"• **{name}** — {tool.description[:40]}...")

        st.divider()
        if st.button("🗑 清空对话历史"):
            agent.clear_history()
            st.session_state.messages = []
            st.rerun()

    # Main chat area
    st.title("Friday")
    st.caption("就像钢铁侠的星期五，随时在线。")

    # Init chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("输入你的问题..."):
        # Show user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                full_response = ""
                for chunk in agent.chat(prompt):
                    full_response += chunk
            st.markdown(full_response.strip())
        st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})


if __name__ == "__main__":
    main()
