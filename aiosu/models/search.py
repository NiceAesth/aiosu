"""
This module contains models for the search endpoint.
"""
from __future__ import annotations

from typing import Optional
from typing import Union

from .base import BaseModel
from .user import User
from .wiki import WikiPage


class SearchResult(BaseModel):
    data: list[Union[User, WikiPage]]
    total: int


class SearchResponse(BaseModel):
    users: Optional[SearchResult]
    wiki_pages: Optional[SearchResult]
