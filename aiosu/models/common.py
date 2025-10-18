"""
This module contains models for miscellaneous objects.
"""

from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Callable
from datetime import datetime
from functools import cached_property
from typing import Literal

from emojiflags.lookup import lookup as flag_lookup  # type: ignore
from pydantic import Field
from pydantic import computed_field
from pydantic import field_validator

from .base import BaseModel
from .gamemode import Gamemode

__all__ = (
    "Achievement",
    "BeatmapScoreboardType",
    "Country",
    "CurrentUserAttributes",
    "CursorModel",
    "HTMLBody",
    "ScoreType",
    "SortType",
    "TimestampedCount",
)


SortType = Literal["id_asc", "id_desc"]
ScoreType = Literal[
    "solo_score",
    "score_best_osu",
    "score_best_taiko",
    "score_best_fruits",
    "score_best_mania",
    "score_osu",
    "score_taiko",
    "score_fruits",
    "score_mania",
    "legacy_match_score",
]
BeatmapScoreboardType = Literal["global", "country", "friend"]


class TimestampedCount(BaseModel):
    start_date: datetime
    count: int

    @field_validator("start_date", mode="before")
    @classmethod
    def _date_validate(cls, v: object) -> datetime:
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d")
        if isinstance(v, datetime):
            return v

        raise ValueError(f"{v} is not a valid value.")


class Achievement(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    grouping: str
    icon_url: str
    ordering: int
    mode: Gamemode | None = None
    instructions: str | None = None


class Country(BaseModel):
    code: str
    name: str

    @computed_field  # type: ignore
    @cached_property
    def flag_emoji(self) -> str:
        r"""Emoji for the flag.

        :return: Unicode emoji representation of the country's flag
        :rtype: str
        """
        return flag_lookup(self.code)


class HTMLBody(BaseModel):
    html: str
    raw: str | None = None
    bbcode: str | None = None


class PinAttributes(BaseModel):
    is_pinned: bool
    score_id: int
    score_type: ScoreType | None = None


class CurrentUserAttributes(BaseModel):
    can_beatmap_update_owner: bool | None = None
    can_delete: bool | None = None
    can_edit_metadata: bool | None = None
    can_edit_tags: bool | None = None
    can_hype: bool | None = None
    can_hype_reason: str | None = None
    can_love: bool | None = None
    can_remove_from_loved: bool | None = None
    is_watching: bool | None = None
    new_hype_time: datetime | None = None
    nomination_modes: list[Gamemode] | None = None
    remaining_hype: int | None = None
    can_destroy: bool | None = None
    can_reopen: bool | None = None
    can_moderate_kudosu: bool | None = None
    can_resolve: bool | None = None
    vote_score: int | None = None
    can_message: bool | None = None
    can_message_error: str | None = None
    last_read_id: int | None = None
    can_new_comment: bool | None = None
    can_new_comment_reason: str | None = None
    pin: PinAttributes | None = None


class CursorModel(BaseModel):
    r"""NOTE: This model is not serializable by orjson directly.

    Use the provided .model_dump_json() or .model_dump() methods instead.
    """

    cursor_string: str | None = None
    next: Callable[[object, object], Awaitable[CursorModel]] | None = Field(
        default=None,
        exclude=True,
    )
    """Partial function to get the next page of results."""
