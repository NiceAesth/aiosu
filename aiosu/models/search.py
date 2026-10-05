"""
This module contains models for the search endpoint.
"""

from __future__ import annotations

from typing import Literal

from .base import BaseModel
from .user import UserCompact
from .wiki import WikiPage

__all__ = (
    "SearchMode",
    "SearchResponse",
    "SearchResult",
)

SearchMode = Literal["all", "user", "wiki_page"]


class SearchResult(BaseModel):
    data: list[UserCompact | WikiPage]
    total: int


class SearchResponse(BaseModel):
    users: SearchResult | None = None
    wiki_pages: SearchResult | None = None
