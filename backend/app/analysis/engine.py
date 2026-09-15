import json

import httpx
from pydantic import BaseModel

from app.analysis import prompts
from app.analysis.metrics import DimensionRaws, ExtendedStats
from app.analysis.mock_provider import MockProvider
from app.coaching.archetypes import Archetype
from app.coaching.planner import TrainingTask, build_plan
from app.coaching.rules import Problem
from app.schemas import Match

DIMENSION_KEYS = ("aim", "duel", "awareness", "economy", "utility", "consistency")


class DeepAnalysis(BaseModel):
    overview: str
    dimensions: dict[str, str]  # 六维 key → 诊断段落
    moments: list[str]
    prescription: list[TrainingTask]
    roast: str
    mock: bool = False  # 任一阶段走了 Mock 通道即为 True


# ---- 数据事实清单（基准对比层输出，喂给各段 prompt）----

def _stats_block(match: Match, player_name: str, raws: DimensionRaws,
                 ext: ExtendedStats) -> str:
    p = next(p for p in match.players if p.name == player_name)
    clutch = f"{ext.clutch_wr:.0%}" if ext.clutch_wr is not None else "无样本"
    return (
        f"地图 {match.map}，比分 {match.blue_score}:{match.red_score}，英雄 {p.agent}（{p.team} 队）\n"
        f"KDA {p.kills}/{p.deaths}/{p.assists}，ACS {p.score}，爆头率 {raws.aim_hs_rate:.0%}\n"
        f"ADR {ext.adr:.1f}，KAST {ext.kast:.0%}，首杀参与率 {ext.fb_participation:.0%}，"
        f"手枪局胜率 {ext.pistol_wr:.0%}，残局胜率 {clutch}\n"
        f"首杀 {p.first_bloods} 首死 {p.first_deaths}，存活 {p.survival_rounds} 回合，"
        f"回合均花费 {raws.economy_spend_per_round:.0f}，"
        f"回合均技能 {raws.utility_casts_per_round:.1f}，"
        f"ACS 变异系数 {raws.consistency_acs_cv:.2f}"
    )


def _facts_block(problems: list[Problem]) -> str:
    if not problems:
        return "- 各维度均在段位基准之上"
    return "\n".join(f"- {p.dimension}: {p.evidence}" for p in problems)


def _rounds_digest(match: Match, player_name: str) -> str:
    if not match.rounds:
        return "无回合级数据"
    p = next(p for p in match.players if p.name == player_name)
    lines = []
    for r in match.rounds:
        tags = []
        if r.pistol:
            tags.append("手枪局")
        if r.player_first_blood:
            tags.append("玩家首杀")
        if r.player_first_death:
            tags.append("玩家首死")
        if r.player_kills >= 2:
            tags.append(f"玩家{r.player_kills}杀")
        win = "胜" if r.winning_team == p.team else "负"
        lines.append(f"第{r.round_num}回合 {win}（{r.end_type}）{'/'.join(tags)}")
    return "\n".join(lines)


# ---- 输出校验与降级 ----

def _parse(text: str):
    return json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())


def _validate_overview(data) -> dict:
    if not isinstance(data, dict):
        raise ValueError("overview 段应返回 JSON 对象")
    if not (isinstance(data.get("overview"), str) and data["overview"].strip()):
        raise ValueError("overview 缺失或为空")
    if not (isinstance(data.get("roast"), str) and data["roast"].strip()):
        raise ValueError("roast 缺失或为空")
    return {"overview": data["overview"], "roast": data["roast"]}


def _validate_dimensions(data) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ValueError("dimensions 段应返回 JSON 对象")
    missing = [k for k in DIMENSION_KEYS
               if not (isinstance(data.get(k), str) and data[k].strip())]
    if missing:
        raise ValueError(f"dimensions 缺少维度: {missing}")
    return {k: data[k] for k in DIMENSION_KEYS}


def _validate_moments(data) -> list[str]:
    if not isinstance(data, list) or not data:
        raise ValueError("moments 段应返回非空数组")
    if not all(isinstance(m, str) and m.strip() for m in data):
        raise ValueError("moments 元素必须是非空字符串")
    return data


def _validate_prescription(data) -> list[TrainingTask]:
    if not isinstance(data, list) or not data:
        raise ValueError("prescription 段应返回非空数组")
    return [TrainingTask.model_validate(t) for t in data]


_STAGE_ERRORS = (json.JSONDecodeError, ValueError, KeyError,
                 httpx.HTTPError, RuntimeError)


def _run_stage(client, mock: MockProvider, system: str, user: str,
               validate) -> tuple:
    """先走真 LLM，失败重试一次，仍失败则回退 MockProvider。
    返回 (validated_result, used_mock)。"""
    for _ in range(2):
        try:
            return validate(_parse(client.chat(system, user))), isinstance(client, MockProvider)
        except _STAGE_ERRORS:
            continue
    return validate(_parse(mock.chat(system, user))), True


def analyze_deep(match: Match, player_name: str, raws: DimensionRaws,
                 ext: ExtendedStats, primary: Archetype, subs: list[Archetype],
                 problems: list[Problem], llm) -> DeepAnalysis:
    mock = MockProvider(match=match, player_name=player_name, raws=raws, ext=ext,
                        primary=primary, subs=subs, problems=problems)
    client = llm if (llm is not None and llm.is_configured()) else mock

    stats_block = _stats_block(match, player_name, raws, ext)
    facts_block = _facts_block(problems)
    rounds_digest = _rounds_digest(match, player_name)
    base_tasks = build_plan(problems)
    tasks_block = json.dumps([t.model_dump() for t in base_tasks],
                             ensure_ascii=False) if base_tasks else "[]（本场无问题点）"
    problems_block = "\n".join(f"- {p.description}（{p.evidence}）" for p in problems) \
        or "本场未发现明显问题点"

    overview, m1 = _run_stage(
        client, mock, prompts.SYSTEM_OVERVIEW,
        prompts.build_overview_prompt(player_name, stats_block, facts_block, primary.title),
        _validate_overview)
    dimensions, m2 = _run_stage(
        client, mock, prompts.SYSTEM_DIMENSIONS,
        prompts.build_dimensions_prompt(player_name, stats_block, facts_block),
        _validate_dimensions)
    moments, m3 = _run_stage(
        client, mock, prompts.SYSTEM_MOMENTS,
        prompts.build_moments_prompt(player_name, stats_block, rounds_digest),
        _validate_moments)
    prescription, m4 = _run_stage(
        client, mock, prompts.SYSTEM_PRESCRIPTION,
        prompts.build_prescription_prompt(player_name, problems_block, tasks_block),
        _validate_prescription)

    return DeepAnalysis(
        overview=overview["overview"], roast=overview["roast"],
        dimensions=dimensions, moments=moments, prescription=prescription,
        mock=any([m1, m2, m3, m4]),
    )
