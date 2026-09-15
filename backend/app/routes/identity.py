from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import load_settings, save_settings
from app.db import (list_profile_names, mark_match_analyzed, remove_profile,
                    save_profile)

router = APIRouter(prefix="/api")


class IdentityBody(BaseModel):
    name: str


@router.get("/identity")
def get_identity():
    name = load_settings().identity.name
    return {"name": name, "onboarded": name is not None}


@router.post("/identity")
def bind_identity(request: Request, body: IdentityBody):
    """绑定游戏身份：先验证玩家存在（采集器查得到对局），再持久化到
    config.json。存量对局全部预标记为已分析，避免自动化首轮把历史
    对局当新对局轰炸分析。"""
    name = body.name.strip()
    matches = request.app.state.collector.recent_matches(name, 10)
    if not matches:
        raise HTTPException(status_code=404, detail="找不到该玩家")
    settings = load_settings()
    old_name = settings.identity.name
    settings.identity.name = name
    save_settings(settings)
    # 自动化轮询按档案表玩家名驱动：新玩家补建档案，
    # 换绑时移除旧身份档案，避免继续为旧玩家拉新对局
    if name not in list_profile_names():
        save_profile(name, None, None)
    if old_name and old_name != name:
        remove_profile(old_name)
    for m in matches:
        mark_match_analyzed(m.match_id, name)
    return {"ok": True, "name": name}
