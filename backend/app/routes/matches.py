import random
import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.automation import process_new_matches
from app.collector.fixture import FixtureCollector
from app.db import load_profile

router = APIRouter(prefix="/api")


@router.get("/matches")
def list_matches(request: Request, name: str, count: int = 10):
    collector = request.app.state.collector
    return collector.recent_matches(name, count)


@router.get("/profile")
def profile(request: Request, name: str):
    """玩家档案：段位/RR 取档案表，其余从已采集对局聚合。"""
    matches = request.app.state.collector.recent_matches(name, 10)
    wins = 0
    acs_total = 0
    headshots = 0
    shots_total = 0
    agents: list[str] = []
    for m in matches:
        p = next(p for p in m.players if p.name == name)
        if (m.blue_score > m.red_score) == (p.team == "blue"):
            wins += 1
        acs_total += p.score
        headshots += p.headshots
        shots_total += p.headshots + p.bodyshots + p.legshots
        agents.append(p.agent)
    games = len(matches)
    counts = Counter(agents)
    # 次数降序；同次数保持近→远的首次出现顺序（稳定排序）
    main_agents = sorted(dict.fromkeys(agents), key=lambda a: -counts[a])[:3]
    saved = load_profile(name) or {}
    return {
        "name": name,
        "rank_tier": saved.get("rank_tier"),
        "rr": saved.get("rr"),
        "main_agents": main_agents,
        "recent": {
            "games": games,
            "wins": wins,
            "avg_acs": round(acs_total / games, 1) if games else 0.0,
            "avg_hs": round(headshots / shots_total, 3) if shots_total else 0.0,
        },
    }


@router.post("/dev/simulate-new-match")
def simulate_new_match(request: Request, name: str = "测试玩家#1234"):
    """fixture 演示通道：随机复制一场该玩家对局，改 match_id 与时间后
    走与真实轮询相同的自动化链路（分析 → 写通知）。"""
    collector = request.app.state.collector
    if not isinstance(collector, FixtureCollector):
        raise HTTPException(status_code=400, detail="仅 fixture 采集器支持模拟新对局")
    candidates = collector.recent_matches(name, 10)
    if not candidates:
        raise HTTPException(status_code=404, detail="该玩家没有对局可复制")
    sim = random.choice(candidates).model_copy(deep=True)
    sim.match_id = f"{sim.match_id}-sim-{uuid.uuid4().hex[:6]}"
    sim.started_at = datetime.now(timezone.utc)
    collector.add_match(sim)
    notes = process_new_matches(request.app, name)
    return {"match_id": sim.match_id, "notifications": notes}
