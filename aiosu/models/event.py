"""
This module contains models for API events.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import root_validator

from .base import BaseModel
from .beatmap import BeatmapRankStatus
from .common import Achievement
from .gamemode import Gamemode

if TYPE_CHECKING:
    from typing import Any

__all__ = (
    "Event",
    "EventBeatmap",
    "EventBeatmapset",
    "EventUser",
    "EventType",
)

EventType = Literal[
    "achievement",
    "beatmapPlaycount",
    "beatmapsetApprove",
    "beatmapsetDelete",
    "beatmapsetRevive",
    "beatmapsetUpdate",
    "beatmapsetUpload",
    "rank",
    "rankLost",
    "usernameChange",
    "userSupportAgain",
    "userSupportFirst",
    "userSupportGift",
]


class EventBeatmap(BaseModel):
    title: str
    url: str


class EventBeatmapset(BaseModel):
    title: str
    url: str


class EventUser(BaseModel):
    username: str
    url: str
    previous_username: Optional[str]

    @root_validator(pre=True)
    def _rename_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        if previous_username := values.pop("previousUsername", None):
            values["previous_username"] = previous_username
        return values


class Event(BaseModel):
    created_at: datetime
    id: int
    type: EventType
    r"""Information on types: https://github.com/ppy/osu-web/blob/master/resources/assets/lib/interfaces/event-json.ts"""
    parse_error: Optional[bool]
    achievment: Optional[Achievement]
    user: Optional[EventUser]
    beatmap: Optional[EventBeatmap]
    beatmapset: Optional[EventBeatmapset]
    approval: Optional[BeatmapRankStatus]
    count: Optional[int]
    rank: Optional[int]
    mode: Optional[Gamemode]
    score_rank: Optional[str]

    @root_validator(pre=True)
    def _rename_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        if score_rank := values.pop("scoreRank", None):
            values["score_rank"] = score_rank
        return values
