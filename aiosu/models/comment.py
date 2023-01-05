"""
This module contains models for comment objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import BaseModel
from .common import CurrentUserAttributes
from .common import CursorModel
from .user import User

__all__ = (
    "Commentable",
    "Comment",
    "CommentBundle",
)


class Commentable(BaseModel):
    id: Optional[int]
    title: Optional[str]
    url: Optional[str]
    type: Optional[str]
    owner_id: Optional[int]
    owner_title: Optional[str]
    current_user_attributes: Optional[CurrentUserAttributes]


class Comment(BaseModel):
    id: int
    commentable_id: int
    commentable_type: str
    created_at: datetime
    updated_at: datetime
    pinned: bool
    votes_count: int
    replies_count: int
    message: Optional[str]
    message_html: Optional[str]
    deleted_at: Optional[datetime]
    edited_at: Optional[datetime]
    edited_by_id: Optional[int]
    parent_id: Optional[int]
    legacy_name: Optional[str]
    user_id: Optional[int]


class CommentBundle(CursorModel):
    commentable_meta: list[Commentable]
    comments: list[Comment]
    has_more: bool
    included_comments: list[Comment]
    sort: str
    user_follow: bool
    user_votes: list[int]
    users: list[User]
    pinned_comments: Optional[list[Comment]]
    total: Optional[int]
    top_level_count: Optional[int]
    has_more_id: Optional[int]
