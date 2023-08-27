"""
This module contains models for miscellaneous objects.
"""
from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import Any
from typing import Coroutine
from typing import Literal
from typing import Optional

from emojiflags.lookup import lookup as flag_lookup  # type: ignore
from pydantic import computed_field
from pydantic import Field
from pydantic import field_validator

from .base import BaseModel
from .gamemode import Gamemode

__all__ = (
    "Achievement",
    "Country",
    "CurrentUserAttributes",
    "TimestampedCount",
    "CursorModel",
    "SortType",
    "ScoreType",
    "BeatmapScoreboardType",
    "HTMLBody",
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
]
BeatmapScoreboardType = Literal["global", "country", "friend"]


class TimestampedCount(BaseModel):
    start_date: datetime
    count: int

    @field_validator("start_date", mode="before")
    @classmethod
    def _date_validate(cls, v: Any) -> Any:
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d")
        return v


class Achievement(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    grouping: str
    icon_url: str
    ordering: int
    mode: Optional[Gamemode] = None
    instructions: Optional[str] = None


class Country(BaseModel):
    code: str
    name: str

    @computed_field  # type: ignore
    @property
    def flag_emoji(self) -> str:
        r"""Emoji for the flag.

        :return: Unicode emoji representation of the country's flag
        :rtype: str
        """
        return flag_lookup(self.code)


class HTMLBody(BaseModel):
    html: str
    raw: Optional[str] = None
    bbcode: Optional[str] = None


class PinAttributes(BaseModel):
    is_pinned: bool
    score_id: int
    score_type: ScoreType


class CurrentUserAttributes(BaseModel):
    can_beatmap_update_owner: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_edit_metadata: Optional[bool] = None
    can_edit_tags: Optional[bool] = None
    can_hype: Optional[bool] = None
    can_hype_reason: Optional[str] = None
    can_love: Optional[bool] = None
    can_remove_from_loved: Optional[bool] = None
    is_watching: Optional[bool] = None
    new_hype_time: Optional[datetime] = None
    nomination_modes: Optional[list[Gamemode]] = None
    remaining_hype: Optional[int] = None
    can_destroy: Optional[bool] = None
    can_reopen: Optional[bool] = None
    can_moderate_kudosu: Optional[bool] = None
    can_resolve: Optional[bool] = None
    vote_score: Optional[int] = None
    can_message: Optional[bool] = None
    can_message_error: Optional[str] = None
    last_read_id: Optional[int] = None
    can_new_comment: Optional[bool] = None
    can_new_comment_reason: Optional[str] = None
    pin: Optional[PinAttributes] = None


class CursorModel(BaseModel):
    r"""NOTE: This model is not serializable by orjson directly.

    Use the provided .model_dump_json() or .model_dump() methods instead.
    """

    cursor_string: Optional[str] = None
    next: Optional[partial[Coroutine[Any, Any, CursorModel]]] = Field(
        default=None,
        exclude=True,
    )
    """Partial function to get the next page of results."""
