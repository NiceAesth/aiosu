"""
This module contains models for comment objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

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
    id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    owner_id: Optional[int] = None
    owner_title: Optional[str] = None
    current_user_attributes: Optional[CurrentUserAttributes] = None


class Comment(BaseModel):
    id: int
    commentable_id: int
    commentable_type: CommentableType
    created_at: datetime
    updated_at: datetime
    pinned: bool
    votes_count: int
    replies_count: int
    message: Optional[str] = None
    message_html: Optional[str] = None
    deleted_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    edited_by_id: Optional[int] = None
    parent_id: Optional[int] = None
    legacy_name: Optional[str] = None
    user_id: Optional[int] = None


class CommentBundle(CursorModel):
    commentable_meta: list[Commentable]
    comments: list[Comment]
    has_more: bool
    included_comments: list[Comment]
    sort: CommentSortType
    user_follow: bool
    user_votes: list[int]
    users: list[User]
    pinned_comments: Optional[list[Comment]] = None
    total: Optional[int] = None
    top_level_count: Optional[int] = None
    has_more_id: Optional[int] = None
