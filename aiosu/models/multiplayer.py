"""
This module contains models for multiplayer.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import Field
from pydantic import model_validator

from .base import BaseModel
from .beatmap import Beatmap
from .common import CursorModel
from .gamemode import Gamemode
from .lazer import LazerMod
from .lazer import LazerScore
from .mods import Mods
from .score import Score
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
    "MultiplayerRoomGroupType",
    "MultiplayerRoomMode",
    "MultiplayerRoomsResponse",
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
MultiplayerRoomGroupType = Literal["playlists", "realtime"]
MultiplayerQueueMode = Literal["host_only", "all_players", "all_players_round_robin"]


class MultiplayerScoresAround(BaseModel):
    higher: MultiplayerScoresResponse
    lower: MultiplayerScoresResponse


class MultiplayerScoresResponse(CursorModel):
    scores: list[LazerScore]
    user_score: LazerScore | None = None
    total: int | None = None


class MultiplayerMatch(BaseModel):
    id: int
    name: str
    start_time: datetime
    end_time: datetime | None = None


class MultiplayerGame(BaseModel):
    id: int
    start_time: datetime
    mode: Gamemode
    scoring_type: MultiplayerScoringType
    team_type: MultiplayerTeamType
    mods: list[Mods | LazerMod]
    beatmap_id: int
    scores: list[Score]
    beatmap: Beatmap | None = None
    end_time: datetime | None = None


class MultiplayerEvent(BaseModel):
    id: int
    timestamp: datetime
    type: MultiplayerEventType
    user_id: int | None = None
    game: MultiplayerGame | None = None

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
    current_game_id: int | None = None


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
    playlist_order: int | None = None
    played_at: datetime | None = None


class MultiplayerRoom(BaseModel):
    id: int
    name: str
    category: MultiplayerRoomCategory
    type: MultiplayerRoomGroupType
    user_id: int
    channel_id: int
    active: bool
    has_password: bool
    auto_skip: bool
    host: User
    queue_mode: MultiplayerQueueMode
    playlist: list[MultiplayerPlaylistItem]
    recent_participants: list[User]
    participant_count: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_attempts: int | None = None


class MultiplayerLeaderboardItem(BaseModel):
    accuracy: float
    attempts: int
    completed: int
    pp: float
    room_id: int
    total_score: int
    user_id: int
    user: User
    position: int | None = None


class MultiplayerLeaderboardResponse(BaseModel):
    leaderboard: list[MultiplayerLeaderboardItem]
    user_score: MultiplayerLeaderboardItem | None = None


class MultiplayerRoomsResponse(CursorModel):
    """Currently unused. Relevant for api-version >= 99999999"""

    rooms: list[MultiplayerRoom]
