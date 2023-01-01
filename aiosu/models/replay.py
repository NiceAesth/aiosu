"""
This module contains models for replays.
"""
from __future__ import annotations

from datetime import datetime
from enum import IntFlag

from .base import BaseModel
from .gamemode import Gamemode
from .mods import Mods
from .score import ScoreStatistics


class ReplayKey(IntFlag):
    """Replay key data."""

    K1 = 1 << 0
    K2 = 1 << 1
    K3 = 1 << 2
    K4 = 1 << 3
    K5 = 1 << 4
    K6 = 1 << 5
    K7 = 1 << 6
    K8 = 1 << 7
    K9 = 1 << 8
    K10 = 1 << 9
    K11 = 1 << 10
    K12 = 1 << 11
    K13 = 1 << 12
    K14 = 1 << 13
    K15 = 1 << 14
    K16 = 1 << 15
    K17 = 1 << 16
    K18 = 1 << 17


class ReplayLifebarEvent(BaseModel):
    """Replay lifebar event data."""

    time: int
    hp: float


class ReplayEvent(BaseModel):
    """Replay event data."""

    time: int
    x: float
    y: float
    keys: ReplayKey


class Replay(BaseModel):
    """Replay file data."""

    mode: Gamemode
    version: int
    map_md5: str
    player_name: str
    played_at: datetime
    replay_md5: str
    online_id: int
    score: int
    max_combo: int
    perfect_combo: bool
    mods: Mods
    statistics: ScoreStatistics
    replay_data: list[ReplayEvent]
    lifebar_data: list[ReplayLifebarEvent]

    def __repr__(self) -> str:
        return f"<Replay {self.player_name} {self.map_md5}>"

    def __str__(self) -> str:
        return f"{self.player_name} {self.played_at} {self.map_md5} +{self.mods}"
