"""
This module contains models for API v2 difficulty attribute objects.
"""

from __future__ import annotations

import abc

from .base import BaseModel

__all__ = (
    "CatchPerformanceAttributes",
    "ManiaPerformanceAttributes",
    "OsuPerformanceAttributes",
    "PerformanceAttributes",
    "TaikoPerformanceAttributes",
)


class PerformanceAttributes(BaseModel, abc.ABC):
    total: float


class OsuPerformanceAttributes(PerformanceAttributes):
    aim: float
    speed: float
    accuracy: float
    flashlight: float
    reading: float
    effective_miss_count: float
    combo_based_estimated_miss_count: float
    score_based_estimated_miss_count: float | None
    aim_estimated_slider_breaks: float
    speed_estimated_slider_breaks: float
    speed_deviation: float | None


class TaikoPerformanceAttributes(PerformanceAttributes):
    difficulty: float
    accuracy: float
    estimated_unstable_rate: float | None


class ManiaPerformanceAttributes(PerformanceAttributes):
    difficulty: float


class CatchPerformanceAttributes(PerformanceAttributes): ...
