"""
This module contains models for news post objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

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
    newer: Optional[NewsPost] = None
    older: Optional[NewsPost] = None


class NewsPost(BaseModel):
    id: int
    title: str
    slug: str
    author: str
    edit_url: str
    published_at: datetime
    updated_at: datetime
    first_image: Optional[str] = None
    content: Optional[str] = None
    preview: Optional[str] = None
    navigation: Optional[Navigation] = None


class NewsSidebar(BaseModel):
    current_year: int
    years: list[int]
    news_posts: list[NewsPost]


class NewsListing(CursorModel):
    news_posts: list[NewsPost]
    search: NewsSearch
    news_sidebar: NewsSidebar
