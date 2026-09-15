from pydantic import BaseModel

from app.analysis.baselines import Baseline, DimensionBaseline
from app.schemas import Match


class DimensionRaws(BaseModel):
    aim_hs_rate: float
    duel_first_blood_diff: float
    duel_first_duel_winrate: float
    awareness_clutch_proxy: float
    economy_spend_per_round: float
    utility_casts_per_round: float
    consistency_acs_cv: float


class AbilityScores(BaseModel):
    aim: float
    duel: float
    awareness: float
    economy: float
    utility: float
    consistency: float
    overall: float
    grade: str


def _player_stats(matches: list[Match], player_name: str):
    stats = []
    for m in matches:
        p = next((p for p in m.players if p.name == player_name), None)
        if p is not None:
            stats.append((m, p))
    if not stats:
        raise ValueError(f"对局中找不到玩家: {player_name}")
    return stats


def compute_raws(matches: list[Match], player_name: str) -> DimensionRaws:
    stats = _player_stats(matches, player_name)
    kills = sum(p.kills for _, p in stats)
    hs = sum(p.headshots for _, p in stats)
    fb = sum(p.first_bloods for _, p in stats)
    fd = sum(p.first_deaths for _, p in stats)
    rounds = sum(max(m.blue_score + m.red_score, 1) for m, _ in stats)
    casts = sum(sum(p.ability_casts.values()) for _, p in stats)
    acs_values = [p.score / max(m.blue_score + m.red_score, 1) for m, p in stats]

    hs_rate = hs / kills if kills else 0.0
    fb_diff = float(fb - fd)
    fb_wr = fb / (fb + fd) if (fb + fd) else 0.5
    # 冷启动代理指标：多杀占比（视觉复盘上线后换被侧身击杀占比）
    multi_kills = sum(1 for _, p in stats if p.kills >= 2 * max(p.deaths, 1) and p.kills >= 15)
    clutch_proxy = multi_kills / len(stats)
    econ = sum(p.econ_spent for _, p in stats) / rounds
    casts_per_round = casts / rounds
    mean_acs = sum(acs_values) / len(acs_values)
    if len(acs_values) > 1 and mean_acs > 0:
        var = sum((v - mean_acs) ** 2 for v in acs_values) / (len(acs_values) - 1)
        cv = (var ** 0.5) / mean_acs
    else:
        cv = 0.25

    return DimensionRaws(
        aim_hs_rate=hs_rate,
        duel_first_blood_diff=fb_diff,
        duel_first_duel_winrate=fb_wr,
        awareness_clutch_proxy=clutch_proxy,
        economy_spend_per_round=econ,
        utility_casts_per_round=casts_per_round,
        consistency_acs_cv=cv,
    )


def _percentile_score(value: float, dim: DimensionBaseline, lower_is_better: bool = False) -> float:
    if lower_is_better:
        value = -value
        median, p90 = -dim.median, -dim.p90
        if p90 < median:
            median, p90 = p90, median
    else:
        median, p90 = dim.median, dim.p90
    if value <= median:
        return max(0.0, 50.0 * value / median) if median else 50.0
    span = p90 - median
    return min(100.0, 50.0 + 40.0 * (value - median) / span) if span > 0 else 90.0


_WEIGHTS = {"aim": 0.22, "duel": 0.20, "awareness": 0.16,
            "economy": 0.14, "utility": 0.14, "consistency": 0.14}


def compute_scores(raws: DimensionRaws, baseline: Baseline) -> AbilityScores:
    aim = _percentile_score(raws.aim_hs_rate, baseline.aim)
    duel = _percentile_score(raws.duel_first_duel_winrate, baseline.duel)
    awareness = _percentile_score(raws.awareness_clutch_proxy, baseline.awareness)
    economy = _percentile_score(raws.economy_spend_per_round, baseline.economy)
    utility = _percentile_score(raws.utility_casts_per_round, baseline.utility)
    consistency = _percentile_score(raws.consistency_acs_cv, baseline.consistency, lower_is_better=True)
    dims = {"aim": aim, "duel": duel, "awareness": awareness,
            "economy": economy, "utility": utility, "consistency": consistency}
    overall = sum(dims[k] * _WEIGHTS[k] for k in dims)
    grade = "S" if overall >= 85 else "A" if overall >= 70 else "B" if overall >= 50 else "C" if overall >= 30 else "D"
    return AbilityScores(**dims, overall=round(overall, 1), grade=grade)
