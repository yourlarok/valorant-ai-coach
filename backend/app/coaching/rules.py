from pydantic import BaseModel

from app.analysis.baselines import Baseline
from app.analysis.metrics import DimensionRaws


class Problem(BaseModel):
    dimension: str  # aim/duel/awareness/economy/utility/consistency
    description: str
    evidence: str


def detect_problems(raws: DimensionRaws, baseline: Baseline) -> list[Problem]:
    problems: list[Problem] = []
    if raws.aim_hs_rate < baseline.aim.median * 0.8:
        problems.append(Problem(
            dimension="aim",
            description="爆头率明显低于同段位水平，瞄准习惯偏向身体",
            evidence=f"爆头率 {raws.aim_hs_rate:.0%}，段位中位数 {baseline.aim.median:.0%}",
        ))
    if raws.duel_first_duel_winrate < baseline.duel.median * 0.8:
        problems.append(Problem(
            dimension="duel",
            description="首轮对枪胜率偏低，开局交火经常吃亏",
            evidence=f"首轮对枪胜率 {raws.duel_first_duel_winrate:.0%}，段位中位数 {baseline.duel.median:.0%}",
        ))
    if raws.awareness_clutch_proxy < baseline.awareness.median * 0.6:
        problems.append(Problem(
            dimension="awareness",
            description="残局与多杀场景贡献不足，意识与站位有提升空间",
            evidence=f"残局代理指标 {raws.awareness_clutch_proxy:.2f}，段位中位数 {baseline.awareness.median:.2f}",
        ))
    if raws.economy_spend_per_round > baseline.economy.p90:
        problems.append(Problem(
            dimension="economy",
            description="每回合花费过高，eco 局可能存在强行起枪",
            evidence=f"回合均花费 {raws.economy_spend_per_round:.0f}，段位 p90 {baseline.economy.p90:.0f}",
        ))
    if raws.utility_casts_per_round < baseline.utility.median * 0.6:
        problems.append(Problem(
            dimension="utility",
            description="技能使用率偏低，没有发挥英雄技能价值",
            evidence=f"回合均技能 {raws.utility_casts_per_round:.1f}，段位中位数 {baseline.utility.median:.1f}",
        ))
    if raws.consistency_acs_cv > 0.40:
        problems.append(Problem(
            dimension="consistency",
            description="发挥波动大，神一场鬼一场",
            evidence=f"ACS 变异系数 {raws.consistency_acs_cv:.2f}，超过 0.40 阈值",
        ))
    return problems
