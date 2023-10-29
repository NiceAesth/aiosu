"""
This module contains models for rankings.
"""
from __future__ import annotations

from typing import Literal
from typing import Optional

from .beatmap import Beatmapset
from .common import CursorModel
from .spotlight import Spotlight
from .user import UserStats


__all__ = (
    "RankingFilter",
    "RankingType",
    "RankingVariant",
    "Rankings",
)

RankingFilter = Literal["all", "friends"]
RankingType = Literal["performance", "score", "country", "charts"]
RankingVariant = Literal["4k", "7k"]


class Rankings(CursorModel):
    ranking: list[UserStats]
    total: Optional[int] = None
    spotlight: Optional[Spotlight] = None
    beatmapsets: Optional[list[Beatmapset]] = None
