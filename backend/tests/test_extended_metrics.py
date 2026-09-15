import json
from pathlib import Path

from app.analysis.metrics import ExtendedStats, extended_stats
from app.schemas import Match

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> Match:
    raw = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    return Match.model_validate(raw)


def test_extended_stats_match_sample_known_values():
    stats = extended_stats([_load("match_sample.json")], "测试玩家#1234")
    assert isinstance(stats, ExtendedStats)
    # ADR = 2900 / 22 回合
    assert abs(stats.adr - 2900 / 22) < 1e-6
    # KAST：12 个击杀回合 + 3 个存活回合 + 5 个助攻回合 = 20/22
    assert abs(stats.kast - 20 / 22) < 1e-6
    # 首杀参与率 = 4 / 22
    assert abs(stats.fb_participation - 4 / 22) < 1e-6
    # 手枪局：第 1、13 回合均为蓝队（目标玩家方）获胜
    assert stats.pistol_wr == 1.0
    # 残局胜率 = 1/2
    assert stats.clutch_wr == 0.5


def test_extended_stats_multi_match_aggregation():
    matches = [_load("match_sample.json"), _load("match_002.json")]
    stats = extended_stats(matches, "测试玩家#1234")
    # match_002：20 回合，damage 3200 → 两场合计 (2900+3200)/42
    assert abs(stats.adr - (2900 + 3200) / 42) < 1e-6
    # match_002 首杀 6 次 → (4+6)/42
    assert abs(stats.fb_participation - 10 / 42) < 1e-6
    # 残局：1+2 胜 / 2+3 场
    assert abs(stats.clutch_wr - 3 / 5) < 1e-6
    assert 0.0 <= stats.kast <= 1.0
    assert 0.0 <= stats.pistol_wr <= 1.0


def test_extended_stats_clutch_wr_none_when_no_attempts():
    raw = json.loads((FIXTURE_DIR / "match_sample.json").read_text(encoding="utf-8"))
    for pl in raw["players"]:
        pl["clutch_wins"] = 0
        pl["clutch_attempts"] = 0
    match = Match.model_validate(raw)
    stats = extended_stats([match], "测试玩家#1234")
    assert stats.clutch_wr is None


def test_extended_stats_legacy_fixture_without_round_fields():
    # 无回合级新字段的旧数据仍可计算（KAST 退化为按总击杀估算）
    raw = {
        "match_id": "legacy-001",
        "map": "源工重镇",
        "started_at": "2026-09-10T20:00:00+08:00",
        "blue_score": 13,
        "red_score": 7,
        "players": [
            {"puuid": "p1", "name": "测试玩家#1234", "agent": "捷风", "team": "blue",
             "kills": 15, "deaths": 10, "assists": 4, "damage_made": 2600,
             "first_bloods": 3},
        ],
    }
    stats = extended_stats([Match.model_validate(raw)], "测试玩家#1234")
    assert abs(stats.adr - 2600 / 20) < 1e-6
    assert abs(stats.fb_participation - 3 / 20) < 1e-6
    assert 0.0 <= stats.kast <= 1.0
    assert stats.clutch_wr is None


def test_extended_stats_player_not_found():
    import pytest

    with pytest.raises(ValueError):
        extended_stats([_load("match_sample.json")], "不存在的玩家#0000")
