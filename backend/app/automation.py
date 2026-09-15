import asyncio
import logging

from fastapi import FastAPI

from app.analysis.baselines import load_baseline
from app.analysis.engine import DeepAnalysis, analyze_deep
from app.analysis.metrics import compute_raws, extended_stats
from app.coaching.archetypes import match_archetypes
from app.coaching.rules import detect_problems
from app.collector.fixture import FixtureCollector
from app.db import (is_match_analyzed, list_profile_names, load_profile,
                    mark_match_analyzed)
from app.notifications import Notification, create_notification
from app.schemas import Match

logger = logging.getLogger(__name__)


def run_deep_analysis(app: FastAPI, match: Match, player_name: str) -> DeepAnalysis:
    """与 /api/analysis/{match_id} 相同的深度分析管线，供后台自动化同步调用。"""
    profile = load_profile(player_name)
    rank_tier = (profile or {}).get("rank_tier") or "钻石"
    raws = compute_raws([match], player_name)
    ext = extended_stats([match], player_name)
    baseline = load_baseline(rank_tier)
    primary, subs = match_archetypes(raws)
    problems = detect_problems(raws, baseline)
    try:
        return analyze_deep(match, player_name, raws, ext, primary, subs,
                            problems, app.state.llm)
    except Exception:
        # 任何未预期异常以 llm=None 重试一次，走 Mock/降级路径
        return analyze_deep(match, player_name, raws, ext, primary, subs,
                            problems, None)


def process_new_matches(app: FastAPI, player_name: str) -> list[Notification]:
    """自动化链路核心：发现未分析过的新对局 → 深度分析 → 写通知。
    同步函数，测试与 dev 模拟端点直接调用；按 match_id 幂等。"""
    fresh = [m for m in app.state.collector.recent_matches(player_name, 10)
             if not is_match_analyzed(m.match_id)]
    fresh.sort(key=lambda m: m.started_at)  # 旧→新依次处理
    made = []
    for m in fresh:
        run_deep_analysis(app, m, player_name)
        mark_match_analyzed(m.match_id, player_name)
        p = next(p for p in m.players if p.name == player_name)
        made.append(create_notification(
            "analysis_done",
            "新对局深度复盘完成",
            f"{m.map} {m.blue_score}:{m.red_score}（{p.agent}），点击查看完整报告。",
            f"/report/{m.match_id}",
        ))
    return made


class AutomationEngine:
    """后台轮询器：定时拉取已绑定玩家的最新对局并自动分析。
    fixture 采集器数据静态，不启动轮询（演示走 POST /api/dev/simulate-new-match）。"""

    def __init__(self, poll_interval_min: int = 5):
        self.poll_interval_min = poll_interval_min
        self._task: asyncio.Task | None = None

    def start(self, app: FastAPI) -> None:
        if isinstance(app.state.collector, FixtureCollector):
            return
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop(app))

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _loop(self, app: FastAPI) -> None:
        while True:
            try:
                for name in list_profile_names():
                    made = process_new_matches(app, name)
                    if made:
                        logger.info("自动化分析 %s：新增 %d 条通知", name, len(made))
            except Exception:
                logger.exception("自动化轮询失败，下一周期重试")
            await asyncio.sleep(self.poll_interval_min * 60)
