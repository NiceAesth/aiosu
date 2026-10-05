from __future__ import annotations

import abc
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...models.score import Score

if TYPE_CHECKING:
    from ...models.beatmap import BeatmapDifficultyAttributes
    from ...models.mods import Mod
    from ...models.performance import PerformanceAttributes


@dataclass
class _BeatmapDifficulty:
    overall_difficulty: float
    approach_rate: float
    drain_rate: float


def _require_number(value: object, name: str) -> float:
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"Missing or invalid {name}.")
    return float(value)


def _get_mod(score: Score, acronym: str) -> Mod | None:
    return next((mod for mod in score.mods if mod.acronym == acronym), None)


def _has_mod(score: Score, acronym: str) -> bool:
    return _get_mod(score, acronym) is not None


def _calculate_rate_with_mods(score: Score) -> float:
    rate = 1.0
    for mod in score.mods:
        if mod.acronym == "DT" and "NC" in score.mods and not mod.settings:
            continue
        if mod.acronym in ("DT", "NC"):
            rate *= _require_number(
                mod.settings.get("speed_change", 1.5),
                "speed_change",
            )
        elif mod.acronym in ("WU", "WD"):
            rate *= round(
                _require_number(mod.settings.get("initial_rate", 1.0), "initial_rate"),
                2,
            )
        elif mod.acronym == "AS":
            rate *= _require_number(
                mod.settings.get("initial_rate", 1.0),
                "initial_rate",
            )
        elif mod.acronym in ("HT", "DC"):
            rate *= _require_number(
                mod.settings.get("speed_change", 0.75),
                "speed_change",
            )
    if rate <= 0:
        raise ValueError("Clock rate must be positive.")
    return rate


def _difficulty_with_mods(score: Score) -> _BeatmapDifficulty:
    if score.beatmap is None:
        raise ValueError("Given score does not have a beatmap.")
    difficulty = _BeatmapDifficulty(
        overall_difficulty=_require_number(score.beatmap.accuracy, "beatmap.accuracy"),
        approach_rate=_require_number(score.beatmap.ar, "beatmap.ar"),
        drain_rate=_require_number(score.beatmap.drain, "beatmap.drain"),
    )
    for mod in score.mods:
        if mod.acronym == "HR":
            difficulty.overall_difficulty = min(
                difficulty.overall_difficulty * 1.4,
                10.0,
            )
            difficulty.approach_rate = min(difficulty.approach_rate * 1.4, 10.0)
            difficulty.drain_rate = min(difficulty.drain_rate * 1.4, 10.0)
        elif mod.acronym == "EZ":
            difficulty.overall_difficulty *= 0.5
            difficulty.approach_rate *= 0.5
            difficulty.drain_rate *= 0.5
        elif mod.acronym == "TP":
            difficulty.approach_rate *= 0.5
        elif mod.acronym == "DA":
            overall_difficulty = mod.settings.get("overall_difficulty")
            approach_rate = mod.settings.get("approach_rate")
            drain_rate = mod.settings.get("drain_rate")
            if overall_difficulty is not None:
                difficulty.overall_difficulty = _require_number(
                    overall_difficulty,
                    "overall_difficulty",
                )
            if approach_rate is not None:
                difficulty.approach_rate = _require_number(
                    approach_rate,
                    "approach_rate",
                )
            if drain_rate is not None:
                difficulty.drain_rate = _require_number(drain_rate, "drain_rate")
    return difficulty


class AbstractPerformanceCalculator(abc.ABC):
    __slots__ = ("difficulty_attributes",)

    def __init__(self, difficulty_attributes: BeatmapDifficultyAttributes):
        self.difficulty_attributes = difficulty_attributes

    @abc.abstractmethod
    def calculate(self, score: Score) -> PerformanceAttributes: ...

    @staticmethod
    def _validate_score(score: Score) -> None:
        if not isinstance(score, Score):
            raise TypeError("Performance calculators require a Score.")
