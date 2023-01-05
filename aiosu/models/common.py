"""
This module contains models for miscellaneous objects.
"""
from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import Literal
from typing import Optional

from emojiflags.lookup import lookup as flag_lookup  # type: ignore
from pydantic import Field
from pydantic import validator

from .base import BaseModel
from .gamemode import Gamemode

__all__ = (
    "Achievement",
    "Country",
    "CurrentUserAttributes",
    "TimestampedCount",
    "CursorModel",
    "SortTypes",
)


SortTypes = Literal["id_asc", "id_desc"]


class TimestampedCount(BaseModel):
    start_date: datetime
    count: int

    @validator("start_date", pre=True)
    def _date_validate(cls, v: str) -> datetime:
        return datetime.strptime(v, "%Y-%m-%d")


class Achievement(BaseModel):
    id: int
    name: str
    slug: str
    desciption: str
    grouping: str
    icon_url: str
    mode: Gamemode
    ordering: int
    instructions: Optional[str]


class Country(BaseModel):
    code: str
    name: str

    @property
    def flag_emoji(self) -> str:
        r"""Emoji for the flag.

        :return: Unicode emoji representation of the country's flag
        :rtype: str
        """
        return flag_lookup(self.code)


class CurrentUserAttributes(BaseModel):
    can_destroy: Optional[bool]
    can_reopen: Optional[bool]
    can_moderate_kudosu: Optional[bool]
    can_resolve: Optional[bool]
    vote_score: Optional[int]
    can_message: Optional[bool]
    can_message_error: Optional[str]
    last_read_id: Optional[int]
    can_new_comment: Optional[bool]
    can_new_comment_reason: Optional[str]


class CursorModel(BaseModel):
    r"""NOTE: This model is not serializable by orjson directly.

    Use the provided .json() or .dict() methods instead.
    """

    cursor_string: Optional[str]
    next: Optional[partial] = Field(exclude=True)
    """Partial function to get the next page of results."""
