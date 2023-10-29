"""
This module contains the Forum model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from .base import BaseModel
from .common import CursorModel
from .common import HTMLBody

__all__ = [
    "ForumCreateTopicResponse",
    "ForumPoll",
    "ForumPollOption",
    "ForumPost",
    "ForumTopic",
    "ForumTopicResponse",
    "ForumTopicType",
]

ForumTopicType = Literal[
    "normal",
    "sticky",
    "announcement",
]


class ForumPollOption(BaseModel):
    id: int
    text: HTMLBody
    vote_count: Optional[int] = None


class ForumPoll(BaseModel):
    allow_vote_change: bool
    hide_incomplete_results: bool
    max_votes: int
    total_vote_count: int
    options: list[ForumPollOption]
    started_at: datetime
    title: HTMLBody
    ended_at: Optional[datetime] = None
    last_vote_at: Optional[datetime] = None


class ForumTopic(BaseModel):
    id: int
    title: str
    created_at: datetime
    first_post_id: int
    last_post_id: int
    forum_id: int
    is_locked: bool
    post_count: int
    type: ForumTopicType
    updated_at: datetime
    user_id: int
    deleted_at: Optional[datetime] = None
    poll: Optional[ForumPoll] = None


class ForumPost(BaseModel):
    id: int
    created_at: datetime
    forum_id: int
    topic_id: int
    user_id: int
    edited_by_id: Optional[int] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    body: Optional[HTMLBody] = None


class ForumTopicResponse(CursorModel):
    topic: ForumTopic
    posts: list[ForumPost]


class ForumCreateTopicResponse(BaseModel):
    topic: ForumTopic
    post: ForumPost
