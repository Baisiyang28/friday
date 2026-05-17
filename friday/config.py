"""Friday 配置管理"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class DeepSeekConfig(BaseModel):
    api_key: str = ""
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"


class ClaudeConfig(BaseModel):
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"


class ApiConfig(BaseModel):
    provider: str = "deepseek"
    deepseek: DeepSeekConfig = DeepSeekConfig()
    claude: ClaudeConfig = ClaudeConfig()


class LocalConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"


class LLMConfig(BaseModel):
    primary: str = "api"
    fallback: str = "local"
    api: ApiConfig = ApiConfig()
    local: LocalConfig = LocalConfig()


class MemoryConfig(BaseModel):
    max_turns: int = 50
    db_path: str = "data/conversations.db"


class FeishuConfig(BaseModel):
    app_id: str = ""
    app_secret: str = ""


class Config(BaseModel):
    llm: LLMConfig = LLMConfig()
    memory: MemoryConfig = MemoryConfig()
    feishu: FeishuConfig = FeishuConfig()


_config: Optional[Config] = None


def load_config(path: str = "config.yaml") -> Config:
    """加载 YAML 配置文件"""
    global _config

    config_path = Path(path)
    if not config_path.exists() and not config_path.is_absolute():
        # 如果 CWD 下找不到，尝试在 friday 包目录下查找
        fallback = Path(__file__).parent / path
        if fallback.exists():
            config_path = fallback
    if not config_path.exists():
        _config = Config()
        return _config

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    _config = Config(**data)
    return _config


def get_config() -> Config:
    """获取全局配置（已加载）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
