"""
This module contains models for spotlight objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from .base import BaseModel

__all__ = ("Spotlight",)

SpotlightType = Literal["bestof", "monthly", "spotlight", "theme", "special"]


class Spotlight(BaseModel):
    id: int
    name: str
    mode_specific: bool
    type: SpotlightType
    start_date: datetime
    end_date: datetime
    participant_count: Optional[int] = None
