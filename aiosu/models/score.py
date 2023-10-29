"""
This module contains models for Score objects.
"""
from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import computed_field
from pydantic import model_validator

from ..utils.accuracy import CatchAccuracyCalculator
from ..utils.accuracy import ManiaAccuracyCalculator
from ..utils.accuracy import OsuAccuracyCalculator
from ..utils.accuracy import TaikoAccuracyCalculator
from .base import BaseModel
from .base import cast_int
from .beatmap import Beatmap
from .beatmap import Beatmapset
from .common import CurrentUserAttributes
from .gamemode import Gamemode
from .mods import Mods
from .user import User

if TYPE_CHECKING:
    from collections.abc import Mapping
    from .. import v1

__all__ = (
    "Score",
    "ScoreStatistics",
    "ScoreWeight",
    "calculate_score_completion",
)

accuracy_calculators = {
    "osu": OsuAccuracyCalculator(),
    "mania": ManiaAccuracyCalculator(),
    "taiko": TaikoAccuracyCalculator(),
    "fruits": CatchAccuracyCalculator(),
}


def calculate_score_completion(
    mode: Gamemode,
    statistics: ScoreStatistics,
    beatmap: Beatmap,
) -> Optional[float]:
    """Calculates completion for a score.

    :param mode: The gamemode of the score
    :type mode: aiosu.models.gamemode.Gamemode
    :param statistics: The statistics of the score
    :type statistics: aiosu.models.score.ScoreStatistics
    :param beatmap: The beatmap of the score
    :type beatmap: aiosu.models.beatmap.Beatmap
    :raises ValueError: If the gamemode is unknown
    :return: Completion for the given score
    :rtype: Optional[float]
    """
    if not beatmap.count_objects:
        return None

    if mode == Gamemode.STANDARD:
        return (
            (
                statistics.count_300
                + statistics.count_100
                + statistics.count_50
                + statistics.count_miss
            )
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.TAIKO:
        return (
            (statistics.count_300 + statistics.count_100 + statistics.count_miss)
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.CTB:
        return (
            (statistics.count_300 + statistics.count_100 + +statistics.count_miss)
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.MANIA:
        return (
            (
                statistics.count_300
                + statistics.count_100
                + statistics.count_50
                + statistics.count_miss
                + statistics.count_geki
                + statistics.count_katu
            )
            / beatmap.count_objects
        ) * 100

    raise ValueError("Unknown mode specified.")


class ScoreWeight(BaseModel):
    percentage: float
    pp: float


class ScoreStatistics(BaseModel):
    count_50: int
    count_100: int
    count_300: int
    count_miss: int
    count_geki: int
    count_katu: int

    @model_validator(mode="before")
    @classmethod
    def _convert_none_to_zero(cls, values: dict[str, object]) -> dict[str, object]:
        # Lazer API returns null for some statistics
        for key in values:
            if values[key] is None:
                values[key] = 0
        return values

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> ScoreStatistics:
        return cls.model_validate(
            {
                "count_50": data["count50"],
                "count_100": data["count100"],
                "count_300": data["count300"],
                "count_geki": data["countgeki"],
                "count_katu": data["countkatu"],
                "count_miss": data["countmiss"],
            },
        )


class Score(BaseModel):
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
    id: Optional[int] = None
    """Always present except for API v1 recent scores."""
    pp: Optional[float] = 0
    best_id: Optional[int] = None
    beatmap: Optional[Beatmap] = None
    beatmapset: Optional[Beatmapset] = None
    weight: Optional[ScoreWeight] = None
    user: Optional[User] = None
    rank_global: Optional[int] = None
    rank_country: Optional[int] = None
    type: Optional[str] = None
    current_user_attributes: Optional[CurrentUserAttributes] = None
    beatmap_id: Optional[int] = None
    """Only present on API v1"""

    @property
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

    @property
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

    @computed_field  # type: ignore
    @cached_property
    def completion(self) -> Optional[float]:
        """Beatmap completion.

        :raises ValueError: If mode is unknown
        :return: Beatmap completion of a score (%). 100% for passes. None if no beatmap.
        :rtype: Optional[float]
        """
        if not self.beatmap:
            return None

        if self.passed:
            return 100.0

        return calculate_score_completion(self.mode, self.statistics, self.beatmap)

    @model_validator(mode="before")
    @classmethod
    def _fail_rank(cls, values: dict[str, object]) -> dict[str, object]:
        if not values["passed"]:
            values["rank"] = "F"
        return values

    async def request_beatmap(self, client: v1.Client) -> None:
        r"""For v1 Scores: requests the beatmap from the API and sets it.

        :param client: An API v1 Client
        :type client: aiosu.v1.client.Client
        """
        if self.beatmap_id is None:
            raise ValueError("Score has unknown beatmap ID")
        if self.beatmap is None and self.beatmapset is None:
            sets = await client.get_beatmap(
                mode=self.mode,
                beatmap_id=self.beatmap_id,
            )
            self.beatmapset = sets[0]
            self.beatmap = sets[0].beatmaps[0]  # type: ignore

    @classmethod
    def _from_api_v1(
        cls,
        data: Mapping[str, object],
        mode: Gamemode,
    ) -> Score:
        statistics = ScoreStatistics._from_api_v1(data)
        score = cls.model_validate(
            {
                "id": data["score_id"],
                "user_id": data["user_id"],
                "accuracy": 0.0,
                "mods": cast_int(data["enabled_mods"]),
                "score": data["score"],
                "pp": data.get("pp", 0.0),
                "max_combo": data["maxcombo"],
                "passed": data["rank"] != "F",
                "perfect": data["perfect"],
                "statistics": statistics,
                "rank": data["rank"],
                "created_at": data["date"],
                "mode": mode,
                "beatmap_id": data.get("beatmap_id"),
                "replay": data.get("replay_available", False),
            },
        )
        score.accuracy = accuracy_calculators[str(mode)].calculate(score)
        return score
