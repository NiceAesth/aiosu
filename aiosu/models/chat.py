"""
This module contains models for chat.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import BaseModel
from .common import CurrentUserAttributes
from .user import User

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


class ChatMessage(BaseModel):
    message_id: int
    sender_id: int
    channel_id: int
    timestamp: str
    content: str
    is_action: bool
    uuid: str | None = None
    sender: User | None = None


class ChatMessageCreateResponse(BaseModel):
    channel: ChatChannel
    message: ChatMessage


class ChatUpdateResponse(BaseModel):
    messages: list[ChatMessage] | None = None
    presence: list[ChatChannel] | None = None
    silences: list


class ChatChannelResponse(BaseModel):
    channel: ChatChannel
    users: list[User] | None = None
