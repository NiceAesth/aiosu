"""
This module contains models for replays.
"""

from __future__ import annotations

from datetime import datetime
from enum import IntFlag
from enum import unique

from pydantic import model_validator

from ..base import BaseModel
from ..gamemode import Gamemode
from ..lazer import LazerReplayData
from ..mods import Mod
from ..mods import Mods
from ..score import ScoreStatistics

__all__ = (
    "ReplayEvent",
    "ReplayFile",
    "ReplayKey",
    "ReplayLifebarEvent",
)


def _parse_skip_offset(events: list[ReplayEvent], mods: Mods) -> int:
    """Parse the skip offset from a list of replay events."""
    if len(events) < 2:
        return 0
    if Mod.Autoplay in mods:
        return events[1].time - 100000
    return events[1].time


def _parse_rng_seed(events: list[ReplayEvent]) -> int:
    """Parse the RNG seed from a list of replay events."""
    if len(events) < 2:
        return 0
    return int(events[-1].keys)


@unique
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


class ReplayFile(BaseModel):
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
    mod_extras: float | None = None
    skip_offset: int | None = None
    rng_seed: int | None = None
    lazer_replay_data: LazerReplayData | None = None

    def __repr__(self) -> str:
        return f"<Replay {self.player_name} {self.map_md5}>"

    def __str__(self) -> str:
        return f"{self.player_name} {self.played_at} {self.map_md5} +{self.mods}"

    @model_validator(mode="after")
    def _add_skip_offset(self) -> ReplayFile:
        if not self.skip_offset:
            self.skip_offset = _parse_skip_offset(
                self.replay_data,
                self.mods,
            )
        return self

    @model_validator(mode="after")
    def _add_rng_seed(self) -> ReplayFile:
        if not self.rng_seed and self.version >= 2013_03_19:
            self.rng_seed = _parse_rng_seed(self.replay_data)
        return self
