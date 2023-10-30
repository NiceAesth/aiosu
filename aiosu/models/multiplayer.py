"""
This module contains models for multiplayer.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import Field
from pydantic import model_validator

from .base import BaseModel
from .beatmap import Beatmap
from .common import CursorModel
from .gamemode import Gamemode
from .lazer import LazerMod
from .lazer import LazerScoreStatistics
from .mods import Mods
from .user import User

__all__ = (
    "MultiplayerEvent",
    "MultiplayerEventType",
    "MultiplayerGame",
    "MultiplayerLeaderboardItem",
    "MultiplayerLeaderboardResponse",
    "MultiplayerMatch",
    "MultiplayerMatchResponse",
    "MultiplayerMatchesResponse",
    "MultiplayerQueueMode",
    "MultiplayerRoom",
    "MultiplayerRoomCategory",
    "MultiplayerRoomMode",
    "MultiplayerRoomTypeGroup",
    "MultiplayerRoomsResponse",
    "MultiplayerScore",
    "MultiplayerScoreSortType",
    "MultiplayerScoresAround",
    "MultiplayerScoresResponse",
    "MultiplayerScoringType",
    "MultiplayerTeamType",
)

MultiplayerScoringType = Literal["score", "accuracy", "combo", "scorev2"]
MultiplayerTeamType = Literal["head-to-head", "tag-coop", "team-vs", "tag-team-vs"]
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
MultiplayerRoomCategory = Literal["normal", "spotlight", "featured_artist"]
MultiplayerRoomTypeGroup = Literal["playlists", "realtime"]
MultiplayerQueueMode = Literal["host_only", "all_players", "all_players_round_robin"]


class MultiplayerScoresAround(BaseModel):
    higher: MultiplayerScoresResponse
    lower: MultiplayerScoresResponse


class MultiplayerScore(BaseModel):
    user_id: int
    rank: str
    accuracy: float
    max_combo: int
    mods: list[Union[Mods, LazerMod]]
    passed: bool
    statistics: LazerScoreStatistics
    id: Optional[int] = None
    room_id: Optional[int] = None
    user: Optional[User] = None
    beatmap_id: Optional[int] = None
    playlist_item_id: Optional[int] = None
    position: Optional[int] = None
    total_score: Optional[int] = None
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


class MultiplayerGame(BaseModel):
    id: int
    start_time: datetime
    mode: Gamemode
    scoring_type: MultiplayerScoringType
    team_type: MultiplayerTeamType
    mods: list[Union[Mods, LazerMod]]
    beatmap_id: int
    scores: list[MultiplayerScore]
    beatmap: Optional[Beatmap] = None
    end_time: Optional[datetime] = None


class MultiplayerEvent(BaseModel):
    id: int
    timestamp: datetime
    type: MultiplayerEventType
    user_id: Optional[int] = None
    game: Optional[MultiplayerGame] = None

    @model_validator(mode="before")
    @classmethod
    def _set_type(cls, values: dict[str, object]) -> dict[str, object]:
        if "detail" in values and isinstance(values["detail"], Mapping):
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
