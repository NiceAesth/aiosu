"""
This module contains models for Score objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import root_validator

from ..utils.accuracy import CatchAccuracyCalculator
from ..utils.accuracy import ManiaAccuracyCalculator
from ..utils.accuracy import OsuAccuracyCalculator
from ..utils.accuracy import TaikoAccuracyCalculator
from .base import BaseModel
from .beatmap import Beatmap
from .beatmap import Beatmapset
from .common import CurrentUserAttributes
from .gamemode import Gamemode
from .mods import Mods
from .user import User

if TYPE_CHECKING:
    from typing import Any
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
) -> float:
    """Calculates completion for a score.

    :param mode: The gamemode of the score
    :type mode: aiosu.models.gamemode.Gamemode
    :param statistics: The statistics of the score
    :type statistics: aiosu.models.score.ScoreStatistics
    :param beatmap: The beatmap of the score
    :type beatmap: aiosu.models.beatmap.Beatmap
    :raises ValueError: If the gamemode is unknown
    :return: Completion for the given score
    :rtype: float
    """
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

    @root_validator(pre=True)
    def _convert_none_to_zero(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Lazer API returns null for some statistics
        for key in values:
            if values[key] is None:
                values[key] = 0
        return values

    @classmethod
    def _from_api_v1(cls, data: Any) -> ScoreStatistics:
        return cls.parse_obj(
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
    id: Optional[int]
    """Always present except for API v1 recent scores."""
    pp: Optional[float] = 0
    best_id: Optional[int]
    beatmap: Optional[Beatmap]
    beatmapset: Optional[Beatmapset]
    weight: Optional[ScoreWeight]
    user: Optional[User]
    rank_global: Optional[int]
    rank_country: Optional[int]
    type: Optional[str]
    current_user_attributes: Optional[CurrentUserAttributes]
    beatmap_id: Optional[int]
    """Only present on API v1"""

    @property
    def completion(self) -> float:
        """Beatmap completion.

        :raises ValueError: If beatmap is None
        :raises ValueError: If mode is unknown
        :return: Beatmap completion of a score (%). 100% for passes
        :rtype: float
        """
        if not self.beatmap:
            raise ValueError("Beatmap object is not set.")

        return calculate_score_completion(self.mode, self.statistics, self.beatmap)

    @property
    def score_url(self) -> Optional[str]:
        # score.id has undefined behaviour, best_id is the one you should use as it returns None if the URL does not exist
        r"""Link to the score.

        :return: Link to the score on the osu! website
        :rtype: Optional[str]
        """
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}"
            if self.best_id
            else None
        )

    @property
    def replay_url(self) -> Optional[str]:
        # score.id has undefined behaviour, best_id is the one you should use as it returns None if the URL does not exist
        r"""Link to the replay.

        :return: Link to download the replay on the osu! website
        :rtype: Optional[str]
        """
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}/download"
            if self.best_id and self.replay
            else None
        )

    @root_validator
    def _check_completion(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("beatmap"):
            return values
        completion = calculate_score_completion(
            values["mode"],
            values["statistics"],
            values["beatmap"],
        )
        if completion != 100:
            values["passed"] = False
            values["perfect"] = False
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
        data: Any,
        mode: Gamemode,
    ) -> Score:
        statistics = ScoreStatistics._from_api_v1(data)
        score = cls.parse_obj(
            {
                "id": data["score_id"],
                "user_id": data["user_id"],
                "accuracy": 0.0,
                "mods": int(data["enabled_mods"]),
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
