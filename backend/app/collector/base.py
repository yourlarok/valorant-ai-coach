from typing import Protocol

from app.schemas import Match


class Collector(Protocol):
    def recent_matches(self, name: str, count: int = 10) -> list[Match]: ...
    def match_detail(self, match_id: str) -> Match: ...
