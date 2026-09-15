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
    weapon_kills: dict[str, int] = Field(default_factory=dict)  # 武器击杀分布
    ability_damage: int = 0  # 技能伤害
    ability_assists: int = 0  # 技能辅助（助攻/闪光致盲等）
    survival_rounds: int = 0  # 存活回合数
    clutch_wins: int = 0  # 残局获胜次数
    clutch_attempts: int = 0  # 残局尝试次数
    party_id: str | None = None


class RoundResult(BaseModel):
    round_num: int
    winning_team: Literal["blue", "red"]
    end_type: str = "elimination"  # elimination/defuse/detonate/time
    player_kills: int = 0  # 目标玩家该回合击杀数
    player_first_blood: bool = False  # 目标玩家是否首杀
    player_first_death: bool = False  # 目标玩家是否首死
    pistol: bool = False  # 是否手枪局


class Match(BaseModel):
    match_id: str
    mode: str = "竞技模式"
    map: str
    started_at: datetime
    blue_score: int
    red_score: int
    players: list[PlayerMatchStats]
    rounds: list[RoundResult] = Field(default_factory=list)
