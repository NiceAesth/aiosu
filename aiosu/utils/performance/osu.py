from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...models.performance import OsuPerformanceAttributes
from . import _difficulty as diff_utils
from ._base import AbstractPerformanceCalculator
from ._base import _calculate_rate_with_mods
from ._base import _difficulty_with_mods
from ._base import _get_mod
from ._base import _has_mod
from ._base import _require_number
from ._osu_legacy_score_miss import OsuLegacyScoreMissCalculator

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.score import Score


class OsuPerformanceCalculator(AbstractPerformanceCalculator):
    PERFORMANCE_BASE_MULTIPLIER = 1.12
    PERFORMANCE_NORM_EXPONENT = 1.1

    @staticmethod
    def difficulty_to_performance(difficulty: float) -> float:
        return 4.0 * math.pow(difficulty, 3)

    def calculate(self, score: Score) -> OsuPerformanceAttributes:
        self._validate_score(score)
        return self._create_performance_attributes(score, self.difficulty_attributes)

    def _create_performance_attributes(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> OsuPerformanceAttributes:
        if score.beatmap is None:
            raise ValueError("Given score does not have a beatmap.")

        classic = _get_mod(score, "CL")
        self.using_classic_slider_accuracy = (
            classic is not None
            and classic.settings.get("no_slider_head_accuracy", True) is True
        )
        self.using_score_v2 = _has_mod(score, "V2")
        self.accuracy = max(0.0, min(score.accuracy, 1.0))
        self.score_max_combo = max(0, min(score.max_combo, attributes.max_combo))
        self.count_great = score.statistics.great
        self.count_ok = score.statistics.ok
        self.count_meh = score.statistics.meh
        self.count_miss = score.statistics.miss
        self.hit_circle_count = int(
            _require_number(score.beatmap.count_circles, "beatmap.count_circles"),
        )
        self.slider_count = int(
            _require_number(score.beatmap.count_sliders, "beatmap.count_sliders"),
        )
        self.spinner_count = int(
            _require_number(score.beatmap.count_spinners, "beatmap.count_spinners"),
        )
        self.count_slider_ends_dropped = self.slider_count - (
            score.statistics.slider_tail_hit or 0
        )
        self.count_slider_tick_miss = score.statistics.large_tick_miss or 0
        self.effective_miss_count = float(self.count_miss)
        self.aim_estimated_slider_breaks = 0.0
        self.speed_estimated_slider_breaks = 0.0

        difficulty = _difficulty_with_mods(score)
        self.clock_rate = _calculate_rate_with_mods(score)
        self.great_hit_window = (
            math.floor(80 - 6 * difficulty.overall_difficulty) - 0.5
        ) / self.clock_rate
        self.ok_hit_window = (
            math.floor(140 - 8 * difficulty.overall_difficulty) - 0.5
        ) / self.clock_rate
        self.meh_hit_window = (
            math.floor(200 - 10 * difficulty.overall_difficulty) - 0.5
        ) / self.clock_rate
        self.approach_rate = self._calculate_rate_adjusted_approach_rate(
            difficulty.approach_rate,
            self.clock_rate,
        )
        self.overall_difficulty = (79.5 - self.great_hit_window) / 6
        self.drain_rate = difficulty.drain_rate

        combo_based_estimated_miss_count = (
            self._calculate_combo_based_estimated_miss_count(attributes)
        )
        score_based_estimated_miss_count = None
        if (
            self.using_classic_slider_accuracy
            and not self.using_score_v2
            and score.legacy_total_score is not None
            and score.legacy_total_score > 0
        ):
            legacy_score_miss_calculator = OsuLegacyScoreMissCalculator(
                score,
                attributes,
            )
            score_based_estimated_miss_count = legacy_score_miss_calculator.calculate()
            self.effective_miss_count = score_based_estimated_miss_count
        else:
            self.effective_miss_count = combo_based_estimated_miss_count
        self.effective_miss_count = max(self.count_miss, self.effective_miss_count)
        self.effective_miss_count = min(self.total_hits, self.effective_miss_count)
        self.effective_miss_count = max(0.0, self.effective_miss_count)
        if self.effective_miss_count > 0:
            aim_top_weighted_slider_factor = _require_number(
                attributes.aim_top_weighted_slider_factor,
                "aim_top_weighted_slider_factor",
            )
            speed_top_weighted_slider_factor = _require_number(
                attributes.speed_top_weighted_slider_factor,
                "speed_top_weighted_slider_factor",
            )
            self.aim_estimated_slider_breaks = self._calculate_estimated_slider_breaks(
                aim_top_weighted_slider_factor,
                attributes,
            )
            self.speed_estimated_slider_breaks = (
                self._calculate_estimated_slider_breaks(
                    speed_top_weighted_slider_factor,
                    attributes,
                )
            )

        multiplier = self.PERFORMANCE_BASE_MULTIPLIER
        if _has_mod(score, "NF"):
            multiplier *= max(0.90, 1.0 - 0.02 * self.effective_miss_count)
        if _has_mod(score, "SO") and self.total_hits > 0:
            multiplier *= 1.0 - math.pow(self.spinner_count / self.total_hits, 0.85)
        if _has_mod(score, "RX"):
            ok_multiplier = 0.75 * max(
                0.0,
                (
                    1 - self.overall_difficulty / 13.33
                    if self.overall_difficulty > 0.0
                    else 1.0
                ),
            )
            meh_multiplier = max(
                0.0,
                (
                    1 - math.pow(self.overall_difficulty / 13.33, 5)
                    if self.overall_difficulty > 0.0
                    else 1.0
                ),
            )
            self.effective_miss_count = min(
                self.effective_miss_count
                + self.count_ok * ok_multiplier
                + self.count_meh * meh_multiplier,
                self.total_hits,
            )

        self.speed_deviation = self._calculate_speed_deviation(attributes)
        aim_value = self._compute_aim_value(score, attributes)
        speed_value = self._compute_speed_value(score, attributes)
        accuracy_value = self._compute_accuracy_value(score, attributes)
        reading_value = self._compute_reading_value(attributes)
        flashlight_value = self._compute_flashlight_value(score, attributes)
        cognition_value = self._sum_cognition_difficulty(
            reading_value,
            flashlight_value,
        )
        total_value = (
            diff_utils.norm(
                self.PERFORMANCE_NORM_EXPONENT,
                aim_value,
                speed_value,
                accuracy_value,
                cognition_value,
            )
            * multiplier
        )
        return OsuPerformanceAttributes(
            aim=aim_value,
            speed=speed_value,
            accuracy=accuracy_value,
            flashlight=flashlight_value,
            reading=reading_value,
            effective_miss_count=self.effective_miss_count,
            combo_based_estimated_miss_count=combo_based_estimated_miss_count,
            score_based_estimated_miss_count=score_based_estimated_miss_count,
            aim_estimated_slider_breaks=self.aim_estimated_slider_breaks,
            speed_estimated_slider_breaks=self.speed_estimated_slider_breaks,
            speed_deviation=self.speed_deviation,
            total=total_value,
        )

    def _compute_aim_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if _has_mod(score, "AP"):
            return 0.0

        aim_difficulty = _require_number(attributes.aim_difficulty, "aim_difficulty")
        aim_difficult_slider_count = _require_number(
            attributes.aim_difficult_slider_count,
            "aim_difficult_slider_count",
        )
        slider_factor = _require_number(attributes.slider_factor, "slider_factor")
        if self.slider_count > 0 and aim_difficult_slider_count > 0:
            if self.using_classic_slider_accuracy:
                maximum_possible_dropped_sliders = self.total_imperfect_hits
                estimate_improperly_followed_difficult_sliders = max(
                    0.0,
                    min(
                        min(
                            maximum_possible_dropped_sliders,
                            attributes.max_combo - self.score_max_combo,
                        ),
                        aim_difficult_slider_count,
                    ),
                )
            else:
                estimate_improperly_followed_difficult_sliders = max(
                    0.0,
                    min(
                        self.count_slider_ends_dropped + self.count_slider_tick_miss,
                        aim_difficult_slider_count,
                    ),
                )
            slider_nerf_factor = (1 - slider_factor) * math.pow(
                1
                - estimate_improperly_followed_difficult_sliders
                / aim_difficult_slider_count,
                3,
            ) + slider_factor
            aim_difficulty *= slider_nerf_factor

        aim_value = self.difficulty_to_performance(aim_difficulty)
        length_bonus = 0.95 + 0.35 * min(1.0, self.total_hits / 2000.0)
        if self.total_hits > 2000:
            length_bonus += math.log10(self.total_hits / 2000.0) * 0.5
        aim_value *= length_bonus
        if self.effective_miss_count > 0:
            relevant_miss_count = min(
                self.effective_miss_count + self.aim_estimated_slider_breaks,
                self.total_imperfect_hits + self.count_slider_tick_miss,
            )
            aim_difficult_strain_count = _require_number(
                attributes.aim_difficult_strain_count,
                "aim_difficult_strain_count",
            )
            aim_value *= self._calculate_miss_penalty(
                relevant_miss_count,
                aim_difficult_strain_count,
            )

        if _has_mod(score, "BL"):
            aim_value *= 1.3 + (
                self.total_hits
                * (0.0016 / (1 + 2 * self.effective_miss_count))
                * math.pow(self.accuracy, 16)
            ) * (1 - 0.003 * self.drain_rate * self.drain_rate)
        elif _has_mod(score, "TC"):
            aim_value *= 1.0 + self._calculate_traceable_bonus(slider_factor)
        aim_value *= self.accuracy
        return aim_value

    def _compute_speed_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if _has_mod(score, "RX") or self.speed_deviation is None:
            return 0.0

        speed_difficulty = _require_number(
            attributes.speed_difficulty,
            "speed_difficulty",
        )
        if speed_difficulty <= 0:
            return 0.0
        speed_value = self.difficulty_to_performance(speed_difficulty)
        if self.effective_miss_count > 0:
            relevant_miss_count = min(
                self.effective_miss_count + self.speed_estimated_slider_breaks,
                self.total_imperfect_hits + self.count_slider_tick_miss,
            )
            speed_difficult_strain_count = _require_number(
                attributes.speed_difficult_strain_count,
                "speed_difficult_strain_count",
            )
            speed_value *= self._calculate_miss_penalty(
                relevant_miss_count,
                speed_difficult_strain_count,
            )
        if _has_mod(score, "BL"):
            speed_value *= 1.12

        speed_high_deviation_multiplier = self._calculate_speed_high_deviation_nerf(
            attributes,
        )
        speed_value *= speed_high_deviation_multiplier
        effective_hit_window = 20 * math.pow(4 / speed_difficulty, 0.35)
        effective_accuracy = diff_utils.erf(effective_hit_window / self.speed_deviation)
        speed_value *= math.pow(effective_accuracy, 2)
        return speed_value

    def _compute_accuracy_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if _has_mod(score, "RX"):
            return 0.0

        amount_hit_objects_with_accuracy = self.hit_circle_count
        if not self.using_classic_slider_accuracy or self.using_score_v2:
            amount_hit_objects_with_accuracy += self.slider_count
        if amount_hit_objects_with_accuracy > 0:
            better_accuracy_percentage = (
                (
                    self.count_great
                    - max(self.total_hits - amount_hit_objects_with_accuracy, 0)
                )
                * 6
                + self.count_ok * 2
                + self.count_meh
            ) / (amount_hit_objects_with_accuracy * 6)
        else:
            better_accuracy_percentage = 0.0
        better_accuracy_percentage = max(0.0, better_accuracy_percentage)

        accuracy_value = (
            math.pow(1.52163, self.overall_difficulty)
            * math.pow(better_accuracy_percentage, 24)
            * 2.83
        )
        if amount_hit_objects_with_accuracy < 1000:
            accuracy_value *= math.pow(amount_hit_objects_with_accuracy / 1000.0, 0.3)
        else:
            accuracy_value *= math.pow(amount_hit_objects_with_accuracy / 1000.0, 0.1)
        if _has_mod(score, "BL"):
            accuracy_value *= 1.14
        elif _has_mod(score, "TC"):
            accuracy_value *= 1 + 0.08 * diff_utils.reverse_lerp(
                self.approach_rate,
                11.5,
                10,
            )
        return accuracy_value

    def _compute_flashlight_value(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if not _has_mod(score, "FL"):
            return 0.0

        flashlight_difficulty = _require_number(
            attributes.flashlight_difficulty,
            "flashlight_difficulty",
        )
        flashlight_value = 25 * math.pow(flashlight_difficulty, 2)
        if self.effective_miss_count > 0:
            flashlight_value *= 0.97 * math.pow(
                1 - math.pow(self.effective_miss_count / self.total_hits, 0.775),
                math.pow(self.effective_miss_count, 0.875),
            )
        flashlight_value *= self._get_combo_scaling_factor(attributes)
        flashlight_value *= 0.5 + self.accuracy / 2.0
        return flashlight_value

    def _compute_reading_value(self, attributes: BeatmapDifficultyAttributes) -> float:
        reading_difficulty = _require_number(
            attributes.reading_difficulty,
            "reading_difficulty",
        )
        reading_value = self.difficulty_to_performance(reading_difficulty)
        if self.effective_miss_count > 0:
            reading_difficult_note_count = _require_number(
                attributes.reading_difficult_note_count,
                "reading_difficult_note_count",
            )
            reading_value *= self._calculate_miss_penalty(
                self.effective_miss_count + self.aim_estimated_slider_breaks,
                reading_difficult_note_count,
            )
        reading_value *= math.pow(self.accuracy, 3)
        return reading_value

    @classmethod
    def _sum_cognition_difficulty(cls, reading: float, flashlight: float) -> float:
        if reading <= 0:
            return flashlight
        if flashlight <= 0:
            return reading
        return diff_utils.norm(
            cls.PERFORMANCE_NORM_EXPONENT,
            reading,
            flashlight * max(0.25, min(flashlight / reading, 1.0)),
        )

    def _calculate_combo_based_estimated_miss_count(
        self,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if self.slider_count <= 0:
            return float(self.count_miss)

        miss_count = float(self.count_miss)
        if self.using_classic_slider_accuracy:
            aim_top_weighted_slider_factor = _require_number(
                attributes.aim_top_weighted_slider_factor,
                "aim_top_weighted_slider_factor",
            )
            likely_missed_sliderend_portion = 0.04 + 0.06 * math.pow(
                min(aim_top_weighted_slider_factor, 1),
                2,
            )
            full_combo_threshold = attributes.max_combo - min(
                4 + likely_missed_sliderend_portion * self.slider_count,
                self.slider_count,
            )
            if self.score_max_combo < full_combo_threshold:
                miss_count = full_combo_threshold / max(1.0, self.score_max_combo)
            miss_count = min(miss_count, self.total_imperfect_hits)
            max_possible_slider_breaks = min(
                self.slider_count,
                (attributes.max_combo - self.score_max_combo) // 2,
            )
            slider_breaks = miss_count - self.count_miss
            if slider_breaks > max_possible_slider_breaks:
                miss_count = self.count_miss + max_possible_slider_breaks
        else:
            full_combo_threshold = attributes.max_combo - self.count_slider_ends_dropped
            if self.score_max_combo < full_combo_threshold:
                miss_count = full_combo_threshold / max(1.0, self.score_max_combo)
            miss_count = min(miss_count, self.count_slider_tick_miss + self.count_miss)
        return miss_count

    def _calculate_estimated_slider_breaks(
        self,
        top_weighted_slider_factor: float,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        non_miss_mistakes = self.count_ok + self.count_meh
        if (
            not self.using_classic_slider_accuracy
            or non_miss_mistakes == 0
            or attributes.max_combo <= 0
        ):
            return 0.0

        missed_combo_percent = 1.0 - self.score_max_combo / attributes.max_combo
        estimated_slider_breaks = min(
            non_miss_mistakes,
            self.effective_miss_count * top_weighted_slider_factor,
        )
        non_miss_mistake_adjustment = (
            non_miss_mistakes - estimated_slider_breaks + 4.5
        ) / (non_miss_mistakes + 4)
        estimated_slider_breaks *= diff_utils.smoothstep(
            self.effective_miss_count,
            1,
            2,
        )
        return (
            estimated_slider_breaks
            * non_miss_mistake_adjustment
            * diff_utils.logistic(missed_combo_percent, 0.33, 15)
        )

    def _calculate_speed_deviation(
        self,
        attributes: BeatmapDifficultyAttributes,
    ) -> float | None:
        if self.total_successful_hits == 0:
            return None

        speed_note_count = _require_number(
            attributes.speed_note_count,
            "speed_note_count",
        )
        speed_note_count += (self.total_hits - speed_note_count) * 0.1
        relevant_count_miss = min(self.count_miss, speed_note_count)
        relevant_count_meh = min(self.count_meh, speed_note_count - relevant_count_miss)
        relevant_count_ok = min(
            self.count_ok,
            speed_note_count - relevant_count_miss - relevant_count_meh,
        )
        relevant_count_great = max(
            0.0,
            speed_note_count
            - relevant_count_miss
            - relevant_count_meh
            - relevant_count_ok,
        )
        return self._calculate_deviation(
            relevant_count_great,
            relevant_count_ok,
            relevant_count_meh,
        )

    def _calculate_deviation(
        self,
        relevant_count_great: float,
        relevant_count_ok: float,
        relevant_count_meh: float,
    ) -> float | None:
        if relevant_count_great + relevant_count_ok + relevant_count_meh <= 0:
            return None
        if self.great_hit_window <= 0 or self.ok_hit_window <= 0:
            raise ValueError("Hit windows must be positive.")

        n = max(1.0, relevant_count_great + relevant_count_ok)
        p = relevant_count_great / n
        z = 2.32634787404
        p_lower_bound = min(
            p,
            (n * p + z * z / 2) / (n + z * z)
            - z / (n + z * z) * math.sqrt(n * p * (1 - p) + z * z / 4),
        )
        if p_lower_bound > 0.01:
            deviation = self.great_hit_window / (
                diff_utils.SQRT2 * diff_utils.erf_inv(p_lower_bound)
            )
            ok_hit_window_tail_amount = (
                math.sqrt(2 / math.pi)
                * self.ok_hit_window
                * math.exp(-0.5 * math.pow(self.ok_hit_window / deviation, 2))
                / (
                    deviation
                    * diff_utils.erf(
                        self.ok_hit_window / (diff_utils.SQRT2 * deviation),
                    )
                )
            )
            deviation *= math.sqrt(1 - ok_hit_window_tail_amount)
        else:
            deviation = self.ok_hit_window / math.sqrt(3)

        meh_variance = (
            self.meh_hit_window * self.meh_hit_window
            + self.ok_hit_window * self.meh_hit_window
            + self.ok_hit_window * self.ok_hit_window
        ) / 3
        deviation = math.sqrt(
            (
                (relevant_count_great + relevant_count_ok) * math.pow(deviation, 2)
                + relevant_count_meh * meh_variance
            )
            / (relevant_count_great + relevant_count_ok + relevant_count_meh),
        )
        return deviation

    def _calculate_speed_high_deviation_nerf(
        self,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if self.speed_deviation is None:
            return 0.0

        speed_difficulty = _require_number(
            attributes.speed_difficulty,
            "speed_difficulty",
        )
        speed_value = self.difficulty_to_performance(speed_difficulty)
        excess_speed_difficulty_cutoff = 100 + 220 * math.pow(
            22 / self.speed_deviation,
            6.5,
        )
        if speed_value <= excess_speed_difficulty_cutoff:
            return 1.0

        scale = 50
        adjusted_speed_value = scale * (
            math.log((speed_value - excess_speed_difficulty_cutoff) / scale + 1)
            + excess_speed_difficulty_cutoff / scale
        )
        lerp = 1 - diff_utils.reverse_lerp(self.speed_deviation, 22.0, 27.0)
        adjusted_speed_value += (speed_value - adjusted_speed_value) * lerp
        return adjusted_speed_value / speed_value

    def _calculate_traceable_bonus(self, slider_factor: float = 1.0) -> float:
        high_approach_rate_slider_visibility_factor = (
            0.5 + math.pow(slider_factor, 6) / 2
        )
        low_approach_rate_slider_visibility_factor = math.pow(slider_factor, 6)
        traceable_bonus = 0.0275
        traceable_bonus += (
            0.025
            * (12.0 - max(self.approach_rate, 7))
            * high_approach_rate_slider_visibility_factor
        )
        if self.approach_rate < 7:
            traceable_bonus += (
                0.025
                * (7.0 - max(self.approach_rate, 0))
                * low_approach_rate_slider_visibility_factor
            )
        if self.approach_rate < 0:
            traceable_bonus += (
                0.025
                * (1 - math.pow(1.5, self.approach_rate))
                * low_approach_rate_slider_visibility_factor
            )
        return traceable_bonus

    @staticmethod
    def _calculate_miss_penalty(
        miss_count: float,
        difficult_strain_count: float,
    ) -> float:
        denominator = 4 * math.log(max(1, difficult_strain_count))
        if denominator == 0:
            return 0.0
        return 0.93 / (miss_count / denominator + 1)

    def _get_combo_scaling_factor(
        self,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        if attributes.max_combo <= 0:
            return 1.0
        return min(
            math.pow(self.score_max_combo, 0.8) / math.pow(attributes.max_combo, 0.8),
            1.0,
        )

    @staticmethod
    def _calculate_rate_adjusted_approach_rate(
        approach_rate: float,
        clock_rate: float,
    ) -> float:
        if approach_rate > 5:
            preempt = 1200 + (450 - 1200) * (approach_rate - 5) / 5
        else:
            preempt = 1200 + (1200 - 1800) * (approach_rate - 5) / 5
        preempt /= clock_rate
        if preempt < 1200:
            return (preempt - 1200) / (450 - 1200) * 5 + 5
        return (preempt - 1200) / (1200 - 1800) * 5 + 5

    @property
    def total_hits(self) -> int:
        return self.count_great + self.count_ok + self.count_meh + self.count_miss

    @property
    def total_successful_hits(self) -> int:
        return self.count_great + self.count_ok + self.count_meh

    @property
    def total_imperfect_hits(self) -> int:
        return self.count_ok + self.count_meh + self.count_miss
