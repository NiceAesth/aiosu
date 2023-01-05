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
    "NewsPost",
    "Navigation",
    "NewsListing",
    "NewsSearch",
)


class NewsSearch(BaseModel):
    limit: int
    sort: Literal["published_desc"]


class Navigation(BaseModel):
    newer: Optional[NewsPost]
    older: Optional[NewsPost]


class NewsPost(BaseModel):
    id: int
    title: str
    slug: str
    author: str
    edit_url: str
    published_at: datetime
    updated_at: datetime
    first_image: Optional[str]
    content: Optional[str]
    preview: Optional[str]
    navigation: Optional[Navigation]


class NewsSidebar(BaseModel):
    current_year: int
    years: list[int]
    news_posts: list[NewsPost]


class NewsListing(CursorModel):
    news_posts: list[NewsPost]
    search: NewsSearch
    news_sidebar: NewsSidebar


Navigation.update_forward_refs()
