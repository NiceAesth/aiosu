"""
This module contains models for Score objects.
"""
from __future__ import annotations

import datetime
from typing import Optional
from typing import TYPE_CHECKING

from ..utils.accuracy import CatchAccuracyCalculator
from ..utils.accuracy import ManiaAccuracyCalculator
from ..utils.accuracy import OsuAccuracyCalculator
from ..utils.accuracy import TaikoAccuracyCalculator
from .beatmap import Beatmap
from .beatmap import Beatmapset
from .gamemode import Gamemode
from .models import BaseModel
from .mods import Mods
from .user import User

if TYPE_CHECKING:
    from typing import Any
    from .. import v1

accuracy_calculators = {
    "osu": OsuAccuracyCalculator(),
    "mania": ManiaAccuracyCalculator(),
    "taiko": TaikoAccuracyCalculator(),
    "fruits": CatchAccuracyCalculator(),
}


class ScoreWeight(BaseModel):
    percentage: float
    pp: float


class ScoreStatistics(BaseModel):
    count_50: int
    count_100: int
    count_300: int
    count_geki: int
    count_katu: int
    count_miss: int

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
    created_at: datetime.datetime
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
    beatmap_id: Optional[int] = None
    """Only present on API v1"""

    @property
    def completion(self) -> float:  # Should probably move to utils
        """Beatmap completion.

        :raises ValueError: If beatmap is None
        :raises ValueError: If mode is unknown
        :return: Beatmap completion of a score (%). 100% for passes
        :rtype: float
        """
        if not self.beatmap:
            raise ValueError("Beatmap object is not set.")

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
        raise ValueError("Unknown mode specified.")

    @property
    def score_url(self) -> Optional[str]:
        # score.id has undefined behaviour, best_id is the one you should use as it returns None if the URL does not exist
        """Link to the score.

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
        """Link to the replay.

        :return: Link to download the replay on the osu! website
        :rtype: Optional[str]
        """
        return (
            f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}/download"
            if self.best_id
            else None
        )

    async def request_beatmap(self, client: v1.Client) -> None:
        """For v1 Scores: requests the beatmap from the API and sets it.

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
            self.beatmap = sets[0].beatmaps[0]

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
