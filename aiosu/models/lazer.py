"""
This module contains models for lazer specific data.
"""
from __future__ import annotations

from typing import Any
from typing import Optional

from pydantic import Field

from .base import BaseModel

__all__ = (
    "LazerMod",
    "LazerScoreStatistics",
)


class LazerMod(BaseModel):
    """Temporary model for lazer mods."""

    acronym: str
    settings: dict[str, Any] = Field(default_factory=dict)


class LazerScoreStatistics(BaseModel):
    ok: Optional[int]
    meh: Optional[int]
    miss: Optional[int]
    great: Optional[int]
    ignore_hit: Optional[int]
    ignore_miss: Optional[int]
    large_bonus: Optional[int]
    large_tick_hit: Optional[int]
    large_tick_miss: Optional[int]
    small_bonus: Optional[int]
    small_tick_hit: Optional[int]
    small_tick_miss: Optional[int]
    good: Optional[int]
    perfect: Optional[int]
    legacy_combo_increase: Optional[int]


class LazerReplayData(BaseModel):
    mods: list[LazerMod]
    statistics: LazerScoreStatistics
    maximum_statistics: LazerScoreStatistics
