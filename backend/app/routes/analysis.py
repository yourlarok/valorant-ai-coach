import json

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.analysis.analyzer import analyze_match
from app.analysis.baselines import load_baseline
from app.analysis.engine import analyze_deep
from app.analysis.metrics import compute_raws, compute_scores, extended_stats
from app.coaching.archetypes import match_archetypes
from app.coaching.rules import detect_problems

router = APIRouter(prefix="/api")

_DIM_NAMES = {"aim": "瞄准", "duel": "对枪", "awareness": "意识",
              "economy": "经济", "utility": "技能", "consistency": "稳定性"}
_TREND_THRESHOLD = 5.0  # 前后半段分差超过该值才算明显进步/退步


@router.get("/analysis/weekly")
def weekly(request: Request, name: str, rank_tier: str = "钻石"):
    collector = request.app.state.collector
    matches = collector.recent_matches(name, 10)
    games = len(matches)
    if not games:
        return {"narrative": "暂无对局数据，先打几把再来看周报。",
                "improved": [], "regressed": [], "games": 0}

    baseline = load_baseline(rank_tier)
    raws = compute_raws(matches, name)
    scores = compute_scores(raws, baseline)
    ext = extended_stats(matches, name)
    problems = detect_problems(raws, baseline)

    wins = 0
    for m in matches:
        p = next(p for p in m.players if p.name == name)
        if (m.blue_score > m.red_score) == (p.team == "blue"):
            wins += 1

    improved: list[str] = []
    regressed: list[str] = []
    trend_text = ""
    chrono = list(reversed(matches))  # 时间正序
    mid = games // 2
    if mid >= 1:
        s_first = compute_scores(compute_raws(chrono[:mid], name), baseline)
        s_second = compute_scores(compute_raws(chrono[mid:], name), baseline)
        deltas = {k: getattr(s_second, k) - getattr(s_first, k) for k in _DIM_NAMES}
        improved = [f"{_DIM_NAMES[k]}（{deltas[k]:+.1f}）"
                    for k in deltas if deltas[k] >= _TREND_THRESHOLD]
        regressed = [f"{_DIM_NAMES[k]}（{deltas[k]:+.1f}）"
                     for k in deltas if deltas[k] <= -_TREND_THRESHOLD]
        if improved and regressed:
            trend_text = (f"相比前半段，{'、'.join(improved)} 进步明显；"
                          f"{'、'.join(regressed)} 有所下滑。")
        elif improved:
            trend_text = f"相比前半段，{'、'.join(improved)} 进步明显，其余维度基本持平。"
        elif regressed:
            trend_text = f"相比前半段，{'、'.join(regressed)} 有所下滑，其余维度基本持平。"
        else:
            trend_text = "前后半段各维度评分基本持平，发挥进入平台期。"

    parts = [
        f"近 {games} 场 {wins} 胜 {games - wins} 负，"
        f"综合评分 {scores.overall}（{scores.grade} 级）。",
        f"ADR {ext.adr:.0f}、KAST {ext.kast:.0%}、"
        f"首杀参与率 {ext.fb_participation:.0%}、手枪局胜率 {ext.pistol_wr:.0%}。",
    ]
    if ext.clutch_wr is not None:
        parts.append(f"残局胜率 {ext.clutch_wr:.0%}。")
    if trend_text:
        parts.append(trend_text)
    if problems:
        parts.append(f"下周训练优先解决「{_DIM_NAMES[problems[0].dimension]}」："
                     f"{problems[0].description}。")
    return {"narrative": "".join(parts),
            "improved": improved, "regressed": regressed, "games": games}


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
    ext = extended_stats([match], name)
    baseline = load_baseline(rank_tier)
    scores = compute_scores(raws, baseline)
    primary, subs = match_archetypes(raws)
    try:
        analysis = analyze_match(match, name, raws, primary, subs, llm)
    except (json.JSONDecodeError, ValueError, KeyError, httpx.HTTPError, RuntimeError):
        # LLM 返回非法 JSON、响应缺少 choices 键、HTTP 调用失败或未配置等异常时降级到模板化输出，避免接口 500
        analysis = analyze_match(match, name, raws, primary, subs, None)
    problems = detect_problems(raws, baseline)
    deep = analyze_deep(match, name, raws, ext, primary, subs, problems, llm)
    return {
        "scores": scores, "raws": raws,
        "primary": primary, "subs": subs,
        "analysis": analysis, "problems": problems,
        "deep": deep, "ext": ext, "mock": deep.mock,
    }
