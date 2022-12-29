"""
This module contains models for news post objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import BaseModel


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


Navigation.update_forward_refs()
