import json

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.analysis.analyzer import analyze_match
from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws, compute_scores
from app.coaching.archetypes import match_archetypes
from app.coaching.rules import detect_problems

router = APIRouter(prefix="/api")


@router.get("/analysis/{match_id}")
def analyze(request: Request, match_id: str, name: str, rank_tier: str = "钻石"):
    collector = request.app.state.collector
    llm = request.app.state.llm
    try:
        match = collector.match_detail(match_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在")
    if not any(p.name == name for p in match.players):
        raise HTTPException(status_code=404, detail="该玩家不在此对局中")

    raws = compute_raws([match], name)
    baseline = load_baseline(rank_tier)
    scores = compute_scores(raws, baseline)
    primary, subs = match_archetypes(raws)
    try:
        analysis = analyze_match(match, name, raws, primary, subs, llm)
    except (json.JSONDecodeError, ValueError, KeyError, httpx.HTTPError, RuntimeError):
        # LLM 返回非法 JSON、响应缺少 choices 键、HTTP 调用失败或未配置等异常时降级到模板化输出，避免接口 500
        analysis = analyze_match(match, name, raws, primary, subs, None)
    problems = detect_problems(raws, baseline)
    return {
        "scores": scores, "raws": raws,
        "primary": primary, "subs": subs,
        "analysis": analysis, "problems": problems,
    }
