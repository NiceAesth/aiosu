"""
This module contains models for rankings.
"""
from __future__ import annotations

from typing import Literal
from typing import Optional

from .base import BaseModel
from .beatmap import Beatmapset
from .common import Cursor
from .spotlight import Spotlight
from .user import UserStats


__all__ = (
    "RankingType",
    "Rankings",
)

RankingType = Literal["performance", "score", "country", "charts"]


class Rankings(BaseModel):
    ranking: UserStats
    cursor: Cursor
    total: int
    spotlight: Optional[Spotlight]
    beatmapsets: Optional[list[Beatmapset]]
