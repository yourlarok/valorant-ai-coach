import json
import os
from pathlib import Path

from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "coach.db"
FIXTURE_DIR = BASE_DIR / "tests" / "fixtures"
CONFIG_PATH = BASE_DIR / "config.json"


class LLMSettings(BaseModel):
    # 默认内置 DeepSeek（快速模型 deepseek-chat）；key 只存本地或走环境变量
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"


class WeGameSettings(BaseModel):
    # 真机联调时按实际抓包结果修改；路径集中在此便于维护
    match_list_path: str = "/wegine/valorant/v1/match-history"
    match_detail_path: str = "/wegine/valorant/v1/match-detail"
    base_url: str = "https://mlol.qt.qq.com"


class Settings(BaseModel):
    llm: LLMSettings = LLMSettings()
    wegame: WeGameSettings = WeGameSettings()


def load_settings() -> Settings:
    if CONFIG_PATH.exists():
        settings = Settings.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        settings = Settings()
    # 环境变量兜底：DEEPSEEK_API_KEY 优先于空配置
    if not settings.llm.api_key:
        env_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if env_key:
            settings.llm.api_key = env_key
    return settings


def save_settings(settings: Settings) -> None:
    CONFIG_PATH.write_text(
        json.dumps(settings.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
