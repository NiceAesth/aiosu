from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...models.performance import CatchPerformanceAttributes
from ._base import AbstractPerformanceCalculator
from ._base import _calculate_rate_with_mods
from ._base import _difficulty_with_mods
from ._base import _has_mod

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.score import Score


class CatchPerformanceCalculator(AbstractPerformanceCalculator):
    def calculate(self, score: Score) -> CatchPerformanceAttributes:
        self._validate_score(score)
        return self._create_performance_attributes(score, self.difficulty_attributes)

    def _create_performance_attributes(
        self,
        score: Score,
        attributes: BeatmapDifficultyAttributes,
    ) -> CatchPerformanceAttributes:
        self.num300 = score.statistics.great
        self.num100 = score.statistics.large_tick_hit
        self.num50 = score.statistics.small_tick_hit
        self.num_katu = score.statistics.small_tick_miss
        self.num_miss = max(0, score.statistics.count_miss)
        score_max_combo = max(0, min(score.max_combo, attributes.max_combo))
        value = (
            math.pow(5.0 * max(1.0, attributes.star_rating / 0.0049) - 4.0, 2.0)
            / 100000.0
        )
        num_total_hits = self._total_combo_hits()
        length_bonus = 0.95 + 0.3 * min(1.0, num_total_hits / 2500.0)
        if num_total_hits > 2500:
            length_bonus += math.log10(num_total_hits / 2500.0) * 0.475
        value *= length_bonus
        value *= math.pow(0.97, self.num_miss)

        if attributes.max_combo > 0:
            value *= min(
                math.pow(score_max_combo, 0.35) / math.pow(attributes.max_combo, 0.35),
                1.0,
            )
        difficulty = _difficulty_with_mods(score)
        clock_rate = _calculate_rate_with_mods(score)
        if difficulty.approach_rate > 5:
            preempt = 1200 + (450 - 1200) * (difficulty.approach_rate - 5) / 5
        else:
            preempt = 1200 + (1200 - 1800) * (difficulty.approach_rate - 5) / 5
        preempt /= clock_rate
        if preempt > 1200.0:
            approach_rate = -(preempt - 1800.0) / 120.0
        else:
            approach_rate = -(preempt - 1200.0) / 150.0 + 5.0

        approach_rate_factor = 1.0
        if approach_rate > 9.0:
            approach_rate_factor += 0.1 * (approach_rate - 9.0)
        if approach_rate > 10.0:
            approach_rate_factor += 0.1 * (approach_rate - 10.0)
        elif approach_rate < 8.0:
            approach_rate_factor += 0.025 * (8.0 - approach_rate)
        value *= approach_rate_factor

        if _has_mod(score, "HD"):
            if approach_rate <= 10.0:
                value *= 1.05 + 0.075 * (10.0 - approach_rate)
            else:
                value *= 1.01 + 0.04 * (11.0 - min(11.0, approach_rate))
        if _has_mod(score, "FL"):
            value *= 1.35 * length_bonus
        value *= math.pow(self._accuracy(), 5.5)
        if _has_mod(score, "NF"):
            value *= max(0.90, 1.0 - 0.02 * self.num_miss)
        return CatchPerformanceAttributes(total=value)

    def _accuracy(self) -> float:
        if self._total_hits() == 0:
            return 0.0
        return max(0.0, min(self._total_successful_hits() / self._total_hits(), 1.0))

    def _total_hits(self) -> int:
        return self.num50 + self.num100 + self.num300 + self.num_miss + self.num_katu

    def _total_successful_hits(self) -> int:
        return self.num50 + self.num100 + self.num300

    def _total_combo_hits(self) -> int:
        return self.num_miss + self.num100 + self.num300
