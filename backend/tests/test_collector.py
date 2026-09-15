from pathlib import Path

from app.collector.fixture import FixtureCollector
from app.collector.wegame import WeGameCollector, map_wegame_detail
from app.config import WeGameSettings

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_fixture_collector_lists_and_detail():
    c = FixtureCollector(FIXTURE_DIR)
    matches = c.recent_matches("测试玩家#1234")
    assert len(matches) >= 1
    detail = c.match_detail(matches[0].match_id)
    assert detail.match_id == matches[0].match_id
    assert len(detail.players) == 10


def test_wegame_detail_mapping():
    # WeGame 原始响应（结构按真机抓包校准，此处定义映射契约）
    raw = {
        "matchId": "wg-001",
        "mapName": "亚海悬城",
        "queueName": "竞技模式",
        "startTime": "2026-09-14T20:00:00",
        "teamA": {"score": 13},
        "teamB": {"score": 9},
        "players": [
            {"id": "p1", "nickname": "测试玩家#1234", "heroName": "捷风", "team": "A",
             "kill": 18, "death": 14, "assist": 5, "combatScore": 245,
             "headshot": 6, "bodyshot": 10, "legshot": 2,
             "damage": 2900, "firstKill": 4, "firstDeath": 2, "goldSpent": 38500},
        ],
    }
    match = map_wegame_detail(raw)
    assert match.match_id == "wg-001"
    assert match.blue_score == 13
    me = match.players[0]
    assert me.name == "测试玩家#1234"
    assert me.kills == 18 and me.team == "blue"


def test_wegame_collector_uses_injected_fetch():
    captured = {}

    def fake_fetch(path: str, params: dict) -> dict:
        captured["path"] = path
        return {"list": []}

    c = WeGameCollector(WeGameSettings(), fetch_json=fake_fetch)
    assert c.recent_matches("测试玩家#1234") == []
    assert captured["path"] == WeGameSettings().match_list_path
