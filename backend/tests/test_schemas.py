import json
from pathlib import Path

from app.schemas import Match

MATCH_SAMPLE_PATH = Path(__file__).parent / "fixtures" / "match_sample.json"


def test_match_sample_parses():
    raw = json.loads(MATCH_SAMPLE_PATH.read_text(encoding="utf-8"))
    match = Match.model_validate(raw)
    assert match.match_id == "fixture-match-001"
    assert len(match.players) == 10
    me = next(p for p in match.players if p.name == "测试玩家#1234")
    assert me.kills == 18
    assert match.blue_score + match.red_score >= 13


def test_headshot_rate_derivable():
    raw = json.loads(MATCH_SAMPLE_PATH.read_text(encoding="utf-8"))
    match = Match.model_validate(raw)
    me = next(p for p in match.players if p.name == "测试玩家#1234")
    total = me.headshots + me.bodyshots + me.legshots
    assert total > 0
