"""
This module contains models for lazer specific data.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import computed_field
from pydantic import Field
from pydantic import model_validator

from .base import BaseModel
from .beatmap import Beatmap
from .beatmap import Beatmapset
from .common import CurrentUserAttributes
from .gamemode import Gamemode
from .score import ScoreWeight
from .user import User

__all__ = (
    "LazerMod",
    "LazerScoreStatistics",
    "LazerReplayData",
    "LazerScore",
)


def calculate_score_completion(
    statistics: LazerScoreStatistics,
    beatmap: Beatmap,
) -> float:
    """Calculates completion for a score.

    :param statistics: The statistics of the score
    :type statistics: aiosu.models.lazer.LazerScoreStatistics
    :param beatmap: The beatmap of the score
    :type beatmap: aiosu.models.beatmap.Beatmap
    :raises ValueError: If the gamemode is unknown
    :return: Completion for the given score
    :rtype: float
    """
    return (
        (
            statistics.perfect
            + statistics.good
            + statistics.great
            + statistics.ok
            + statistics.meh
            + statistics.miss
        )
        / beatmap.count_objects
    ) * 100


class LazerMod(BaseModel):
    """Temporary model for lazer mods."""

    acronym: str
    settings: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.acronym


class LazerScoreStatistics(BaseModel):
    ok: int = 0
    meh: int = 0
    miss: int = 0
    great: int = 0
    ignore_hit: int = 0
    ignore_miss: int = 0
    large_bonus: int = 0
    large_tick_hit: int = 0
    large_tick_miss: int = 0
    small_bonus: int = 0
    small_tick_hit: int = 0
    small_tick_miss: int = 0
    good: int = 0
    perfect: int = 0
    legacy_combo_increase: int = 0

    @computed_field
    def count_300(self) -> int:
        return self.great

    @computed_field
    def count_100(self) -> int:
        return self.ok

    @computed_field
    def count_50(self) -> int:
        return self.meh

    @computed_field
    def count_miss(self) -> int:
        return self.miss

    @computed_field
    def count_geki(self) -> int:
        return self.perfect

    @computed_field
    def count_katu(self) -> int:
        return self.good


class LazerReplayData(BaseModel):
    mods: list[LazerMod]
    statistics: LazerScoreStatistics
    maximum_statistics: LazerScoreStatistics


class LazerScore(BaseModel):
    id: int
    accuracy: float
    beatmap_id: int
    max_combo: int
    maximum_statistics: LazerScoreStatistics
    mods: list[LazerMod]
    passed: bool
    rank: str
    ruleset_id: int
    ended_at: datetime
    statistics: LazerScoreStatistics
    total_score: int
    user_id: int
    replay: bool
    type: str
    current_user_attributes: CurrentUserAttributes
    beatmap: Beatmap
    beatmapset: Beatmapset
    user: User
    build_id: Optional[int] = None
    started_at: Optional[datetime] = None
    best_id: Optional[int] = None
    legacy_perfect: Optional[bool] = None
    pp: Optional[float] = None
    weight: Optional[ScoreWeight] = None

    @computed_field
    def mods_str(self) -> str:
        return "".join(str(mod) for mod in self.mods)

    @computed_field
    def created_at(self) -> datetime:
        return self.ended_at

    @computed_field
    def completion(self) -> Optional[float]:
        """Beatmap completion.

        :return: Beatmap completion of a score (%). 100% for passes. None if no beatmap.
        :rtype: Optional[float]
        """
        if not self.beatmap:
            return None

        if self.passed:
            return 100.0

        return calculate_score_completion(self.statistics, self.beatmap)

    @computed_field
    def mode(self) -> Gamemode:
        return Gamemode(self.ruleset_id)

    @computed_field
    def score(self) -> int:
        return self.total_score

    @computed_field
    def score_url(self) -> Optional[str]:
        r"""Link to the score.

        :return: Link to the score on the osu! website
        :rtype: Optional[str]
        """
        if (not self.id and not self.best_id) or not self.passed:
            return None
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}"
            if self.best_id
            else f"https://osu.ppy.sh/scores/{self.id}"
        )

    @computed_field
    def replay_url(self) -> Optional[str]:
        r"""Link to the replay.

        :return: Link to download the replay on the osu! website
        :rtype: Optional[str]
        """
        if not self.replay:
            return None
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}/download"
            if self.best_id
            else f"https://osu.ppy.sh/scores/{self.id}/download"
        )

    @model_validator(mode="before")
    @classmethod
    def _fail_rank(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values["passed"]:
            values["rank"] = "F"
        return values
