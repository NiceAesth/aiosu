from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...models.performance import ManiaPerformanceAttributes
from ._base import AbstractPerformanceCalculator
from ._base import _has_mod

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.score import Score


class ManiaPerformanceCalculator(AbstractPerformanceCalculator):
    def calculate(self, score: Score) -> ManiaPerformanceAttributes:
        self._validate_score(score)
        return self._create_performance_attributes(score, self.difficulty_attributes)

    def _create_performance_attributes(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> ManiaPerformanceAttributes:
        self.count_perfect = score.statistics.perfect
        self.count_great = score.statistics.great
        self.count_good = score.statistics.good
        self.count_ok = score.statistics.ok
        self.count_meh = score.statistics.meh
        self.count_miss = max(0, score.statistics.miss)
        self.score_accuracy = max(0.0, min(self._calculate_custom_accuracy(), 1.0))

        multiplier = 1.0
        if _has_mod(score, "NF"):
            multiplier *= 0.75
        if _has_mod(score, "EZ"):
            multiplier *= 0.5
        difficulty_value = self._compute_difficulty_value(attributes)
        total_value = difficulty_value * multiplier
        return ManiaPerformanceAttributes(
            difficulty=difficulty_value,
            total=total_value,
        )

    def _compute_difficulty_value(
        self,
        attributes: BeatmapDifficultyAttributes,
    ) -> float:
        difficulty_value = (
            8.0
            * math.pow(max(attributes.star_rating - 0.15, 0.05), 2.2)
            * max(0.0, 5 * self.score_accuracy - 4)
            * (1 + 0.1 * min(1.0, self.total_hits / 1500))
        )
        return difficulty_value

    @property
    def total_hits(self) -> int:
        return (
            self.count_perfect
            + self.count_ok
            + self.count_great
            + self.count_good
            + self.count_meh
            + self.count_miss
        )

    def _calculate_custom_accuracy(self) -> float:
        if self.total_hits == 0:
            return 0.0
        return (
            self.count_perfect * 320
            + self.count_great * 300
            + self.count_good * 200
            + self.count_ok * 100
            + self.count_meh * 50
        ) / (self.total_hits * 320)
