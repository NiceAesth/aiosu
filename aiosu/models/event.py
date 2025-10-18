"""
This module contains models for API events.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from typing import Literal

from pydantic import Field

from .base import BaseModel
from .beatmap import BeatmapRankStatus
from .common import Achievement
from .common import CursorModel
from .gamemode import Gamemode

if TYPE_CHECKING:
    pass

__all__ = (
    "Event",
    "EventBeatmap",
    "EventBeatmapset",
    "EventResponse",
    "EventType",
    "EventUser",
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
    previous_username: str | None = Field(default=None, alias="previousUsername")


class Event(BaseModel):
    created_at: datetime
    id: int
    type: EventType
    r"""Information on types: https://github.com/ppy/osu-web/blob/master/resources/js/interfaces/event-json.ts"""
    parse_error: bool | None = None
    achievement: Achievement | None = None
    user: EventUser | None = None
    beatmap: EventBeatmap | None = None
    beatmapset: EventBeatmapset | None = None
    approval: BeatmapRankStatus | None = None
    count: int | None = None
    rank: int | None = None
    mode: Gamemode | None = None
    score_rank: str | None = Field(default=None, alias="scoreRank")


class EventResponse(CursorModel):
    events: list[Event]
