# Yokino — 个人 AI 助理

你的个人 AI 生活学习工作助理。

## 特性

- **多后端 LLM** — DeepSeek API 主力 + Claude API 可选 + Ollama 本地备用，API 挂了自动降级
- **16 个内置工具** — 文件读写、联网搜索、提醒、笔记、天气、知识库检索、Python/Shell 执行、工作流
- **三端访问** — CLI (Rich 终端) + 飞书 Bot + Web UI (Streamlit)
- **主动推送** — 每日简报 (8:00) + 提醒检查 (每 30 秒)
- **本地记忆** — SQLite 会话历史，知识库全文检索
- **隐私安全** — 全部本地部署，API 配置不泄露

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的 DeepSeek API Key

# 3. 启动 CLI
python main.py
```

### 可选：本地离线后备

```bash
# 安装 Ollama 并拉取模型
ollama pull qwen2.5:7b
```

API 不可用时自动切换本地模型，完全离线可用。

### 可选：Web UI

```bash
pip install streamlit
streamlit run run_web.py
```

### 可选：飞书 Bot

在 [飞书开发者后台](https://open.feishu.cn) 创建自建应用，获取 app_id 和 app_secret，填入 `config.yaml`：

```yaml
feishu:
  app_id: "cli_xxxxxxxx"
  app_secret: "xxxxxxxx"
```

然后启动：

```bash
pip install lark-oapi
python run_bot.py
```

## CLI 命令

| 命令 | 功能 |
|------|------|
| `/status` | 查看 LLM 后端状态 |
| `/tools` | 列出已注册的工具 |
| `/clear` | 清空对话历史 |
| `/exit` | 退出 |

## 内置工具 (16)

| 工具 | 功能 |
|------|------|
| `read_file` / `write_file` / `search_files` | 文件操作 |
| `web_search` | 联网搜索 (DuckDuckGo + Bing 备选) |
| `set_reminder` / `list_reminders` | 设置和查看提醒 |
| `create_note` / `read_notes` | Markdown 笔记管理 |
| `get_weather` | 天气查询 (wttr.in) |
| `search_knowledge` / `add_knowledge` / `list_knowledge` | 个人知识库 |
| `run_python` / `run_shell` | 脚本执行 (沙箱) |
| `run_workflow` / `list_workflows` | 多步骤工作流 |

## 项目结构

```
yokino/
├── main.py                  # CLI 入口
├── run_bot.py               # 飞书 Bot 入口
├── run_web.py               # Web UI 入口
├── config.example.yaml      # 配置模板
├── config.py                # 配置管理 (Pydantic)
│
├── core/
│   ├── engine.py            # Agent 主循环
│   ├── llm/                 # LLM 后端 (DeepSeek / Claude / Ollama)
│   └── tools/               # 16 个工具
│
├── interfaces/feishu.py     # 飞书 Bot (WebSocket)
├── memory/
│   ├── store.py             # SQLite 会话记忆
│   └── knowledge.py         # 知识库后端
├── scheduler/scheduler.py   # 定时任务 (每日简报 + 提醒)
│
├── knowledge/               # 用户知识库目录
├── workflows/               # 工作流配置
└── data/                    # 运行时数据 (本地)
```

## 架构

```
用户 (CLI / 飞书 / Web)
        │
   Message Router
        │
   Agent Loop (engine.py)
        ├── LLM Backend (API → 本地自动降级)
        ├── Tool System (16 tools)
        └── Memory (SQLite + Knowledge Base)
        │
   Scheduler (每日简报 + 提醒推送)
```

## 技术栈

| 组件 | 选型 |
|------|------|
| LLM 主力 | DeepSeek API |
| LLM 备用 | Ollama + Qwen 2.5 7B |
| CLI | Click + Rich |
| Bot 平台 | 飞书 (lark-oapi) |
| Web UI | Streamlit |
| 数据库 | SQLite |
| 调度 | APScheduler |
| 配置 | YAML + Pydantic |

## 许可

MIT
