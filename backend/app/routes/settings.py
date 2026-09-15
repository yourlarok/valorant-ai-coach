from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.analysis.llm import LLMClient
from app.config import LLMSettings, load_settings, save_settings

router = APIRouter(prefix="/api")


class LLMSettingsBody(BaseModel):
    base_url: str | None = None
    api_key: str | None = None  # None = 保持不变；空字符串 = 清除 key
    model: str | None = None


def _public(llm: LLMClient) -> dict:
    # 永不回显 api_key 本体，只返回 configured 布尔
    return {"base_url": llm.base_url, "model": llm.model,
            "configured": llm.is_configured()}


@router.get("/settings/llm")
def get_llm_settings(request: Request):
    return _public(request.app.state.llm)


@router.put("/settings/llm")
def put_llm_settings(request: Request, body: LLMSettingsBody):
    current = request.app.state.llm
    updated = LLMSettings(
        base_url=body.base_url or current.base_url,
        api_key=current.api_key if body.api_key is None else body.api_key,
        model=body.model or current.model,
    )
    settings = load_settings()
    settings.llm = updated
    save_settings(settings)
    # 热更新，无需重启
    request.app.state.llm = LLMClient(updated.base_url, updated.api_key, updated.model)
    return _public(request.app.state.llm)
