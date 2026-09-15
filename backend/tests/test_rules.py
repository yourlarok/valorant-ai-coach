from app.analysis.baselines import load_baseline
from app.analysis.metrics import DimensionRaws
from app.coaching.planner import build_plan
from app.coaching.rules import detect_problems

BASELINE = load_baseline("钻石")


def _raws(**kw) -> DimensionRaws:
    defaults = dict(
        aim_hs_rate=0.22, duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5,
        awareness_clutch_proxy=0.15, economy_spend_per_round=1800.0,
        utility_casts_per_round=1.5, consistency_acs_cv=0.25,
    )
    defaults.update(kw)
    return DimensionRaws(**defaults)


def test_low_hs_triggers_aim_problem():
    problems = detect_problems(_raws(aim_hs_rate=0.10), BASELINE)
    assert any(p.dimension == "aim" for p in problems)
    aim_p = next(p for p in problems if p.dimension == "aim")
    assert "10" in aim_p.evidence or "0.1" in aim_p.evidence


def test_no_problem_when_above_median():
    problems = detect_problems(_raws(aim_hs_rate=0.30), BASELINE)
    assert not any(p.dimension == "aim" for p in problems)


def test_plan_maps_aim_to_aimlab():
    problems = detect_problems(_raws(aim_hs_rate=0.10), BASELINE)
    plan = build_plan(problems)
    assert plan
    assert any("Aim Lab" in t.tool or "aim" in t.tool.lower() for t in plan)
    assert all(t.freq for t in plan)
    assert all(t.done is False for t in plan)
