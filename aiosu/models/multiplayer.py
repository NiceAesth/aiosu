"""
This module contains models for multiplayer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import root_validator

from .base import BaseModel
from .common import CursorModel
from .mods import Mods
from .score import ScoreStatistics
from .user import User

__all__ = (
    "MultiplayerScoreSortType",
    "MultiplayerScoresResponse",
    "MultiplayerScore",
    "MultiplayerScoresAround",
    "MultiplayerMatch",
    "MultiplayerEventTypes",
    "MultiplayerEvent",
    "MultiplayerMatchResponse",
    "MultiplayerMatchesResponse",
)

MultiplayerScoreSortType = Literal["score_asc", "score_desc"]
MultiplayerEventTypes = Literal[
    "match-created",
    "match-disbanded",
    "host-changed",
    "player-joined",
    "player-left",
    "player-kicked",
    "match-created-no-user",
    "match-disbanded-no-user",
    "host-changed-no-user",
    "player-joined-no-user",
    "player-left-no-user",
    "player-kicked-no-user",
]


class MultiplayerScoresAround(BaseModel):
    higher: MultiplayerScoresResponse
    lower: MultiplayerScoresResponse


class MultiplayerScore(BaseModel):
    id: int
    user_id: int
    room_id: int
    playlist_team_id: int
    beatmap_id: int
    rank: str
    total_score: int
    accuracy: float
    max_combo: int
    mods: Mods
    passed: bool
    user: User
    statistics: ScoreStatistics
    position: Optional[int]
    scores_around: Optional[MultiplayerScoresAround]


class MultiplayerScoresResponse(CursorModel):
    scores: list[MultiplayerScore]
    user_score: Optional[MultiplayerScore]
    total: Optional[int]


class MultiplayerMatch(BaseModel):
    id: int
    name: str
    start_time: datetime
    end_time: Optional[datetime]


class MultiplayerEvent(BaseModel):
    id: int
    timestamp: datetime
    type: MultiplayerEventTypes
    user_id: Optional[int]

    @root_validator(pre=True)
    def _set_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "detail" in values:
            values["type"] = values["detail"]["type"]
        return values


class MultiplayerMatchResponse(BaseModel):
    match: MultiplayerMatch
    events: list[MultiplayerEvent]
    users: list[User]
    first_event_id: int
    latest_event_id: int
    current_game_id: Optional[int]


class MultiplayerMatchesResponse(CursorModel):
    matches: list[MultiplayerMatch]


MultiplayerScoresAround.update_forward_refs()
