from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PlayerMatchStats(BaseModel):
    puuid: str
    name: str  # 昵称#数字ID
    agent: str
    team: Literal["blue", "red"]
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    score: int = 0  # ACS
    headshots: int = 0
    bodyshots: int = 0
    legshots: int = 0
    damage_made: int = 0
    first_bloods: int = 0
    first_deaths: int = 0
    econ_spent: int = 0
    ability_casts: dict[str, int] = Field(default_factory=dict)
    party_id: str | None = None


class RoundResult(BaseModel):
    round_num: int
    winning_team: Literal["blue", "red"]
    end_type: str = "elimination"  # elimination/defuse/detonate/time


class Match(BaseModel):
    match_id: str
    mode: str = "竞技模式"
    map: str
    started_at: datetime
    blue_score: int
    red_score: int
    players: list[PlayerMatchStats]
    rounds: list[RoundResult] = Field(default_factory=list)
