# Yokino — 个人 AI 助理

你的个人 AI 生活学习工作助理，支持 CLI、Web UI、飞书 Bot 三种交互方式。

## 特性

- **多后端 LLM** — DeepSeek API 主力 + Claude API 可选 + Ollama 本地备用，API 挂了自动降级
- **16 个内置工具** — 文件读写、联网搜索、提醒、笔记、天气、知识库检索、Python/Shell 执行、工作流
- **三端访问** — CLI (Rich 终端) + 飞书 Bot + Web UI (Streamlit)
- **主动推送** — 每日简报 (8:00) + 提醒检查 (每 30 秒)
- **本地记忆** — SQLite 会话历史，知识库全文检索
- **隐私安全** — 全部本地部署，API 配置不会上传到仓库

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- （可选）[Ollama](https://ollama.com) — 用于本地离线后备

### 2. 安装

```bash
# 克隆仓库
git clone https://github.com/Baisiyang28/yokino.git
cd yokino

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
# 复制配置模板
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入你的 API Key：

```yaml
llm:
  primary: api          # 主力后端：api 或 local
  fallback: local       # 备用后端：API 不可用时自动切换

  api:
    provider: deepseek  # deepseek 或 claude
    deepseek:
      api_key: "sk-你的DeepSeek-API-Key"   # 必填
      model: deepseek-chat
      base_url: https://api.deepseek.com
    claude:
      api_key: ""       # 可选，使用 Claude 时填写
      model: claude-sonnet-4-20250514

  local:
    base_url: http://localhost:11434
    model: qwen2.5:7b

memory:
  max_turns: 50
  db_path: data/conversations.db

feishu:
  app_id: ""            # 使用飞书 Bot 时填写
  app_secret: ""
```

> 如果你在国内不方便访问 GitHub，也可以用 [SiliconFlow](https://siliconflow.cn) 或 [DeepSeek 官方](https://platform.deepseek.com) 的 API。将 `base_url` 和 `model` 改为对应值即可。

### 4. 启动

```bash
# CLI 模式（推荐入门）
python main.py

# 指定配置文件
python main.py --config my-config.yaml
```

---

## 三种使用方式

### 方式一：CLI 终端（最常用）

```bash
cd yokino
python main.py
```

启动后进入交互式对话界面，输入问题即可获得回复。Yokino 会自动调用工具完成任务。

**CLI 命令：**

| 命令 | 功能 |
|------|------|
| `/status` | 查看 API 和本地后端是否可用 |
| `/tools` | 列出所有已注册的工具及说明 |
| `/clear` | 清空当前对话历史 |
| `/exit` | 退出程序 |

**对话示例：**

```
你 帮我查一下北京今天天气怎么样

Yokino 思考中...

┌─ Yokino ─────────────────────────────┐
│ 北京今天晴，气温 25°C，体感 27°C，   │
│ 湿度 45%，西北风 15km/h。            │
│ 适合出门，记得防晒。                 │
└──────────────────────────────────────┘

你 设置一个提醒，30分钟后提醒我开会

Yokino 思考中...

┌─ Yokino ─────────────────────────────┐
│ ✅ 提醒已设置：「开会」              │
│ — 将于 2026-05-17 15:30:00 触发     │
└──────────────────────────────────────┘

你 帮我在 knowledge 目录下创建一个笔记，记录今天的天气情况

Yokino 思考中...

┌─ Yokino ─────────────────────────────┐
│ 笔记已创建: knowledge/notes/天气记录.md │
└──────────────────────────────────────┘
```

### 方式二：Web UI（Streamlit）

```bash
pip install streamlit
cd yokino
streamlit run run_web.py
```

浏览器打开 `http://localhost:8501`，即可在网页中与 Yokino 对话。左侧边栏显示后端状态和已注册工具，支持一键清空对话历史。

### 方式三：飞书 Bot

在 [飞书开发者后台](https://open.feishu.cn) 创建自建应用：

1. 获取 `app_id` 和 `app_secret`
2. 填入 `config.yaml` 的 `feishu` 段
3. 在飞书后台开启「机器人」能力并配置事件订阅

```bash
pip install lark-oapi
cd yokino
python run_bot.py
```

启动后 Bot 会自动接收和回复飞书消息，并定时推送每日简报（每天 8:00）和到期提醒。

---

## 内置工具详解（16 个）

Yokino 会在对话中自动判断何时使用工具。你也可以直接要求它使用某个工具。

### 文件操作

| 工具 | 功能 | 参数 |
|------|------|------|
| `read_file` | 读取文件内容（最大 5000 字符） | `path` — 文件路径 |
| `write_file` | 写入内容到文件（覆盖写入） | `path` — 文件路径, `content` — 内容 |
| `search_files` | 在目录下搜索文件名和内容 | `keyword` — 关键词, `directory` — 目录（默认当前） |

**用法示例：**
```
你 帮我读一下 D:/notes/todo.txt 的内容
你 把这段代码写入 D:/projects/test.py
你 在 D:/documents 目录下搜索包含"发票"的文件
```

### 联网搜索

| 工具 | 功能 | 参数 |
|------|------|------|
| `web_search` | 搜索互联网信息（DuckDuckGo + Bing 备选） | `query` — 搜索词, `num` — 条数（默认 5） |

**用法示例：**
```
你 帮我搜索一下 Python 3.13 的新特性
你 查一下今天的热点新闻
```

> 搜索使用 DuckDuckGo API，国内可能较慢。如需更好体验，可自行配置代理。

### 提醒

| 工具 | 功能 | 参数 |
|------|------|------|
| `set_reminder` | 设置定时提醒 | `message` — 提醒内容, `time` — ISO 格式或相对时间 |
| `list_reminders` | 查看所有未触发的提醒 | 无 |

**时间格式说明：**
- ISO 绝对时间：`2026-05-17T15:30:00`
- 相对时间：`30m`（30分钟）、`1h`（1小时）、`2h30m`（2小时30分）、`1d`（1天）

**用法示例：**
```
你 30分钟后提醒我去拿快递
你 明天早上9点提醒我开会
你 我还有哪些未触发的提醒？
```

> 提醒数据存储在 `data/reminders.json`，在 CLI 模式下不会自动推送（需配合飞书 Bot 或自行查看）。

### 笔记

| 工具 | 功能 | 参数 |
|------|------|------|
| `create_note` | 创建 Markdown 笔记 | `title` — 标题, `content` — 内容 |
| `read_notes` | 搜索和读取笔记 | `keyword` — 关键词（可选，留空列出全部） |

**用法示例：**
```
你 帮我记个笔记，标题是"项目思路"，内容是...
你 我有哪些关于"Python"的笔记？
你 列出我所有的笔记
```

> 笔记保存在 `knowledge/notes/` 目录下，每个笔记是一个 `.md` 文件，可以直接用编辑器打开。

### 知识库

| 工具 | 功能 | 参数 |
|------|------|------|
| `search_knowledge` | 全文搜索知识库 | `query` — 关键词, `limit` — 条数（默认 5） |
| `add_knowledge` | 添加文档到知识库 | `title` — 标题, `content` — 内容, `category` — 分类 |
| `list_knowledge` | 列出知识库所有文档 | `category` — 按分类过滤（可选） |

**分类说明：**
- `notes` — 笔记
- `bookmarks` — 书签
- `reference` — 参考资料

**用法示例：**
```
你 把这篇 Docker 教程加入知识库
你 搜索知识库里关于"数据库"的文档
你 列出 reference 分类下的所有文档
```

> 知识库文件保存在 `knowledge/` 目录下，按分类分子目录存储。

### 天气

| 工具 | 功能 | 参数 |
|------|------|------|
| `get_weather` | 查询城市天气 | `city` — 城市名（拼音或英文） |

**用法示例：**
```
你 北京今天天气怎么样？
你 查一下 Tokyo 的天气
```

> 天气数据来自 [wttr.in](https://wttr.in)，国内可能较慢。

### 脚本执行

| 工具 | 功能 | 参数 |
|------|------|------|
| `run_python` | 在临时沙箱中执行 Python 代码 | `code` — Python 代码, `timeout` — 超时秒数（默认 30） |
| `run_shell` | 执行 Shell 命令（危险命令需确认） | `command` — 命令, `confirm` — 危险确认, `timeout` — 超时秒数（默认 60） |

**Shell 安全机制：**
执行包含以下危险模式时会拒绝并等待确认：
- 文件删除：`rm -rf`, `del /f`
- 磁盘操作：`dd if=`, `mkfs`, `format`
- 数据库破坏：`DROP`, `DELETE FROM`, `TRUNCATE`
- 系统控制：`shutdown`, `reboot`, `sudo`, `su`
- 管道安装：`curl ... | sh`, `wget ... | sh`

**用法示例：**
```
你 帮我用 Python 算一下 1 到 100 的素数有哪些
你 执行 pip list 看看安装了哪些包
你 帮我确认删除 temp 目录（需手动设 confirm=True）
```

### 工作流

| 工具 | 功能 | 参数 |
|------|------|------|
| `run_workflow` | 执行预设的多步骤工作流 | `name` — 工作流名称, `params` — 参数（可选） |
| `list_workflows` | 列出所有可用工作流 | 无 |

**创建工作流：**

在 `workflows/` 目录下创建 JSON 文件，例如 `workflows/日报.json`：

```json
{
  "description": "生成每日工作报告",
  "steps": [
    {
      "type": "print",
      "description": "输出日期",
      "message": "📅 日期: {date}"
    },
    {
      "type": "file_read",
      "description": "读取今日笔记",
      "path": "knowledge/notes/今日记录.md"
    },
    {
      "type": "file_write",
      "description": "生成报告",
      "path": "reports/{date}.md",
      "content": "# 日报 ({date})\n\n## 完成事项\n\n- \n\n## 待办\n\n- "
    }
  ]
}
```

**用法示例：**
```
你 运行日报工作流，参数 date=2026-05-17
你 有哪些可用的工作流？
```

---

## 配置详解

### LLM 后端切换

Yokino 会优先使用 `primary` 指定的后端，不可用时自动降至 `fallback`：

```yaml
llm:
  primary: api       # api = DeepSeek/Claude; local = Ollama
  fallback: local    # 备用
```

你也可以改为完全离线模式：

```yaml
llm:
  primary: local
  fallback: local
```

### 本地离线后备

如果你不想用任何云 API，可以完全依赖 Ollama 本地运行：

```bash
# 1. 安装 Ollama
# 从 https://ollama.com 下载安装

# 2. 拉取模型
ollama pull qwen2.5:7b

# 3. 修改 config.yaml
# llm.primary: local
# llm.fallback: local

# 4. 启动
python main.py
```

> qwen2.5:7b 约 4.4GB，首次拉取需要几分钟。7B 模型的推理质量不如 DeepSeek API，但完全离线、免费、隐私。

### 记忆与对话历史

```yaml
memory:
  max_turns: 50        # 保留最近 50 轮对话
  db_path: data/conversations.db
```

对话历史存储在 SQLite 中，超过 `max_turns` 轮后自动丢弃最早的记录。使用 `/clear` 手动清空当前会话。

---

## 项目结构

```
yokino/
├── main.py                  # CLI 入口
├── run_bot.py               # 飞书 Bot 入口
├── run_web.py               # Web UI 入口
├── config.example.yaml      # 配置模板（提交到 git）
├── config.yaml              # 你的配置（gitignore，不提交）
├── config.py                # 配置管理 (Pydantic)
├── requirements.txt         # Python 依赖
│
├── core/
│   ├── engine.py            # Agent 主循环
│   ├── llm/                 # LLM 后端 (DeepSeek / Claude / Ollama)
│   │   ├── base.py          # 后端抽象基类
│   │   ├── api_backend.py   # API 后端（DeepSeek / Claude）
│   │   └── local_backend.py # Ollama 本地后端
│   └── tools/               # 16 个工具
│       ├── base.py          # 工具抽象基类
│       ├── file_ops.py      # 文件读写搜索
│       ├── web_search.py    # 联网搜索
│       ├── reminder.py      # 提醒设置与查看
│       ├── note.py          # 笔记创建与检索
│       ├── weather.py       # 天气查询
│       ├── knowledge_base.py # 知识库增删查
│       ├── script_runner.py # Python/Shell 沙箱
│       └── workflow.py      # 多步骤工作流
│
├── interfaces/
│   └── feishu.py            # 飞书 Bot (WebSocket 长连接)
│
├── memory/
│   ├── store.py             # SQLite 会话记忆
│   └── knowledge.py         # 知识库全文检索后端
│
├── scheduler/
│   └── scheduler.py         # 定时任务 (每日简报 + 提醒检查)
│
├── knowledge/               # 用户知识库目录（本地）
│   ├── notes/               #   笔记
│   ├── bookmarks/           #   书签
│   └── reference/           #   参考文档
│
├── workflows/               # 工作流 JSON 定义
└── data/                    # 运行时数据 (SQLite + 提醒 JSON)
```

---

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

**Agent 循环流程：**

1. 用户输入 → 存入会话历史
2. 检测可用后端（API 优先，不可用则切本地）
3. 构建消息（System Prompt + 历史记录 + 工具定义）
4. 调用 LLM 流式输出
5. 如果 LLM 返回 tool_call → 执行工具 → 将结果追加到历史 → 回到步骤 4
6. 如果 LLM 返回纯文本 → 保存回复 → 结束本轮
7. 最多循环 10 次，防止死循环

---

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
| 配置 | YAML + Pydantic v2 |
| 搜索 | DuckDuckGo API + Bing 备选 |
| 天气 | wttr.in |

## 常见问题

**Q: 启动后提示"未配置 API Key"？**
A: 确保 `config.yaml` 在 `yokino/` 目录下，且 `llm.api.deepseek.api_key` 已填写。如果从其他目录运行，请使用 `--config` 指定配置文件路径。

**Q: DeepSeek API 很慢或连不上？**
A: DeepSeek 偶尔会限流。可以：
- 切换到 Claude API（`provider: claude`）
- 改回本地 Ollama 模式（`primary: local`）
- 检查是否需要代理访问

**Q: 飞书 Bot 收不到消息？**
A: 检查：
1. `app_id` 和 `app_secret` 是否正确
2. 飞书后台是否开启了机器人能力
3. 事件订阅是否配置正确
4. `pip install lark-oapi` 是否已安装

**Q: 知识库和笔记有什么区别？**
A: 笔记（`create_note`）是轻量级的 Markdown 文件，适合随手记录。知识库（`add_knowledge`）自带全文检索，按分类管理，适合长期积累的参考资料。

**Q: 对话历史存在哪里？**
A: `data/conversations.db`（SQLite），程序退出后保留。用 `/clear` 或直接删除该文件即可清空。

## 许可

MIT
