"""
This module contains models for the referee API.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import BaseModel

__all__ = (
    "RefereeAddPlaylistItemRequest",
    "RefereeAddedEvent",
    "RefereeChangeRoomSettingsRequest",
    "RefereeCountdownStartedEvent",
    "RefereeCountdownStoppedEvent",
    "RefereeCountdownType",
    "RefereeEditCurrentPlaylistItemRequest",
    "RefereeEditPlaylistItemRequest",
    "RefereeEvent",
    "RefereeInvitedEvent",
    "RefereeListRoomsResponse",
    "RefereeMakeRoomRequest",
    "RefereeMatchAbortedEvent",
    "RefereeMatchCompletedEvent",
    "RefereeMatchStartedEvent",
    "RefereeMatchState",
    "RefereeMatchStateChangedEvent",
    "RefereeMatchTeam",
    "RefereeMatchType",
    "RefereeMod",
    "RefereeMoveUserRequest",
    "RefereePlayer",
    "RefereePlayerStyle",
    "RefereePlaylistItem",
    "RefereePlaylistItemAddedEvent",
    "RefereePlaylistItemChangedEvent",
    "RefereePlaylistItemRemovedEvent",
    "RefereeRemovePlaylistItemRequest",
    "RefereeRemovedEvent",
    "RefereeRollCompletedEvent",
    "RefereeRollRequest",
    "RefereeRoomJoinedResponse",
    "RefereeRoomSettingsChangedEvent",
    "RefereeSetLockStateRequest",
    "RefereeStartGameplayRequest",
    "RefereeUser",
    "RefereeUserBannedEvent",
    "RefereeUserJoinedEvent",
    "RefereeUserKickedEvent",
    "RefereeUserLeftEvent",
    "RefereeUserModsChangedEvent",
    "RefereeUserStatus",
    "RefereeUserStatusChangedEvent",
    "RefereeUserStyleChangedEvent",
    "RefereeUserTeamChangedEvent",
)


RefereeCountdownType = Literal["match_start", "server_shutting_down"]
RefereeMatchTeam = Literal["red", "blue"]
RefereeMatchType = Literal["head_to_head", "team_versus"]
RefereeUserStatus = Literal["idle", "ready", "playing", "finished_play", "spectating"]


class RefereeMod(BaseModel):
    acronym: str
    settings: dict[str, str | int | float | bool | None] | None = None


class RefereeMatchState(BaseModel):
    type: RefereeMatchType
    locked: bool
    slots: list[int | None] | None = None


class RefereePlayerStyle(BaseModel):
    ruleset_id: int | None = None
    beatmap_id: int | None = None


class RefereePlayer(BaseModel):
    user_id: int
    status: RefereeUserStatus
    style: RefereePlayerStyle = Field(default_factory=RefereePlayerStyle)
    mods: list[RefereeMod] = Field(default_factory=list)
    team: RefereeMatchTeam | None = None


class RefereeUser(BaseModel):
    user_id: int


class RefereePlaylistItem(BaseModel):
    id: int
    ruleset_id: int
    beatmap_id: int
    required_mods: list[RefereeMod] = Field(default_factory=list)
    allowed_mods: list[RefereeMod] = Field(default_factory=list)
    freestyle: bool
    was_played: bool
    order: int


class RefereeMakeRoomRequest(BaseModel):
    ruleset_id: int
    beatmap_id: int
    name: str
    max_participants: int = 0


class RefereeChangeRoomSettingsRequest(BaseModel):
    name: str | None = None
    password: str | None = None
    type: RefereeMatchType | None = None
    max_participants: int | None = None


class RefereeAddPlaylistItemRequest(BaseModel):
    ruleset_id: int
    beatmap_id: int
    required_mods: list[RefereeMod] = Field(default_factory=list)
    allowed_mods: list[RefereeMod] = Field(default_factory=list)
    freestyle: bool = False


class RefereeEditCurrentPlaylistItemRequest(BaseModel):
    ruleset_id: int | None = None
    beatmap_id: int | None = None
    required_mods: list[RefereeMod] | None = None
    allowed_mods: list[RefereeMod] | None = None
    freestyle: bool | None = None


class RefereeEditPlaylistItemRequest(RefereeEditCurrentPlaylistItemRequest):
    playlist_item_id: int


class RefereeRemovePlaylistItemRequest(BaseModel):
    playlist_item_id: int


class RefereeRollRequest(BaseModel):
    max: int | None = None


class RefereeMoveUserRequest(BaseModel):
    user_id: int
    slot: int | None = None
    team: RefereeMatchTeam | None = None


class RefereeSetLockStateRequest(BaseModel):
    locked: bool


class RefereeStartGameplayRequest(BaseModel):
    countdown: int | None = None


class RefereeListRoomsResponse(BaseModel):
    room_ids: list[int] = Field(default_factory=list)


class RefereeRoomJoinedResponse(BaseModel):
    room_id: int
    chat_channel_id: int
    name: str
    password: str
    max_participants: int = 0
    state: RefereeMatchState
    playlist: list[RefereePlaylistItem] = Field(default_factory=list)
    players: list[RefereePlayer] = Field(default_factory=list)
    referees: list[RefereeUser] = Field(default_factory=list)


class RefereeEvent(BaseModel):
    room_id: int


class RefereeUserJoinedEvent(RefereeEvent):
    user_id: int


class RefereeUserLeftEvent(RefereeEvent):
    user_id: int


class RefereeUserKickedEvent(RefereeEvent):
    kicked_user_id: int
    kicking_user_id: int


class RefereeUserBannedEvent(RefereeEvent):
    banned_user_id: int
    banning_user_id: int


class RefereeAddedEvent(RefereeEvent):
    user_id: int


class RefereeRemovedEvent(RefereeEvent):
    user_id: int


class RefereeInvitedEvent(RefereeEvent):
    pass


class RefereeRoomSettingsChangedEvent(RefereeEvent):
    name: str
    password: str
    type: RefereeMatchType
    playlist_item_id: int
    max_participants: int | None = None


class RefereeMatchStateChangedEvent(RefereeEvent):
    state: RefereeMatchState


class RefereePlaylistItemAddedEvent(RefereeEvent):
    playlist_item: RefereePlaylistItem


class RefereePlaylistItemChangedEvent(RefereeEvent):
    playlist_item: RefereePlaylistItem


class RefereePlaylistItemRemovedEvent(RefereeEvent):
    playlist_item_id: int


class RefereeRollCompletedEvent(RefereeEvent):
    user_id: int
    max: int
    result: int


class RefereeUserStatusChangedEvent(RefereeEvent):
    user_id: int
    status: RefereeUserStatus


class RefereeUserModsChangedEvent(RefereeEvent):
    user_id: int
    mods: list[RefereeMod]


class RefereeUserStyleChangedEvent(RefereeEvent):
    user_id: int
    beatmap_id: int | None = None
    ruleset_id: int | None = None


class RefereeUserTeamChangedEvent(RefereeEvent):
    user_id: int
    team: RefereeMatchTeam | None = None


class RefereeCountdownStoppedEvent(RefereeEvent):
    countdown_id: int
    type: RefereeCountdownType


class RefereeCountdownStartedEvent(RefereeEvent):
    countdown_id: int
    type: RefereeCountdownType
    seconds: float


class RefereeMatchAbortedEvent(RefereeEvent):
    playlist_item_id: int


class RefereeMatchCompletedEvent(RefereeEvent):
    playlist_item_id: int


class RefereeMatchStartedEvent(RefereeEvent):
    playlist_item_id: int
    type: RefereeMatchType
    teams: dict[int, RefereeMatchTeam] | None = None
    slots: dict[int, int] | None = None
