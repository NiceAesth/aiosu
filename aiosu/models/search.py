"""
This module contains models for the search endpoint.
"""
from __future__ import annotations

from typing import Literal
from typing import Optional
from typing import Union

from .base import BaseModel
from .user import User
from .wiki import WikiPage

__all__ = (
    "SearchMode",
    "SearchResponse",
    "SearchResult",
)

SearchMode = Literal["all", "user", "wiki_page"]


class SearchResult(BaseModel):
    data: list[Union[User, WikiPage]]
    total: int


class SearchResponse(BaseModel):
    users: Optional[SearchResult] = None
    wiki_pages: Optional[SearchResult] = None
