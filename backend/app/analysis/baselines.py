from pydantic import BaseModel


class DimensionBaseline(BaseModel):
    median: float
    p90: float


class Baseline(BaseModel):
    aim: DimensionBaseline
    duel: DimensionBaseline
    awareness: DimensionBaseline
    economy: DimensionBaseline
    utility: DimensionBaseline
    consistency: DimensionBaseline


# 冷启动经验值，待采集数据积累后按段位真实分布校准
_BASELINES: dict[str, Baseline] = {
    "钻石": Baseline(
        aim=DimensionBaseline(median=0.22, p90=0.35),
        duel=DimensionBaseline(median=0.5, p90=0.7),
        awareness=DimensionBaseline(median=0.15, p90=0.30),
        economy=DimensionBaseline(median=1800.0, p90=2200.0),
        utility=DimensionBaseline(median=1.5, p90=2.5),
        consistency=DimensionBaseline(median=0.25, p90=0.10),
    ),
}


def load_baseline(rank_tier: str) -> Baseline:
    return _BASELINES.get(rank_tier, _BASELINES["钻石"])
