"""
This module contains models for wiki objects.
"""
from __future__ import annotations

from typing import Optional

from .base import BaseModel


class WikiPage(BaseModel):
    title: str
    path: str
    locale: str
    available_locales: list[str]
    layout: str
    markdown: str
    subtitle: Optional[str]
    tags: Optional[list[str]]
