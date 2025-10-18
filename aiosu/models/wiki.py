"""
This module contains models for wiki objects.
"""

from __future__ import annotations

from .base import BaseModel

__all__ = ("WikiPage",)


class WikiPage(BaseModel):
    title: str
    path: str
    locale: str
    available_locales: list[str]
    layout: str
    markdown: str
    subtitle: str | None = None
    tags: list[str] | None = None
