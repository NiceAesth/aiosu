"""
This module contains models for news post objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from .base import BaseModel
from .common import CursorModel

__all__ = (
    "Navigation",
    "NewsListing",
    "NewsPost",
    "NewsSearch",
    "NewsSortType",
)

NewsSortType = Literal["published_asc", "published_desc"]


class NewsSearch(BaseModel):
    limit: int
    sort: NewsSortType


class Navigation(BaseModel):
    newer: NewsPost | None = None
    older: NewsPost | None = None


class NewsPost(BaseModel):
    id: int
    title: str
    slug: str
    author: str
    edit_url: str
    published_at: datetime
    updated_at: datetime
    first_image: str | None = None
    content: str | None = None
    preview: str | None = None
    navigation: Navigation | None = None


class NewsSidebar(BaseModel):
    current_year: int
    years: list[int]
    news_posts: list[NewsPost]


class NewsListing(CursorModel):
    news_posts: list[NewsPost]
    search: NewsSearch
    news_sidebar: NewsSidebar
