import json

from pydantic import BaseModel

from app.analysis.llm import LLMClient
from app.analysis.metrics import DimensionRaws
from app.analysis.prompts import SYSTEM_COACH, build_match_prompt
from app.coaching.archetypes import Archetype
from app.schemas import Match


class MatchAnalysis(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    roast: str


def _stats_block(match: Match, player_name: str, raws: DimensionRaws) -> str:
    p = next(p for p in match.players if p.name == player_name)
    return (
        f"地图 {match.map}，比分 {match.blue_score}:{match.red_score}，英雄 {p.agent}\n"
        f"KDA {p.kills}/{p.deaths}/{p.assists}，ACS {p.score}，爆头率 {raws.aim_hs_rate:.0%}\n"
        f"首杀 {p.first_bloods} 首死 {p.first_deaths}，回合均花费 {raws.economy_spend_per_round:.0f}"
    )


def analyze_match(match: Match, player_name: str, raws: DimensionRaws,
                  primary: Archetype, subs: list[Archetype],
                  llm: LLMClient | None) -> MatchAnalysis:
    block = _stats_block(match, player_name, raws)
    if llm is not None and llm.is_configured():
        resp = llm.chat(SYSTEM_COACH, build_match_prompt(player_name, block, primary.title))
        data = json.loads(resp.strip().removeprefix("```json").removesuffix("```"))
        return MatchAnalysis.model_validate(data)
    # 降级：模板化输出
    p = next(p for p in match.players if p.name == player_name)
    return MatchAnalysis(
        summary=f"{player_name} 使用 {p.agent} 打出 {p.kills}/{p.deaths}/{p.assists}，ACS {p.score}。",
        strengths=[f"爆头率 {raws.aim_hs_rate:.0%}"] if raws.aim_hs_rate > 0.25 else [],
        weaknesses=[f"爆头率仅 {raws.aim_hs_rate:.0%}"] if raws.aim_hs_rate <= 0.15 else [],
        roast=f"系统鉴定：{primary.title}。{primary.roast_hint}",
    )
