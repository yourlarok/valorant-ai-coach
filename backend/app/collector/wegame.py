from collections.abc import Callable
from datetime import datetime

import httpx

from app.config import WeGameSettings
from app.schemas import Match, PlayerMatchStats


def map_wegame_detail(raw: dict) -> Match:
    """WeGame 原始对局详情 → 标准化 Match。字段名按真机抓包结果校准。"""
    players = [
        PlayerMatchStats(
            puuid=p["id"], name=p["nickname"], agent=p["heroName"],
            team="blue" if p["team"] == "A" else "red",
            kills=p.get("kill", 0), deaths=p.get("death", 0), assists=p.get("assist", 0),
            score=p.get("combatScore", 0),
            headshots=p.get("headshot", 0), bodyshots=p.get("bodyshot", 0), legshots=p.get("legshot", 0),
            damage_made=p.get("damage", 0),
            first_bloods=p.get("firstKill", 0), first_deaths=p.get("firstDeath", 0),
            econ_spent=p.get("goldSpent", 0),
        )
        for p in raw.get("players", [])
    ]
    return Match(
        match_id=raw["matchId"], mode=raw.get("queueName", "竞技模式"),
        map=raw["mapName"], started_at=datetime.fromisoformat(raw["startTime"]),
        blue_score=raw["teamA"]["score"], red_score=raw["teamB"]["score"],
        players=players,
    )


class WeGameCollector:
    """结构完整的 WeGame 采集器。登录态获取与真实端点需 Windows 真机联调：
    1. 在本机专用 Chrome 登录 WeGame（或 CDP 复用已有登录态）
    2. 抓包校准 WeGameSettings 中的端点路径与 map_wegame_detail 的字段名
    """

    def __init__(self, settings: WeGameSettings,
                 fetch_json: Callable[[str, dict], dict] | None = None):
        self.settings = settings
        self._fetch = fetch_json or self._http_fetch

    def _http_fetch(self, path: str, params: dict) -> dict:
        resp = httpx.get(f"{self.settings.base_url}{path}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def recent_matches(self, name: str, count: int = 10) -> list[Match]:
        data = self._fetch(self.settings.match_list_path, {"nickname": name, "count": count})
        return [map_wegame_detail(self._fetch(self.settings.match_detail_path,
                                              {"matchId": item["matchId"]}))
                for item in data.get("list", [])[:count]]

    def match_detail(self, match_id: str) -> Match:
        return map_wegame_detail(self._fetch(self.settings.match_detail_path,
                                             {"matchId": match_id}))
