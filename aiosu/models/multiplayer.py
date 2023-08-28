"""
This module contains models for multiplayer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import Field
from pydantic import model_validator

from .base import BaseModel
from .beatmap import Beatmap
from .common import CursorModel
from .gamemode import Gamemode
from .lazer import LazerMod
from .lazer import LazerScoreStatistics
from .user import User

__all__ = (
    "MultiplayerScoreSortType",
    "MultiplayerScoresResponse",
    "MultiplayerScore",
    "MultiplayerScoresAround",
    "MultiplayerMatch",
    "MultiplayerEventType",
    "MultiplayerEvent",
    "MultiplayerMatchResponse",
    "MultiplayerMatchesResponse",
    "MultiplayerRoomMode",
    "MultiplayerRoom",
    "MultiplayerRoomsResponse",
    "MultiplayerRoomCategory",
    "MultiplayerRoomTypeGroup",
    "MultiplayerLeaderboardResponse",
    "MultiplayerLeaderboardItem",
    "MultiplayerQueueMode",
)

MultiplayerScoreSortType = Literal["score_asc", "score_desc"]
MultiplayerEventType = Literal[
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
    "other",
]
MultiplayerRoomMode = Literal["owned", "participated", "ended"]
MultiplayerRoomCategory = Literal["normal", "spotlight", "featured_artists"]
MultiplayerRoomTypeGroup = Literal["playlists", "realtime"]
MultiplayerQueueMode = Literal["host_only", "all_players", "all_players_round_robin"]


class MultiplayerScoresAround(BaseModel):
    higher: MultiplayerScoresResponse
    lower: MultiplayerScoresResponse


class MultiplayerScore(BaseModel):
    id: int
    user_id: int
    room_id: int
    playlist_item_id: int
    beatmap_id: int
    rank: str
    total_score: int
    accuracy: float
    max_combo: int
    mods: list[LazerMod]
    passed: bool
    user: User
    statistics: LazerScoreStatistics
    position: Optional[int] = None
    scores_around: Optional[MultiplayerScoresAround] = None


class MultiplayerScoresResponse(CursorModel):
    scores: list[MultiplayerScore]
    user_score: Optional[MultiplayerScore] = None
    total: Optional[int] = None


class MultiplayerMatch(BaseModel):
    id: int
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None


class MultiplayerEvent(BaseModel):
    id: int
    timestamp: datetime
    type: MultiplayerEventType
    user_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
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
    current_game_id: Optional[int] = None


class MultiplayerMatchesResponse(CursorModel):
    matches: list[MultiplayerMatch]


class MultiplayerPlaylistItem(BaseModel):
    id: int
    room_id: int
    beatmap_id: int
    mode: Gamemode = Field(alias="ruleset_id")
    allowed_mods: list[LazerMod]
    required_mods: list[LazerMod]
    expired: bool
    owner_id: int
    beatmap: Beatmap
    playlist_order: Optional[int] = None
    played_at: Optional[datetime] = None


class MultiplayerRoom(BaseModel):
    id: int
    name: str
    category: MultiplayerRoomCategory
    type: MultiplayerRoomTypeGroup
    user_id: int
    channel_id: int
    active: bool
    has_password: bool
    auto_skip: bool
    host: User
    queue_mode: MultiplayerQueueMode
    playlist: list[MultiplayerPlaylistItem]
    recent_participants: list[User]
    participant_count: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    max_attempts: Optional[int] = None


class MultiplayerLeaderboardItem(BaseModel):
    accuracy: float
    attempts: int
    completed: int
    pp: float
    room_id: int
    total_score: int
    user_id: int
    user: User
    position: Optional[int] = None


class MultiplayerLeaderboardResponse(BaseModel):
    leaderboard: list[MultiplayerLeaderboardItem]
    user_score: Optional[MultiplayerLeaderboardItem] = None


class MultiplayerRoomsResponse(CursorModel):
    """Currently unused. Relevant for api-version >= 99999999"""

    rooms: list[MultiplayerRoom]


MultiplayerScoresAround.model_rebuild()
