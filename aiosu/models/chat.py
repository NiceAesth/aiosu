"""
This module contains models for chat.
"""
from __future__ import annotations

from typing import Literal
from typing import Optional

from pydantic import Field

from .base import BaseModel
from .common import CurrentUserAttributes
from .user import User

__all__ = (
    "ChatChannel",
    "ChatMessage",
    "ChatMessageCreateResponse",
    "ChatChannelTypes",
    "ChatIncludeTypes",
    "ChatUpdateResponse",
    "ChatUserSilence",
    "ChatChannelResponse",
)

ChatChannelTypes = Literal[
    "PM",
    "PUBLIC",
    "PRIVATE",
    "MULTIPLAYER",
    "SPECTATOR",
    "TEMPORARY",
    "GROUP",
    "ANNOUNCE",
]

ChatIncludeTypes = Literal[
    "messages",
    "presence",
    "silences",
]


class ChatUserSilence(BaseModel):
    id: int
    user_id: int


class ChatChannel(BaseModel):
    id: int = Field(alias="channel_id")
    type: ChatChannelTypes
    name: str
    moderated: bool
    icon: Optional[str] = None
    description: Optional[str] = None
    last_message_id: Optional[int] = None
    user_ids: Optional[list[int]] = Field(default=None, alias="users")
    current_user_attributes: Optional[CurrentUserAttributes] = None


class ChatMessage(BaseModel):
    message_id: int
    sender_id: int
    channel_id: int
    timestamp: str
    content: str
    is_action: bool
    uuid: Optional[str] = None
    sender: Optional[User] = None


class ChatMessageCreateResponse(BaseModel):
    channel: ChatChannel
    message: ChatMessage


class ChatUpdateResponse(BaseModel):
    messages: Optional[list[ChatMessage]] = None
    presence: Optional[list[ChatChannel]] = None
    silences: list


class ChatChannelResponse(BaseModel):
    channel: ChatChannel
    users: Optional[list[User]] = None
