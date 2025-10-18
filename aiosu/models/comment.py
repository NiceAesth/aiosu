"""
This module contains models for comment objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from .base import BaseModel
from .common import CurrentUserAttributes
from .common import CursorModel
from .user import User

__all__ = (
    "Comment",
    "CommentBundle",
    "CommentSortType",
    "Commentable",
    "CommentableType",
)

CommentSortType = Literal["new", "old", "top"]
CommentableType = Literal["beatmapset", "news_post", "build"]


class Commentable(BaseModel):
    id: int | None = None
    title: str | None = None
    url: str | None = None
    type: str | None = None
    owner_id: int | None = None
    owner_title: str | None = None
    current_user_attributes: CurrentUserAttributes | None = None


class Comment(BaseModel):
    id: int
    commentable_id: int
    commentable_type: CommentableType
    created_at: datetime
    updated_at: datetime
    pinned: bool
    votes_count: int
    replies_count: int
    message: str | None = None
    message_html: str | None = None
    deleted_at: datetime | None = None
    edited_at: datetime | None = None
    edited_by_id: int | None = None
    parent_id: int | None = None
    legacy_name: str | None = None
    user_id: int | None = None


class CommentBundle(CursorModel):
    commentable_meta: list[Commentable]
    comments: list[Comment]
    has_more: bool
    included_comments: list[Comment]
    sort: CommentSortType
    user_follow: bool
    user_votes: list[int]
    users: list[User]
    pinned_comments: list[Comment] | None = None
    total: int | None = None
    top_level_count: int | None = None
    has_more_id: int | None = None
