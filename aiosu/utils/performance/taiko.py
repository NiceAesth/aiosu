from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...models.gamemode import Gamemode
from ...models.performance import TaikoPerformanceAttributes
from . import _difficulty as diff_utils
from ._base import AbstractPerformanceCalculator
from ._base import _calculate_rate_with_mods
from ._base import _difficulty_with_mods
from ._base import _has_mod
from ._base import _require_number

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.score import Score


class TaikoPerformanceCalculator(AbstractPerformanceCalculator):
    def calculate(self, score: Score) -> TaikoPerformanceAttributes:
        self._validate_score(score)
        return self._create_performance_attributes(score, self.difficulty_attributes)

    def _create_performance_attributes(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> TaikoPerformanceAttributes:
        self.count_great = score.statistics.great
        self.count_ok = score.statistics.ok
        self.count_meh = score.statistics.meh
        self.count_miss = max(0, score.statistics.miss)
        self.clock_rate = _calculate_rate_with_mods(score)
        difficulty = _difficulty_with_mods(score)
        self.great_hit_window = (
            math.floor(50 - 3 * difficulty.overall_difficulty) - 0.5
        ) / self.clock_rate
        self.estimated_unstable_rate = None
        if self.count_great != 0 and self.great_hit_window > 0:
            self.estimated_unstable_rate = (
                self._compute_deviation_upper_bound(self.count_great / self.total_hits)
                * 10
            )

        consistency_factor = _require_number(
            attributes.consistency_factor,
            "consistency_factor",
        )
        self.total_difficult_hits = self.total_hits * consistency_factor
        assert score.beatmap is not None
        is_convert = score.beatmap.mode != Gamemode.TAIKO
        is_classic = _has_mod(score, "CL")
        difficulty_value = (
            self._compute_difficulty_value(score, attributes, is_convert, is_classic)
            * 1.08
        )
        accuracy_value = (
            self._compute_accuracy_value(score, attributes, is_convert) * 1.1
        )
        return TaikoPerformanceAttributes(
            difficulty=difficulty_value,
            accuracy=accuracy_value,
            estimated_unstable_rate=self.estimated_unstable_rate,
            total=difficulty_value + accuracy_value,
        )

    def _compute_difficulty_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
        is_convert: bool,
        is_classic: bool,
    ) -> float:
        if self.estimated_unstable_rate is None or self.total_difficult_hits == 0:
            return 0.0
        if attributes.star_rating <= 0:
            return 0.0

        rhythm_expected_unstable_rate = self._compute_deviation_upper_bound(1.0) * 10
        rhythm_maximum_unstable_rate = self._compute_deviation_upper_bound(0.8) * 10
        rhythm_difficulty = _require_number(
            attributes.rhythm_difficulty,
            "rhythm_difficulty",
        )
        mono_stamina_factor = _require_number(
            attributes.mono_stamina_factor,
            "mono_stamina_factor",
        )
        rhythm_factor = diff_utils.reverse_lerp(
            rhythm_difficulty / attributes.star_rating,
            0.15,
            0.4,
        )
        rhythm_penalty = 1 - diff_utils.logistic(
            self.estimated_unstable_rate,
            midpoint_offset=(
                rhythm_expected_unstable_rate + rhythm_maximum_unstable_rate
            )
            / 2,
            multiplier=10
            / (rhythm_maximum_unstable_rate - rhythm_expected_unstable_rate),
            max_value=0.25 * math.pow(rhythm_factor, 3),
        )
        base_difficulty = (
            5 * max(1.0, attributes.star_rating * rhythm_penalty / 0.110) - 4.0
        )
        difficulty_value = min(
            math.pow(base_difficulty, 3) / 69052.51,
            math.pow(base_difficulty, 2.25) / 1250.0,
        )
        difficulty_value *= 1 + 0.10 * max(0.0, attributes.star_rating - 10)
        length_bonus = 1 + 0.25 * self.total_difficult_hits / (
            self.total_difficult_hits + 4000
        )
        difficulty_value *= length_bonus
        miss_penalty = 0.97 + 0.03 * self.total_difficult_hits / (
            self.total_difficult_hits + 1500
        )
        difficulty_value *= math.pow(miss_penalty, self.count_miss)

        if _has_mod(score, "HD"):
            hidden_bonus = 0.025 if is_convert else 0.1
            if not _has_mod(score, "FL"):
                if not is_classic:
                    hidden_bonus *= 0.2
                if _has_mod(score, "EZ") and is_classic:
                    hidden_bonus *= 0.5
            difficulty_value *= 1 + hidden_bonus
        if _has_mod(score, "FL"):
            difficulty_value *= max(
                1.0,
                1.050 - min(mono_stamina_factor / 50, 1) * length_bonus,
            )

        mono_acc_scaling_exponent = 2 + mono_stamina_factor
        mono_acc_scaling_shift = 500 - 100 * (mono_stamina_factor * 3)
        return difficulty_value * math.pow(
            diff_utils.erf(
                mono_acc_scaling_shift
                / (diff_utils.SQRT2 * self.estimated_unstable_rate),
            ),
            mono_acc_scaling_exponent,
        )

    def _compute_accuracy_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
        is_convert: bool,
    ) -> float:
        if self.great_hit_window <= 0 or self.estimated_unstable_rate is None:
            return 0.0

        accuracy_value = 470 * math.pow(0.9885, self.estimated_unstable_rate)
        accuracy_value *= (
            1
            + math.pow(50 / self.estimated_unstable_rate, 2)
            * math.pow(attributes.star_rating, 2.8)
            / 600
        )
        if _has_mod(score, "HD") and not is_convert:
            accuracy_value *= 1.075
        accuracy_value *= 1 + 0.3 * self.total_difficult_hits / (
            self.total_difficult_hits + 4000
        )
        memory_length_bonus = min(1.15, math.pow(self.total_hits / 1500.0, 0.3))
        if _has_mod(score, "FL") and _has_mod(score, "HD") and not is_convert:
            accuracy_value *= max(1.0, 1.05 * memory_length_bonus)
        return accuracy_value

    def _compute_deviation_upper_bound(self, accuracy: float) -> float:
        z = 2.32634787404
        n = self.total_hits
        p = accuracy
        p_lower_bound = (n * p + z * z / 2) / (n + z * z) - z / (n + z * z) * math.sqrt(
            n * p * (1 - p) + z * z / 4,
        )
        return self.great_hit_window / (
            diff_utils.SQRT2 * diff_utils.erf_inv(p_lower_bound)
        )

    @property
    def total_hits(self) -> int:
        return self.count_great + self.count_ok + self.count_meh + self.count_miss

    @property
    def total_successful_hits(self) -> int:
        return self.count_great + self.count_ok + self.count_meh
