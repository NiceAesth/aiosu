"""
This module contains models for API events.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING

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
    "EventUser",
    "EventType",
    "EventResponse",
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
    previous_username: Optional[str] = Field(default=None, alias="previousUsername")


class Event(BaseModel):
    created_at: datetime
    id: int
    type: EventType
    r"""Information on types: https://github.com/ppy/osu-web/blob/master/resources/assets/lib/interfaces/event-json.ts"""
    parse_error: Optional[bool] = None
    achievement: Optional[Achievement] = None
    user: Optional[EventUser] = None
    beatmap: Optional[EventBeatmap] = None
    beatmapset: Optional[EventBeatmapset] = None
    approval: Optional[BeatmapRankStatus] = None
    count: Optional[int] = None
    rank: Optional[int] = None
    mode: Optional[Gamemode] = None
    score_rank: Optional[str] = Field(default=None, alias="scoreRank")


class EventResponse(CursorModel):
    events: list[Event]
