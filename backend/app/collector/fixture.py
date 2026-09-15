import json
from pathlib import Path

from app.schemas import Match


class FixtureCollector:
    def __init__(self, fixture_dir: Path):
        self.fixture_dir = fixture_dir

    def _load_all(self) -> list[Match]:
        matches = []
        for f in sorted(self.fixture_dir.glob("*.json")):
            matches.append(Match.model_validate(json.loads(f.read_text(encoding="utf-8"))))
        return matches

    def recent_matches(self, name: str, count: int = 10) -> list[Match]:
        mine = [m for m in self._load_all()
                if any(p.name == name for p in m.players)]
        return sorted(mine, key=lambda m: m.started_at, reverse=True)[:count]

    def match_detail(self, match_id: str) -> Match:
        for m in self._load_all():
            if m.match_id == match_id:
                return m
        raise KeyError(f"fixture 中不存在对局 {match_id}")
