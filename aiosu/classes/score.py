from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

from .beatmap import Beatmap
from .beatmap import Beatmapset
from .gamemode import Gamemode
from .mods import Mods
from .user import User


@dataclass(frozen=True)
class ScoreWeight:
    percentage: float
    pp: float


@dataclass(frozen=True)
class ScoreStatistics:
    count_50: int
    count_100: int
    count_300: int
    count_geki: int
    count_katu: int
    count_miss: int


@dataclass()
class Score:
    id: int
    user_id: int
    accuracy: float
    mods: Mods
    score: int
    max_combo: int
    passed: bool
    perfect: bool
    statistics: ScoreStatistics
    rank: str
    created_at: datetime
    mode: Gamemode
    replay: bool
    pp: Optional[float] = 0
    diff_attributes: Optional[dict] = None
    best_id: Optional[int] = None
    beatmap: Optional[Beatmap] = None
    beatmapset: Optional[Beatmapset] = None
    weight: Optional[ScoreWeight] = None
    user: Optional[User] = None
    rank_global: Optional[int] = None
    rank_country: Optional[int] = None

    @property
    def completion(self):
        if self.mode == Gamemode.STANDARD:
            return (
                (
                    self.statistics.count_300
                    + self.statistics.count_100
                    + self.statistics.count_50
                    + self.statistics.count_miss
                )
                / self.beatmap.count_objects
            ) * 100
        if self.mode == Gamemode.TAIKO:
            return (
                (
                    self.statistics.count_300
                    + self.statistics.count_100
                    + self.statistics.count_miss
                )
                / self.beatmap.count_objects
            ) * 100
        if self.mode == Gamemode.CTB:
            return (
                (
                    self.statistics.count_300
                    + self.statistics.count_100
                    + +self.statistics.count_miss
                )
                / self.beatmap.count_objects
            ) * 100
        if self.mode == Gamemode.STANDARD:
            return (
                (
                    self.statistics.count_300
                    + self.statistics.count_100
                    + self.statistics.count_50
                    + self.statistics.count_miss
                    + self.statistics.count_geki
                    + self.statistics.count_katu
                )
                / self.beatmap.count_objects
            ) * 100

    @property
    def score_url(self):
        # score.id has undefined behaviour, best_id is the one you should use as it returns None if the URL does not exist
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}"
            if self.best_id
            else None
        )

    @property
    def replay_url(self):
        # score.id has undefined behaviour, best_id is the one you should use as it returns None if the URL does not exist
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}/download"
            if self.best_id
            else None
        )
