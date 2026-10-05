from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._base import _has_mod
from ._base import _require_number

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.score import Score


class OsuLegacyScoreMissCalculator:
    def __init__(self, score: Score, attributes: BeatmapDifficultyAttributes):
        self.score = score
        self.attributes = attributes

    def calculate(self) -> float:
        if self.attributes.max_combo == 0 or not self.score.legacy_total_score:
            return 0.0
        score_v1_multiplier = (
            _require_number(
                self.attributes.legacy_score_base_multiplier,
                "legacy_score_base_multiplier",
            )
            * self._get_legacy_score_multiplier()
        )
        relevant_combo_per_object = self._calculate_relevant_score_combo_per_object()
        maximum_miss_count = self._calculate_maximum_combo_based_miss_count()
        score_obtained_during_max_combo = self._calculate_score_at_combo(
            self.score.max_combo,
            relevant_combo_per_object,
            score_v1_multiplier,
        )
        remaining_score = (
            self.score.legacy_total_score - score_obtained_during_max_combo
        )
        if remaining_score <= 0:
            return maximum_miss_count
        remaining_combo = self.attributes.max_combo - self.score.max_combo
        expected_remaining_score = self._calculate_score_at_combo(
            remaining_combo,
            relevant_combo_per_object,
            score_v1_multiplier,
        )
        score_based_miss_count = expected_remaining_score / remaining_score
        score_based_miss_count = max(score_based_miss_count, 1)
        return min(score_based_miss_count, maximum_miss_count)

    def _calculate_score_at_combo(
        self,
        combo: float,
        relevant_combo_per_object: float,
        score_v1_multiplier: float,
    ) -> float:
        statistics = self.score.statistics
        total_hits = statistics.great + statistics.ok + statistics.meh + statistics.miss
        estimated_objects = combo / relevant_combo_per_object - 1
        combo_score = (
            (
                2 * (relevant_combo_per_object - 1)
                + (estimated_objects - 1) * relevant_combo_per_object
            )
            * estimated_objects
            / 2
            if relevant_combo_per_object > 0
            else 0.0
        )
        combo_score *= self.score.accuracy * 300 / 25 * score_v1_multiplier
        objects_hit = (total_hits - statistics.miss) * combo / self.attributes.max_combo
        non_combo_score = (
            (
                300
                + _require_number(
                    self.attributes.nested_score_per_object,
                    "nested_score_per_object",
                )
            )
            * self.score.accuracy
            * objects_hit
        )
        return combo_score + non_combo_score

    def _calculate_relevant_score_combo_per_object(self) -> float:
        combo_score = _require_number(
            self.attributes.maximum_legacy_combo_score,
            "maximum_legacy_combo_score",
        )
        combo_score /= (
            300.0
            / 25.0
            * _require_number(
                self.attributes.legacy_score_base_multiplier,
                "legacy_score_base_multiplier",
            )
        )
        result: float = (self.attributes.max_combo - 2) * self.attributes.max_combo
        result /= max(self.attributes.max_combo + 2 * (combo_score - 1), 1)
        return result

    def _calculate_maximum_combo_based_miss_count(self) -> float:
        assert self.score.beatmap is not None
        slider_count = int(
            _require_number(self.score.beatmap.count_sliders, "beatmap.count_sliders"),
        )
        count_miss = self.score.statistics.miss
        if slider_count <= 0:
            return float(count_miss)
        total_imperfect_hits = (
            self.score.statistics.ok + self.score.statistics.meh + count_miss
        )
        miss_count = 0.0
        likely_missed_sliderend_portion = 0.04 + 0.06 * math.pow(
            min(
                _require_number(
                    self.attributes.aim_top_weighted_slider_factor,
                    "aim_top_weighted_slider_factor",
                ),
                1,
            ),
            2,
        )
        full_combo_threshold = self.attributes.max_combo - min(
            4 + likely_missed_sliderend_portion * slider_count,
            slider_count,
        )
        if self.score.max_combo < full_combo_threshold:
            miss_count = math.pow(
                full_combo_threshold / max(1.0, self.score.max_combo),
                2.5,
            )
        miss_count = min(miss_count, total_imperfect_hits)
        max_possible_slider_breaks = min(
            slider_count,
            (self.attributes.max_combo - self.score.max_combo) // 2,
        )
        slider_breaks = miss_count - count_miss
        if slider_breaks > max_possible_slider_breaks:
            miss_count = count_miss + max_possible_slider_breaks
        return miss_count

    def _get_legacy_score_multiplier(self) -> float:
        score_v2 = _has_mod(self.score, "V2")
        multiplier = 1.0
        for mod in self.score.mods:
            if mod.acronym == "DT" and "NC" in self.score.mods and not mod.settings:
                continue
            if mod.acronym == "NF":
                multiplier *= 1.0 if score_v2 else 0.5
            elif mod.acronym == "EZ":
                multiplier *= 0.5
            elif mod.acronym in ("HT", "DC"):
                multiplier *= 0.3
            elif mod.acronym == "HD":
                multiplier *= 1.06
            elif mod.acronym == "HR":
                multiplier *= 1.10 if score_v2 else 1.06
            elif mod.acronym in ("DT", "NC"):
                multiplier *= 1.20 if score_v2 else 1.12
            elif mod.acronym == "FL":
                multiplier *= 1.12
            elif mod.acronym == "SO":
                multiplier *= 0.9
            elif mod.acronym in ("RX", "AP"):
                return 0.0
        return multiplier
