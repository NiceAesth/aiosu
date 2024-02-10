"""
This module contains models for kudosu objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from .base import BaseModel

__all__ = (
    "KudosuAction",
    "KudosuGiver",
    "KudosuHistory",
    "KudosuPost",
)

KudosuAction = Literal[
    "give",
    "vote.give",
    "reset",
    "vote.reset",
    "revoke",
    "vote.revoke",
]


class KudosuGiver(BaseModel):
    url: str
    username: str


class KudosuPost(BaseModel):
    title: str
    url: Optional[str] = None


class KudosuHistory(BaseModel):
    id: int
    action: KudosuAction
    created_at: datetime
    amount: int
    model: str
    giver: Optional[KudosuGiver] = None
    post: Optional[KudosuPost] = None
