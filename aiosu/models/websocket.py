"""
This module contains models for osu!lazer WebSocket messages.
"""

from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import ConfigDict
from pydantic import ValidationInfo
from pydantic import field_validator

from .base import BaseModel
from .beatmap import BeatmapRankStatus
from .mods import Mods

__all__ = (
    "BeatmapStateWebSocketMessage",
    "OsuWebSocketMessage",
    "UserActivityWebSocketMessage",
    "WebSocketBeatmap",
    "WebSocketBeatmapDifficulty",
    "WebSocketBeatmapMetadata",
    "WebSocketInLobbyUserActivityData",
    "WebSocketWatchingReplayUserActivityData",
)


class OsuWebSocketMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class WebSocketBeatmapMetadata(BaseModel):
    artist: str
    artist_unicode: str
    title: str
    title_unicode: str
    author: str
    source: str
    tags: str
    user_tags: list[str]


class WebSocketBeatmapDifficulty(BaseModel):
    approach_rate: float
    circle_size: float
    overall_difficulty: float
    drain_rate: float


class WebSocketBeatmap(BaseModel):
    beatmap_id: int
    beatmapset_id: int
    beatmap_hash: str
    metadata: WebSocketBeatmapMetadata
    difficulty: WebSocketBeatmapDifficulty
    difficulty_name: str
    ruleset_id: int
    bpm: float
    star_rating: float
    maximum_pp: float
    max_combo: int
    status: BeatmapRankStatus | Literal["None", "LocallyModified"]
    total_length: int
    """The total length in milliseconds with mods applied"""
    drain_length: int
    """The drain length in milliseconds with mods applied"""
    object_count: int

    @field_validator("status", mode="before")
    @classmethod
    def _status_validate(cls, value: object) -> object:
        if value in ("None", "LocallyModified"):
            return value
        return BeatmapRankStatus(value)


class BeatmapStateWebSocketMessage(OsuWebSocketMessage):
    type: Literal["BeatmapStateWebSocketMessage"] = "BeatmapStateWebSocketMessage"
    beatmap: WebSocketBeatmap
    ruleset_id: int
    mods: Mods


class WebSocketInLobbyUserActivityData(BaseModel):
    room_id: int
    room_name: str


class WebSocketWatchingReplayUserActivityData(BaseModel):
    score_id: int
    user_id: int
    beatmap_id: int


class UserActivityWebSocketMessage(OsuWebSocketMessage):
    type: Literal["UserActivityWebSocketMessage"] = "UserActivityWebSocketMessage"
    status: str
    data: (
        WebSocketInLobbyUserActivityData
        | WebSocketWatchingReplayUserActivityData
        | dict[str, Any]
        | None
    ) = None

    @field_validator("data", mode="plain")
    @classmethod
    def _activity_validate(cls, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return None
        models: dict[str, type[BaseModel]] = {
            "InLobby": WebSocketInLobbyUserActivityData,
            "WatchingReplay": WebSocketWatchingReplayUserActivityData,
            "SpectatingUser": WebSocketWatchingReplayUserActivityData,
        }
        model = models.get(info.data.get("status", ""))
        if model is not None:
            return model.model_validate(value)
        if not isinstance(value, dict):
            raise ValueError("Activity data must be a dictionary.")
        return value
