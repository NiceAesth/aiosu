"""
This module contains models for seasonal background objects.
"""
from __future__ import annotations

from datetime import datetime

from .models import BaseModel
from .user import User


class Background(BaseModel):
    url: str
    user: User


class SeasonalBackgroundSet(BaseModel):
    ends_at: datetime
    backgrounds: list[Background]
