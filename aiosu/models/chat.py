"""
This module contains models for chat.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import BaseModel
from .common import CurrentUserAttributes
from .user import UserCompact

__all__ = (
    "ChatChannel",
    "ChatChannelResponse",
    "ChatChannelType",
    "ChatIncludeType",
    "ChatMessage",
    "ChatMessageCreateResponse",
    "ChatUpdateResponse",
    "ChatUserSilence",
)

ChatChannelType = Literal[
    "PM",
    "PUBLIC",
    "PRIVATE",
    "MULTIPLAYER",
    "SPECTATOR",
    "TEMPORARY",
    "GROUP",
    "ANNOUNCE",
]

ChatIncludeType = Literal[
    "messages",
    "presence",
    "silences",
]


class ChatUserSilence(BaseModel):
    id: int
    user_id: int


class ChatChannel(BaseModel):
    id: int = Field(alias="channel_id")
    type: ChatChannelType
    name: str
    moderated: bool
    message_length_limit: int
    icon: str | None = None
    description: str | None = None
    last_message_id: int | None = None
    user_ids: list[int] | None = Field(default=None, alias="users")
    current_user_attributes: CurrentUserAttributes | None = None
    active_user_count: int | None = None
    last_read_id: int | None = None
    recent_messages: list[ChatMessage] | None = None
    uuid: str | None = None


class ChatMessage(BaseModel):
    message_id: int
    sender_id: int
    channel_id: int
    timestamp: str
    content: str
    is_action: bool
    type: Literal["action", "markdown", "plain"] | None = None
    uuid: str | None = None
    sender: UserCompact | None = None


class ChatMessageCreateResponse(BaseModel):
    channel: ChatChannel
    message: ChatMessage


class ChatUpdateResponse(BaseModel):
    messages: list[ChatMessage] | None = None
    presence: list[ChatChannel] | None = None
    silences: list


class ChatChannelResponse(BaseModel):
    channel: ChatChannel
    users: list[UserCompact] | None = None
