"""
This module contains accuracy calculators for osu! gamemodes.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from ..models.base import cast_int
from ..models.gamemode import Gamemode
from ..models.mods import Mod

if TYPE_CHECKING:
    from ..models.score import Score

__all__ = [
    "CatchAccuracyCalculator",
    "ManiaAccuracyCalculator",
    "OsuAccuracyCalculator",
    "TaikoAccuracyCalculator",
]


def get_calculator(mode: Gamemode) -> type[AbstractAccuracyCalculator]:
    r"""Returns the accuracy calculator for the given gamemode.

    :param mode: The gamemode to get the calculator for
    :type mode: aiosu.models.gamemode.Gamemode
    :raises ValueError: If the gamemode is unknown
    :return: The accuracy calculator type for the given gamemode
    :rtype: Type[AbstractAccuracyCalculator]
    """
    if mode == Gamemode.STANDARD:
        return OsuAccuracyCalculator
    elif mode == Gamemode.TAIKO:
        return TaikoAccuracyCalculator
    elif mode == Gamemode.MANIA:
        return ManiaAccuracyCalculator
    elif mode == Gamemode.CTB:
        return CatchAccuracyCalculator
    else:
        raise ValueError(f"Unknown gamemode: {mode}")


class AbstractAccuracyCalculator(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def calculate(score: Score) -> float: ...

    @staticmethod
    @abc.abstractmethod
    def calculate_weighted(score: Score) -> float: ...


class OsuAccuracyCalculator(AbstractAccuracyCalculator):
    @staticmethod
    def calculate(score: Score) -> float:
        r"""Calculates accuracy for an osu!std score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Accuracy for the given score
        :rtype: float
        """
        total_hits = (
            score.statistics.count_300
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )

        if total_hits <= 0:
            return 0.0

        return max(
            (
                score.statistics.count_300 * 6.0
                + score.statistics.count_100 * 2.0
                + score.statistics.count_50
            )
            / (total_hits * 6.0),
            0.0,
        )

    @staticmethod
    def calculate_weighted(score: Score) -> float:
        r"""Calculates weighted accuracy for an osu!std score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :raises ValueError: If score does not have an associated beatmap
        :return: Weighted accuracy to be used in pp calculation
        :rtype: float
        """
        if score.beatmap is None:
            raise ValueError("Given score does not have a beatmap.")

        total_hits = (
            score.statistics.count_300
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )

        amount_hit_objects_with_accuracy = cast_int(score.beatmap.count_circles)

        if Mod.ScoreV2 in score.mods:  # TODO: Check for lazer classic mod
            amount_hit_objects_with_accuracy += cast_int(score.beatmap.count_sliders)

        if amount_hit_objects_with_accuracy <= 0:
            return 0.0

        return max(
            (
                (
                    score.statistics.count_300
                    - (total_hits - amount_hit_objects_with_accuracy)
                )
                * 6.0
                + score.statistics.count_100 * 2.0
                + score.statistics.count_50
            )
            / (amount_hit_objects_with_accuracy * 6.0),
            0.0,
        )


class TaikoAccuracyCalculator(AbstractAccuracyCalculator):
    @staticmethod
    def calculate(score: Score) -> float:
        r"""Calculates accuracy for an osu!taiko score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Accuracy for the given score
        :rtype: float
        """
        total_hits = (
            score.statistics.count_300
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )

        if total_hits <= 0:
            return 0.0

        return max(
            (score.statistics.count_300 * 2.0 + score.statistics.count_100)
            / (total_hits * 2.0),
            0.0,
        )

    @classmethod
    def calculate_weighted(cls, score: Score) -> float:
        r"""Calculates weighted accuracy for an osu!taiko score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Weighted accuracy to be used in pp calculation
        :rtype: float
        """
        return cls.calculate(score)


class ManiaAccuracyCalculator(AbstractAccuracyCalculator):
    @staticmethod
    def calculate(score: Score) -> float:
        r"""Calculates accuracy for an osu!mania score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Accuracy for the given score
        :rtype: float
        """
        count_perfect = score.statistics.count_geki
        count_great = score.statistics.count_300
        count_good = score.statistics.count_katu
        count_ok = score.statistics.count_100
        count_meh = score.statistics.count_50
        count_miss = score.statistics.count_miss

        total_hits = (
            count_perfect + count_ok + count_great + count_good + count_meh + count_miss
        )

        if total_hits <= 0:
            return 0.0

        if Mod.ScoreV2 in score.mods:
            return max(
                (
                    +(count_perfect * 305)
                    + (count_great * 300)
                    + (count_good * 200)
                    + (count_ok * 100)
                    + (count_meh * 50)
                )
                / (total_hits * 305),
                0.0,
            )

        return max(
            (
                +((count_perfect + count_great) * 6.0)
                + (count_good * 4.0)
                + (count_ok * 2.0)
                + count_meh
            )
            / (total_hits * 6.0),
            0.0,
        )

    @staticmethod
    def calculate_weighted(score: Score) -> float:
        r"""Calculates weighted accuracy for an osu!mania score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Weighted accuracy to be used in pp calculation
        :rtype: float
        """
        count_perfect = score.statistics.count_geki
        count_great = score.statistics.count_300
        count_good = score.statistics.count_katu
        count_ok = score.statistics.count_100
        count_meh = score.statistics.count_50
        count_miss = score.statistics.count_miss

        total_hits = (
            count_perfect + count_ok + count_great + count_good + count_meh + count_miss
        )

        if total_hits <= 0:
            return 0.0

        return max(
            (
                +(count_perfect * 320)
                + (count_great * 300)
                + (count_good * 200)
                + (count_ok * 100)
                + (count_meh * 50)
            )
            / (total_hits * 320),
            0.0,
        )


class CatchAccuracyCalculator(AbstractAccuracyCalculator):
    @staticmethod
    def calculate(score: Score) -> float:
        r"""Calculates accuracy for an osu!catch score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Accuracy for the given score
        :rtype: float
        """
        fruits_hit = score.statistics.count_300
        ticks_hit = score.statistics.count_100
        tiny_ticks_hit = score.statistics.count_50
        tiny_ticks_missed = score.statistics.count_katu
        misses = score.statistics.count_miss

        total_hits = (
            tiny_ticks_hit + ticks_hit + fruits_hit + misses + tiny_ticks_missed
        )
        successful_hits = tiny_ticks_hit + ticks_hit + fruits_hit

        if total_hits <= 0:
            return 0.0

        return max(float(successful_hits) / total_hits, 0.0)

    @classmethod
    def calculate_weighted(cls, score: Score) -> float:
        r"""Calculates weighted accuracy for an osu!catch score.

        :param score: The score to calculate accuracy for
        :type score: aiosu.models.score.Score
        :return: Weighted accuracy to be used in pp calculation
        :rtype: float
        """
        return cls.calculate(score)
