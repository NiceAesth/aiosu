"""
This module contains models for lazer specific data.
"""

from __future__ import annotations

from .base import BaseModel
from .mods import Mods
from .score import ScoreStatistics

__all__ = ("LazerReplayData",)


class LazerReplayData(BaseModel):
    mods: Mods
    statistics: ScoreStatistics
    maximum_statistics: ScoreStatistics
    online_id: int | None = None
    client_version: str | None = None
