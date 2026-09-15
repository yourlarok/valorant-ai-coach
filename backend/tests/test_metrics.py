import json
from pathlib import Path

from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws, compute_scores
from app.schemas import Match


def _matches() -> list[Match]:
    raw = json.loads(
        (Path(__file__).parent / "fixtures" / "match_sample.json").read_text(encoding="utf-8")
    )
    return [Match.model_validate(raw)]


def test_compute_raws():
    raws = compute_raws(_matches(), "测试玩家#1234")
    # 6/(6+10+2) = 0.333
    assert abs(raws.aim_hs_rate - 6 / 18) < 1e-6
    # first_bloods - first_deaths = 2
    assert raws.duel_first_blood_diff == 2.0
    assert raws.utility_casts_per_round >= 0


def test_compute_scores_bounds_and_grade():
    raws = compute_raws(_matches(), "测试玩家#1234")
    scores = compute_scores(raws, load_baseline("钻石"))
    for v in (scores.aim, scores.duel, scores.awareness,
              scores.economy, scores.utility, scores.consistency, scores.overall):
        assert 0 <= v <= 100
    assert scores.grade in ("S", "A", "B", "C", "D")


def test_median_maps_to_50():
    baseline = load_baseline("钻石")
    from app.analysis.metrics import DimensionRaws
    raws = DimensionRaws(
        aim_hs_rate=baseline.aim.median,
        duel_first_blood_diff=baseline.duel.median,
        duel_first_duel_winrate=baseline.duel.median,
        awareness_clutch_proxy=baseline.awareness.median,
        economy_spend_per_round=baseline.economy.median,
        utility_casts_per_round=baseline.utility.median,
        consistency_acs_cv=baseline.consistency.median,
    )
    scores = compute_scores(raws, baseline)
    assert abs(scores.aim - 50) < 1e-6
