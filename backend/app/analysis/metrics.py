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


class ExtendedStats(BaseModel):
    adr: float  # 场均回合伤害 = damage_made 总和 / 总回合
    kast: float  # 击杀/助攻/存活回合占比
    fb_participation: float  # 首杀参与率 = first_bloods / 总回合
    pistol_wr: float  # 手枪局胜率
    clutch_wr: float | None = None  # 残局胜率，无残局场次时为 None


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
    # score 字段本身即 ACS（场均口径），无需再除以回合数
    acs_values = [float(p.score) for _, p in stats]

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


def extended_stats(matches: list[Match], player_name: str) -> ExtendedStats:
    stats = _player_stats(matches, player_name)

    def _match_rounds(m: Match) -> int:
        return len(m.rounds) if m.rounds else m.blue_score + m.red_score

    total_rounds = sum(_match_rounds(m) for m, _ in stats)
    damage = sum(p.damage_made for _, p in stats)
    fb = sum(p.first_bloods for _, p in stats)

    kast_rounds = 0
    pistol_played = 0
    pistol_won = 0
    for m, p in stats:
        m_rounds = _match_rounds(m)
        if m.rounds:
            kill_rounds = sum(1 for r in m.rounds if r.player_kills > 0)
            for r in m.rounds:
                if r.pistol:
                    pistol_played += 1
                    if r.winning_team == p.team:
                        pistol_won += 1
        else:
            # 无回合级数据时按总击杀估算击杀回合数
            kill_rounds = min(p.kills, m_rounds)
        kill_or_survive = min(kill_rounds + p.survival_rounds, m_rounds)
        kast_rounds += kill_or_survive + min(p.assists, m_rounds - kill_or_survive)

    clutch_wins = sum(p.clutch_wins for _, p in stats)
    clutch_attempts = sum(p.clutch_attempts for _, p in stats)

    return ExtendedStats(
        adr=damage / total_rounds if total_rounds else 0.0,
        kast=kast_rounds / total_rounds if total_rounds else 0.0,
        fb_participation=fb / total_rounds if total_rounds else 0.0,
        pistol_wr=pistol_won / pistol_played if pistol_played else 0.0,
        clutch_wr=clutch_wins / clutch_attempts if clutch_attempts else None,
    )


def _percentile_score(value: float, dim: DimensionBaseline, lower_is_better: bool = False) -> float:
    if lower_is_better:
        if dim.median <= 0:
            return 50.0
        if value <= dim.median:
            # 好于中位数：越接近 0 分越高，median 映射 50，0 映射 100
            return min(100.0, 50.0 + 50.0 * (dim.median - value) / dim.median)
        # 差于中位数：按相对偏差从 50 递减，最低钳到 0
        return max(0.0, 50.0 - 50.0 * (value - dim.median) / dim.median)
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
