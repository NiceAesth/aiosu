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
)

ChatChannelTypes = Literal[
    "PM",
    "PUBLIC",
    "PRIVATE",
    "MULTIPLAYER",
    "SPECTATOR",
    "TEMPORARY",
    "GROUP",
]


class ChatChannel(BaseModel):
    channel_id: int
    type: ChatChannelTypes
    name: str
    icon: str
    moderated: bool
    description: Optional[str]
    last_message_id: Optional[int]
    user_ids: Optional[list[int]] = Field(alias="users")
    current_user_attributes: Optional[CurrentUserAttributes]


class ChatMessage(BaseModel):
    message_id: int
    channel_id: int
    sender_id: int
    content: str
    timestamp: str
    is_action: bool
    sender: User
    uuid: Optional[str]


class ChatMessageCreateResponse(BaseModel):
    new_channel_id: int
    presence: list[ChatChannel]
    message: ChatMessage
