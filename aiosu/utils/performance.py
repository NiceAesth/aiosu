"""
This module contains performance point calculators for osu! gamemodes.
"""

from __future__ import annotations

import abc
import math
from typing import TYPE_CHECKING
from typing import Callable

from ..models import CatchPerformanceAttributes
from ..models import Gamemode
from ..models import ManiaPerformanceAttributes
from ..models import Mod
from ..models import OsuPerformanceAttributes
from ..models import TaikoPerformanceAttributes
from .accuracy import CatchAccuracyCalculator
from .accuracy import ManiaAccuracyCalculator
from .accuracy import OsuAccuracyCalculator
from .accuracy import TaikoAccuracyCalculator

if TYPE_CHECKING:
    from ..models.beatmap import BeatmapDifficultyAttributes
    from ..models.performance import PerformanceAttributes
    from ..models.score import Score


__all__ = [
    "CatchPerformanceCalculator",
    "ManiaPerformanceCalculator",
    "OsuPerformanceCalculator",
    "TaikoPerformanceCalculator",
]

OSU_BASE_MULTIPLIER = 1.15
TAIKO_BASE_MULTIPLIER = 1.13

clamp: Callable[[float, float, float], float] = lambda x, l, u: (
    l if x < l else u if x > u else x
)


class AbstractPerformanceCalculator(abc.ABC):
    __slots__ = ("difficulty_attributes",)

    def __init__(self, difficulty_attributes: BeatmapDifficultyAttributes):
        self.difficulty_attributes = difficulty_attributes

    @abc.abstractmethod
    def calculate(self, score: Score) -> PerformanceAttributes: ...


def get_calculator(mode: Gamemode) -> type[AbstractPerformanceCalculator]:
    r"""Returns the performance calculator for the given gamemode.

    :param mode: The gamemode to get the calculator for
    :type mode: aiosu.models.gamemode.Gamemode
    :raises ValueError: If the gamemode is unknown
    :return: The performance calculator type for the given gamemode
    :rtype: Type[AbstractPerformanceCalculator]
    """
    if mode == Gamemode.STANDARD:
        return OsuPerformanceCalculator
    elif mode == Gamemode.TAIKO:
        return TaikoPerformanceCalculator
    elif mode == Gamemode.MANIA:
        return ManiaPerformanceCalculator
    elif mode == Gamemode.CTB:
        return CatchPerformanceCalculator
    else:
        raise ValueError(f"Unknown gamemode: {mode}")


class OsuPerformanceCalculator(AbstractPerformanceCalculator):
    r"""osu!std performance point calculator. Only compatible with scores from API v2.

    :param difficulty_attributes: API difficulty attributes for a beatmap
    :type difficulty_attributes: BeatmapDifficultyAttributes
    """

    def _is_slider_head_accuracy(self, score: Score) -> bool:
        return True

    def calculate(self, score: Score) -> OsuPerformanceAttributes:
        r"""Calculates performance points for a score.

        :param score: The score to calculate pp for
        :type score: aiosu.models.score.Score
        :raises ValueError: If score does not have an associated beatmap
        :return: Performance attributes for the score
        :rtype: aiosu.models.performance.OsuPerformanceAttributes
        """
        if score.beatmap is None:
            raise ValueError("Given score does not have a beatmap.")

        total_hits = (
            score.statistics.count_300
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )
        effective_miss_count = float(score.statistics.count_miss)

        assert score.beatmap.count_spinners is not None
        assert score.beatmap.count_sliders is not None

        if score.beatmap.count_sliders > 0:
            if self._is_slider_head_accuracy(score):
                full_combo_threshold = (
                    self.difficulty_attributes.max_combo
                    - 0.1 * score.beatmap.count_sliders
                )

                if score.max_combo < full_combo_threshold:
                    effective_miss_count = full_combo_threshold / max(
                        1,
                        score.max_combo,
                    )

                effective_miss_count = min(
                    effective_miss_count,
                    score.statistics.count_100
                    + score.statistics.count_100
                    + score.statistics.count_miss,
                )
            else:
                assert score.statistics.count_slider_tail_hit is not None
                assert score.statistics.count_large_tick_miss is not None

                full_combo_threshold = self.difficulty_attributes.max_combo - (
                    score.beatmap.count_sliders - score.statistics.count_slider_tail_hit
                )

                if score.max_combo < full_combo_threshold:
                    effective_miss_count = full_combo_threshold / max(
                        1,
                        score.max_combo,
                    )

                effective_miss_count = min(
                    effective_miss_count,
                    score.statistics.count_large_tick_miss
                    + score.statistics.count_miss,
                )

        effective_miss_count = clamp(
            effective_miss_count,
            score.statistics.count_miss,
            total_hits,
        )

        multiplier = OSU_BASE_MULTIPLIER

        if Mod.NoFail in score.mods:
            multiplier *= max(0.9, 1.0 - 0.02 * effective_miss_count)

        if Mod.SpunOut in score.mods and total_hits > 0:
            multiplier *= 1.0 - math.pow(
                (score.beatmap.count_spinners / total_hits),
                0.85,
            )

        if Mod.Relax in score.mods:
            assert self.difficulty_attributes.overall_difficulty is not None

            adjusted_od = self.difficulty_attributes.overall_difficulty / 13.33
            ok_multiplier = max(
                0,
                (
                    (1 - pow(adjusted_od, 1.8))
                    if self.difficulty_attributes.overall_difficulty > 0
                    else 1
                ),
            )
            meh_multiplier = max(
                0,
                (
                    (1 - pow(adjusted_od, 5))
                    if self.difficulty_attributes.overall_difficulty > 0
                    else 1
                ),
            )

            effective_miss_count = min(
                effective_miss_count
                + score.statistics.count_100 * ok_multiplier
                + score.statistics.count_50 * meh_multiplier,
                total_hits,
            )

        aim_value = self._compute_aim_value(score, effective_miss_count, total_hits)
        speed_value = self._compute_speed_value(score, effective_miss_count, total_hits)
        accuracy_value = self._compute_accuracy_value(score, total_hits)
        flashlight_value = self._compute_flashlight_value(
            score,
            effective_miss_count,
            total_hits,
        )

        total_value = (
            math.pow(
                math.pow(aim_value, 1.1)
                + math.pow(speed_value, 1.1)
                + math.pow(accuracy_value, 1.1)
                + math.pow(flashlight_value, 1.1),
                1.0 / 1.1,
            )
            * multiplier
        )

        return OsuPerformanceAttributes(
            total=total_value,
            aim=aim_value,
            speed=speed_value,
            accuracy=accuracy_value,
            flashlight=flashlight_value,
            effective_miss_count=effective_miss_count,
        )

    def _compute_aim_value(
        self,
        score: Score,
        effective_miss_count: float,
        total_hits: int,
    ) -> float:
        assert self.difficulty_attributes.aim_difficulty is not None

        aim_value = (
            math.pow(
                5.0 * max(1.0, self.difficulty_attributes.aim_difficulty / 0.0675)
                - 4.0,
                3.0,
            )
            / 100000.0
        )

        length_bonus = (
            0.95
            + 0.4 * min(1.0, total_hits / 2000.0)
            + ((math.log10(total_hits / 2000.0) * 0.5) * int(total_hits > 2000))
        )
        aim_value *= length_bonus

        if effective_miss_count > 0:
            assert self.difficulty_attributes.aim_difficult_strain_count is not None

            aim_value *= self._calculate_miss_penalty(
                effective_miss_count,
                self.difficulty_attributes.aim_difficult_strain_count,
            )

        assert self.difficulty_attributes.approach_rate is not None
        assert score.beatmap is not None
        assert score.beatmap.count_sliders is not None

        approach_rate_factor = 0.0

        if self.difficulty_attributes.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (
                self.difficulty_attributes.approach_rate - 10.33
            )
        elif self.difficulty_attributes.approach_rate < 8.0:
            approach_rate_factor = 0.05 * (
                8.0 - self.difficulty_attributes.approach_rate
            )

        aim_value *= 1.0 + approach_rate_factor * length_bonus

        if Mod.Hidden in score.mods:
            aim_value *= 1.0 + 0.04 * (12.0 - self.difficulty_attributes.approach_rate)

        estimate_difficult_sliders: float = score.beatmap.count_sliders * 0.15

        if score.beatmap.count_sliders > 0:
            estimate_improperly_followed_difficult_sliders = 0.0

            if self._is_slider_head_accuracy(score):
                maximum_possible_dropped_sliders = (
                    score.statistics.count_100
                    + score.statistics.count_50
                    + score.statistics.count_miss
                )
                estimate_improperly_followed_difficult_sliders = clamp(
                    float(
                        min(
                            maximum_possible_dropped_sliders,
                            self.difficulty_attributes.max_combo - score.max_combo,
                        ),
                    ),
                    0.0,
                    estimate_difficult_sliders,
                )
            else:
                assert score.statistics.count_slider_tail_hit is not None
                assert score.statistics.count_large_tick_miss is not None

                estimate_improperly_followed_difficult_sliders = clamp(
                    score.beatmap.count_sliders
                    - score.statistics.count_slider_tail_hit
                    + score.statistics.count_large_tick_miss,
                    0,
                    estimate_difficult_sliders,
                )

            assert self.difficulty_attributes.slider_factor is not None

            slider_nerf_factor = (1 - self.difficulty_attributes.slider_factor) * pow(
                1
                - estimate_improperly_followed_difficult_sliders
                / estimate_difficult_sliders,
                3,
            ) + self.difficulty_attributes.slider_factor
            aim_value *= slider_nerf_factor

        accuracy = score.accuracy
        aim_value *= accuracy

        assert self.difficulty_attributes.overall_difficulty is not None

        aim_value *= (
            0.98 + math.pow(self.difficulty_attributes.overall_difficulty, 2) / 2500
        )

        return aim_value

    def _compute_speed_value(
        self,
        score: Score,
        effective_miss_count: float,
        total_hits: int,
    ) -> float:
        if Mod.Relax in score.mods:
            return 0

        assert self.difficulty_attributes.speed_difficulty is not None
        assert self.difficulty_attributes.approach_rate is not None
        assert self.difficulty_attributes.speed_note_count is not None
        assert self.difficulty_attributes.overall_difficulty is not None

        speed_value = (
            math.pow(
                5.0 * max(1.0, self.difficulty_attributes.speed_difficulty / 0.0675)
                - 4.0,
                3.0,
            )
            / 100000.0
        )

        length_bonus = (
            0.95
            + 0.4 * min(1.0, total_hits / 2000.0)
            + (
                ((math.log10(total_hits / 2000.0) * 0.5) * int(total_hits > 2000))
                if total_hits > 0
                else 0
            )
        )
        speed_value *= length_bonus

        if effective_miss_count > 0:
            assert self.difficulty_attributes.speed_difficult_strain_count is not None

            speed_value *= self._calculate_miss_penalty(
                effective_miss_count,
                self.difficulty_attributes.speed_difficult_strain_count,
            )

        approach_rate_factor = 0.0

        if self.difficulty_attributes.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (
                self.difficulty_attributes.approach_rate - 10.33
            )

        speed_value *= 1.0 + approach_rate_factor * length_bonus

        # if Mod.Blinds in score.mods:
        #     speed_value *= 1.12

        if Mod.Hidden in score.mods:

            speed_value *= 1.0 + 0.04 * (
                12.0 - self.difficulty_attributes.approach_rate
            )

        relevant_total_diff = total_hits - self.difficulty_attributes.speed_note_count
        relevant_count_great = max(0, score.statistics.count_300 - relevant_total_diff)
        relevant_count_ok = max(
            0,
            score.statistics.count_100
            - max(0, relevant_total_diff - score.statistics.count_300),
        )
        relevant_count_meh = max(
            0,
            score.statistics.count_50
            - max(
                0,
                relevant_total_diff
                - score.statistics.count_300
                - score.statistics.count_100,
            ),
        )

        relevant_accuracy = 0.0
        if self.difficulty_attributes.speed_note_count > 0:
            relevant_accuracy = (
                relevant_count_great * 6.0
                + relevant_count_ok * 2.0
                + relevant_count_meh
            ) / (self.difficulty_attributes.speed_note_count * 6.0)

        accuracy = score.accuracy if score.accuracy <= 1.0 else score.accuracy / 100

        speed_value *= (
            0.95 + math.pow(self.difficulty_attributes.overall_difficulty, 2) / 750
        ) * math.pow(
            (accuracy + relevant_accuracy) / 2.0,
            (14.5 - max(self.difficulty_attributes.overall_difficulty, 8)) / 2,
        )

        speed_value *= math.pow(
            0.99,
            (
                0
                if score.statistics.count_50 < total_hits / 500
                else score.statistics.count_50 - total_hits / 500
            ),
        )

        return speed_value

    def _compute_accuracy_value(
        self,
        score: Score,
        total_hits: int,
    ) -> float:
        if Mod.Relax in score.mods:
            return 0

        accuracy_calculator = OsuAccuracyCalculator()
        better_accuracy_percentage = accuracy_calculator.calculate_weighted(score)

        assert self.difficulty_attributes.overall_difficulty is not None
        assert score.beatmap is not None
        assert score.beatmap.count_circles is not None

        accuracy_value = (
            math.pow(1.52163, self.difficulty_attributes.overall_difficulty)
            * math.pow(better_accuracy_percentage, 24)
            * 2.83
        )

        accuracy_value *= min(
            1.15,
            math.pow(score.beatmap.count_circles / 1000.0, 0.3),
        )

        # if Mod.Blinds in score.mods:
        #     accuracy_value *= 1.14

        # if Mod.Traceable in score.mods:
        #     accuracy_value *= 1.08

        if Mod.Hidden in score.mods:
            accuracy_value *= 1.08

        if Mod.Flashlight in score.mods:
            accuracy_value *= 1.02

        return accuracy_value

    def _compute_flashlight_value(
        self,
        score: Score,
        effective_miss_count: float,
        total_hits: int,
    ) -> float:
        if Mod.Flashlight not in score.mods:
            return 0.0

        assert self.difficulty_attributes.flashlight_difficulty is not None
        assert self.difficulty_attributes.overall_difficulty is not None

        flashlight_value = (
            math.pow(self.difficulty_attributes.flashlight_difficulty, 2.0) * 25.0
        )

        if effective_miss_count > 0:
            flashlight_value *= 0.97 * math.pow(
                1 - math.pow(effective_miss_count / total_hits, 0.775),
                math.pow(effective_miss_count, 0.875),
            )

        flashlight_value *= self._get_combo_scaling_factor(score)

        flashlight_value *= (
            0.7
            + 0.1 * min(1.0, total_hits / 200.0)
            + 0.2 * (min(1.0, (total_hits - 200) / 200.0) * int(total_hits > 200))
        )

        accuracy = score.accuracy if score.accuracy <= 1.0 else score.accuracy / 100
        flashlight_value *= 0.5 + accuracy / 2.0
        flashlight_value *= (
            0.98 + math.pow(self.difficulty_attributes.overall_difficulty, 2) / 2500.0
        )

        return flashlight_value

    def _get_combo_scaling_factor(self, score: Score) -> float:
        if self.difficulty_attributes.max_combo <= 0:
            return 1.0

        return min(
            math.pow(score.max_combo, 0.8)
            / math.pow(self.difficulty_attributes.max_combo, 0.8),
            1.0,
        )

    def _calculate_miss_penalty(
        self,
        effective_miss_count: float,
        difficult_strain_count: float,
    ) -> float:
        return 0.96 / (
            (effective_miss_count / (4 * pow(math.log(difficult_strain_count), 0.94)))
            + 1
        )


class TaikoPerformanceCalculator(AbstractPerformanceCalculator):
    r"""osu!taiko performance point calculator.

    :param difficulty_attributes: API difficulty attributes for a beatmap
    :type difficulty_attributes: BeatmapDifficultyAttributes
    """

    def calculate(self, score: Score) -> TaikoPerformanceAttributes:
        r"""Calculates performance points for a score

        :param score: The score to calculate pp for
        :type score: aiosu.models.score.Score
        :return: Performance attributes for the score
        :rtype: aiosu.models.performance.TaikoPerformanceAttributes
        """
        accuracy_calculator = TaikoAccuracyCalculator()
        accuracy = accuracy_calculator.calculate_weighted(score)

        effective_miss_count = self._calculate_effective_miss_count(score)
        total_hits = (
            score.statistics.count_300
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )

        multiplier = TAIKO_BASE_MULTIPLIER

        if Mod.Hidden in score.mods:
            multiplier *= 1.075

        if Mod.Easy in score.mods:
            multiplier *= 0.975

        difficulty_value = self._compute_difficulty_value(
            score,
            total_hits,
            effective_miss_count,
            accuracy,
        )
        accuracy_value = self._compute_accuracy_value(
            score,
            total_hits,
            accuracy,
        )
        total_value = (
            math.pow(
                math.pow(difficulty_value, 1.1) + math.pow(accuracy_value, 1.1),
                1.0 / 1.1,
            )
            * multiplier
        )

        return TaikoPerformanceAttributes(
            total=total_value,
            difficulty=difficulty_value,
            accuracy=accuracy_value,
            effective_miss_count=effective_miss_count,
        )

    def _compute_difficulty_value(
        self,
        score: Score,
        total_hits: int,
        effective_miss_count: float,
        accuracy: float,
    ) -> float:
        difficulty_value = (
            math.pow(
                5 * max(1.0, self.difficulty_attributes.star_rating / 0.115) - 4.0,
                2.25,
            )
            / 1150.0
        )

        length_bonus = 1 + 0.1 * min(1.0, total_hits / 1500.0)
        difficulty_value *= length_bonus

        difficulty_value *= math.pow(0.986, effective_miss_count)

        if Mod.Easy in score.mods:
            difficulty_value *= 0.985

        if Mod.Hidden in score.mods:
            difficulty_value *= 1.025

        if Mod.HardRock in score.mods:
            difficulty_value *= 1.050

        if Mod.Flashlight in score.mods:
            difficulty_value *= 1.050 * length_bonus

        difficulty_value *= math.pow(accuracy, 2.0)
        return difficulty_value

    def _compute_accuracy_value(
        self,
        score: Score,
        total_hits: int,
        accuracy: float,
    ) -> float:
        assert self.difficulty_attributes.great_hit_window is not None

        if self.difficulty_attributes.great_hit_window <= 0:
            return 0.0

        accuracy_value = (
            math.pow(60.0 / self.difficulty_attributes.great_hit_window, 1.1)
            * math.pow(accuracy, 8.0)
            * math.pow(self.difficulty_attributes.star_rating, 0.4)
            * 27.0
        )

        length_bonus = min(1.15, math.pow(total_hits / 1500.0, 0.3))
        accuracy_value *= length_bonus

        if Mod.Hidden in score.mods and Mod.Flashlight in score.mods:
            accuracy_value *= max(1.050, 1.075 * length_bonus)

        return accuracy_value

    def _calculate_effective_miss_count(self, score: Score) -> float:
        return (
            max(
                1.0,
                1000.0
                / (
                    score.statistics.count_300
                    + score.statistics.count_100
                    + score.statistics.count_50
                ),
            )
            * score.statistics.count_miss
        )


class ManiaPerformanceCalculator(AbstractPerformanceCalculator):
    r"""osu!mania performance point calculator.

    :param difficulty_attributes: API difficulty attributes for a beatmap
    :type difficulty_attributes: BeatmapDifficultyAttributes
    """

    def calculate(self, score: Score) -> ManiaPerformanceAttributes:
        r"""Calculates performance points for a score.

        :param score: The score to calculate pp for
        :type score: aiosu.models.score.Score
        :return: Performance attributes for the score
        :rtype: aiosu.models.performance.ManiaPerformanceAttributes
        """
        accuracy_calculator = ManiaAccuracyCalculator()
        accuracy = accuracy_calculator.calculate_weighted(score)

        total_hits = (
            score.statistics.count_geki
            + score.statistics.count_300
            + score.statistics.count_katu
            + score.statistics.count_100
            + score.statistics.count_50
            + score.statistics.count_miss
        )

        multiplier = 1.0

        if Mod.NoFail in score.mods:
            multiplier *= 0.75

        if Mod.Easy in score.mods:
            multiplier *= 0.5

        difficulty_value = self._compute_difficulty_value(accuracy, total_hits)
        total_value = difficulty_value * multiplier

        return ManiaPerformanceAttributes(
            total=total_value,
            difficulty=difficulty_value,
        )

    def _compute_difficulty_value(self, accuracy: float, total_hits: int) -> float:
        difficulty_value = (
            8
            * math.pow(max(self.difficulty_attributes.star_rating - 0.15, 0.05), 2.2)
            * max(0.0, 5.0 * accuracy - 4.0)
            * (1.0 + 0.1 * min(1.0, total_hits / 1500))
        )

        return difficulty_value


class CatchPerformanceCalculator(AbstractPerformanceCalculator):
    r"""osu!catch performance point calculator.

    :param difficulty_attributes: API difficulty attributes for a beatmap
    :type difficulty_attributes: BeatmapDifficultyAttributes
    """

    def calculate(self, score: Score) -> CatchPerformanceAttributes:
        r"""Calculates performance points for a score.

        :param score: The score to calculate pp for
        :type score: aiosu.models.score.Score
        :return: Performance attributes for the score
        :rtype: aiosu.models.performance.CatchPerformanceAttributes
        """
        accuracy_calculator = CatchAccuracyCalculator()
        accuracy = accuracy_calculator.calculate_weighted(score)

        total_combo_hits = (
            score.statistics.count_miss
            + score.statistics.count_100
            + score.statistics.count_300
        )

        total_value = (
            math.pow(
                5.0 * max(1.0, self.difficulty_attributes.star_rating / 0.0049) - 4.0,
                2.0,
            )
            / 100000.0
        )

        length_bonus = (
            0.95
            + 0.3 * min(1.0, total_combo_hits / 2500.0)
            + (
                (math.log10(total_combo_hits / 2500.0) * 0.475)
                * int(total_combo_hits > 2500)
            )
        )
        total_value *= length_bonus

        total_value *= math.pow(0.97, score.statistics.count_miss)

        if self.difficulty_attributes.max_combo > 0:
            total_value *= min(
                math.pow(score.max_combo, 0.8)
                / math.pow(self.difficulty_attributes.max_combo, 0.8),
                1.0,
            )

        approach_rate_factor = 1.0
        assert self.difficulty_attributes.approach_rate is not None

        if self.difficulty_attributes.approach_rate > 9.0:
            approach_rate_factor += 0.1 * (
                self.difficulty_attributes.approach_rate - 9.0
            )

        if self.difficulty_attributes.approach_rate > 10.0:
            approach_rate_factor += 0.1 * (
                self.difficulty_attributes.approach_rate - 10.0
            )
        elif self.difficulty_attributes.approach_rate < 8.0:
            approach_rate_factor += 0.025 * (
                8.0 - self.difficulty_attributes.approach_rate
            )

        total_value *= approach_rate_factor

        if Mod.Hidden in score.mods:
            if self.difficulty_attributes.approach_rate <= 10.0:
                total_value *= 1.05 + 0.075 * (
                    10.0 - self.difficulty_attributes.approach_rate
                )
            elif self.difficulty_attributes.approach_rate > 10.0:
                total_value *= 1.01 + 0.04 * (
                    11.0 - min(11.0, self.difficulty_attributes.approach_rate)
                )

        if Mod.Flashlight in score.mods:
            total_value *= 1.35 * length_bonus

        total_value *= math.pow(accuracy, 5.5)

        if Mod.NoFail in score.mods:
            total_value *= max(0.90, 1 - 0.02 * score.statistics.count_miss)

        return CatchPerformanceAttributes(total=total_value)
