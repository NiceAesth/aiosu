"""
This module contains models for API v2 difficulty attribute objects.
"""
from __future__ import annotations

import abc

from .models import BaseModel


class PerformanceAttributes(BaseModel, abc.ABC):
    total: float


class OsuPerformanceAttributes(PerformanceAttributes):
    aim: float
    speed: float
    accuracy: float
    flashlight: float
    effective_miss_count: float


class TaikoPerformanceAttributes(PerformanceAttributes):
    difficulty: float
    accuracy: float
    effective_miss_count: float


class ManiaPerformanceAttributes(PerformanceAttributes):
    difficulty: float


class CatchPerformanceAttributes(PerformanceAttributes):
    ...
