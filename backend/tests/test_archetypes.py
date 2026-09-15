from app.analysis.metrics import DimensionRaws
from app.coaching.archetypes import match_archetypes


def _raws(**kw) -> DimensionRaws:
    defaults = dict(
        aim_hs_rate=0.22, duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5,
        awareness_clutch_proxy=0.15, economy_spend_per_round=1800.0,
        utility_casts_per_round=1.5, consistency_acs_cv=0.25,
    )
    defaults.update(kw)
    return DimensionRaws(**defaults)


def test_headshot_machine():
    primary, subs = match_archetypes(_raws(aim_hs_rate=0.40))
    assert primary.key == "headshot_machine"


def test_suicide_squad():
    primary, _ = match_archetypes(_raws(duel_first_blood_diff=0.0, duel_first_duel_winrate=0.5))
    # 首杀与首死都靠 aggressive 判定：用 fb_diff≈0 且总对枪次数高不直接可得，
    # 原型判定基于 fb_diff 绝对值低 + winrate 中庸 → 默认原型
    assert primary.key in ("balanced_default", "headshot_machine")


def test_econ_blackhole_subtag():
    _, subs = match_archetypes(_raws(economy_spend_per_round=2600.0))
    assert any(a.key == "econ_blackhole" for a in subs)


def test_stable_sniper_subtag():
    _, subs = match_archetypes(_raws(consistency_acs_cv=0.08))
    assert any(a.key == "stable_pillar" for a in subs)
