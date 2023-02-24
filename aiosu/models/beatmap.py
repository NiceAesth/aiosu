"""
This module contains models for Beatmap objects.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from enum import unique
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import Field
from pydantic import root_validator

from .base import BaseModel
from .common import CursorModel
from .gamemode import Gamemode
from .user import User

__all__ = (
    "Beatmap",
    "BeatmapAvailability",
    "BeatmapCovers",
    "BeatmapDifficultyAttributes",
    "BeatmapFailtimes",
    "BeatmapHype",
    "BeatmapNominations",
    "BeatmapRankStatus",
    "Beatmapset",
    "BeatmapsetDiscussion",
    "BeatmapsetDiscussionPost",
    "BeatmapsetDisscussionType",
    "BeatmapsetEvent",
    "BeatmapsetEventComment",
    "BeatmapsetEventType",
    "BeatmapsetRequestStatus",
    "BeatmapsetVoteEvent",
    "BeatmapUserPlaycount",
    "BeatmapsetDiscussionResponse",
    "BeatmapsetDiscussionPostResponse",
    "BeatmapsetDiscussionVoteResponse",
    "BeatmapsetSearchResponse",
)

BeatmapsetDisscussionType = Literal[
    "hype",
    "praise",
    "problem",
    "review",
    "suggestion",
    "mapper_note",
]


BeatmapsetEventType = Literal[
    "approve",
    "beatmap_owner_change",
    "discussion_delete",
    "discussion_post_delete",
    "discussion_post_restore",
    "discussion_restore",
    "discussion_lock",
    "discussion_unlock",
    "disqualify",
    "genre_edit",
    "issue_reopen",
    "issue_resolve",
    "kudosu_allow",
    "kudosu_deny",
    "kudosu_gain",
    "kudosu_lost",
    "kudosu_recalculate",
    "language_edit",
    "love",
    "nominate",
    "nomination_reset",
    "nomination_reset_received",
    "nsfw_toggle",
    "offset_edit",
    "qualify",
    "rank",
    "remove_from_loved",
]

BeatmapsetRequestStatus = Literal[
    "all",
    "ranked",
    "qualified",
    "disqualified",
    "never_ranked",
]

BEATMAP_RANK_STATUS_NAMES = {
    -2: "graveyard",
    -1: "wip",
    0: "pending",
    1: "ranked",
    2: "approved",
    3: "qualified",
    4: "loved",
}


@unique
class BeatmapRankStatus(Enum):
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4

    @property
    def id(self) -> int:
        return self.value

    @property
    def name_api(self) -> str:
        return BEATMAP_RANK_STATUS_NAMES[self.id]

    def __str__(self) -> str:
        return self.name_api

    @classmethod
    def _missing_(cls, query: object) -> Any:
        if isinstance(query, int):
            for status in list(BeatmapRankStatus):
                if status.id == query:
                    return status
        elif isinstance(query, str):
            for status in list(BeatmapRankStatus):
                if status.name_api == query.lower():
                    return status
        raise ValueError(f"BeatmapRankStatus {query} does not exist.")


class BeatmapAvailability(BaseModel):
    more_information: Optional[str]
    download_disabled: Optional[bool]

    @classmethod
    def _from_api_v1(cls, data: Any) -> BeatmapAvailability:
        return cls.parse_obj({"download_disabled": data["download_unavailable"]})


class BeatmapNominations(BaseModel):
    current: Optional[int]
    required: Optional[int]


class BeatmapCovers(BaseModel):
    cover: str
    card: str
    list: str
    slimcover: str
    cover_2_x: Optional[str] = Field(alias="cover@2x")
    card_2_x: Optional[str] = Field(alias="card@2x")
    list_2_x: Optional[str] = Field(alias="list@2x")
    slimcover_2_x: Optional[str] = Field(alias="slimcover@2x")

    @classmethod
    def from_beatmapset_id(cls, beatmapset_id: int) -> BeatmapCovers:
        base_url = "https://assets.ppy.sh/beatmaps/"
        return cls.parse_obj(
            {
                "cover": f"{base_url}{beatmapset_id}/covers/cover.jpg",
                "card": f"{base_url}{beatmapset_id}/covers/card.jpg",
                "list": f"{base_url}{beatmapset_id}/covers/list.jpg",
                "slimcover": f"{base_url}{beatmapset_id}/covers/slimcover.jpg",
                "cover_2_x": f"{base_url}{beatmapset_id}/covers/cover@2x.jpg",
                "card_2_x": f"{base_url}{beatmapset_id}/covers/card@2x.jpg",
                "list_2_x": f"{base_url}{beatmapset_id}/covers/list@2x.jpg",
                "slimcover_2_x": f"{base_url}{beatmapset_id}/covers/slimcover@2x.jpg",
            },
        )

    @classmethod
    def _from_api_v1(cls, data: Any) -> BeatmapCovers:
        return cls.from_beatmapset_id(data["beatmapset_id"])


class BeatmapHype(BaseModel):
    current: int
    required: int


class BeatmapFailtimes(BaseModel):
    exit: Optional[list[int]]
    fail: Optional[list[int]]


class BeatmapDifficultyAttributes(BaseModel):
    max_combo: int
    star_rating: float
    # osu standard
    aim_difficulty: Optional[float]
    approach_rate: Optional[float]  # osu catch + standard
    flashlight_difficulty: Optional[float]
    overall_difficulty: Optional[float]
    slider_factor: Optional[float]
    speed_difficulty: Optional[float]
    speed_note_count: Optional[float]
    # osu taiko
    stamina_difficulty: Optional[float]
    rhythm_difficulty: Optional[float]
    colour_difficulty: Optional[float]
    # osu mania
    great_hit_window: Optional[float]
    score_multiplier: Optional[float]


class Beatmap(BaseModel):
    id: int
    url: str
    mode: Gamemode
    beatmapset_id: int
    difficulty_rating: float
    status: BeatmapRankStatus
    total_length: int
    user_id: int
    version: str
    accuracy: Optional[float]
    ar: Optional[float]
    cs: Optional[float]
    bpm: Optional[float]
    convert: Optional[bool]
    count_circles: Optional[int]
    count_sliders: Optional[int]
    count_spinners: Optional[int]
    deleted_at: Optional[datetime]
    drain: Optional[float]
    hit_length: Optional[int]
    is_scoreable: Optional[bool]
    last_updated: Optional[datetime]
    passcount: Optional[int]
    play_count: Optional[int] = Field(None, alias="playcount")
    checksum: Optional[str]
    max_combo: Optional[int]
    beatmapset: Optional[Beatmapset]
    failtimes: Optional[BeatmapFailtimes]

    @root_validator(pre=True)
    def _set_url(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("url") is None:
            id = values["id"]
            beatmapset_id = values["beatmapset_id"]
            mode = Gamemode(values["mode"])
            values[
                "url"
            ] = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#{mode}/{id}"
        return values

    @property
    def discussion_url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.beatmapset_id}/discussion/{self.id}/general"

    @property
    def count_objects(self) -> int:
        """Total count of the objects.

        :raises ValueError: Raised if object counts are none
        :return: Sum of counts of all objects
        :rtype: int
        """
        if (
            self.count_circles is None
            or self.count_spinners is None
            or self.count_sliders is None
        ):
            raise ValueError("Beatmap contains no object count information.")
        return self.count_spinners + self.count_circles + self.count_sliders

    @classmethod
    def _from_api_v1(cls, data: Any) -> Beatmap:
        return cls.parse_obj(
            {
                "beatmapset_id": data["beatmapset_id"],
                "difficulty_rating": data["difficultyrating"],
                "id": data["beatmap_id"],
                "mode": int(data["mode"]),
                "status": int(data["approved"]),
                "total_length": data["total_length"],
                "hit_length": data["total_length"],
                "user_id": data["creator_id"],
                "version": data["version"],
                "accuracy": data["diff_overall"],
                "cs": data["diff_size"],
                "ar": data["diff_approach"],
                "drain": data["diff_drain"],
                "last_updated": data["last_update"],
                "bpm": data["bpm"],
                "checksum": data["file_md5"],
                "playcount": data["playcount"],
                "passcount": data["passcount"],
                "count_circles": data["count_normal"],
                "count_sliders": data["count_slider"],
                "count_spinners": data["count_spinner"],
                "max_combo": data["max_combo"],
            },
        )


class Beatmapset(BaseModel):
    id: int
    artist: str
    artist_unicode: str
    covers: BeatmapCovers
    creator: str
    favourite_count: int
    play_count: int = Field(alias="playcount")
    preview_url: str
    source: str
    status: BeatmapRankStatus
    title: str
    title_unicode: str
    user_id: int
    video: bool
    nsfw: Optional[bool]
    hype: Optional[BeatmapHype]
    availability: Optional[BeatmapAvailability]
    bpm: Optional[float]
    can_be_hyped: Optional[bool]
    discussion_enabled: Optional[bool]
    discussion_locked: Optional[bool]
    is_scoreable: Optional[bool]
    last_updated: Optional[datetime]
    legacy_thread_url: Optional[str]
    nominations_summary: Optional[BeatmapNominations]
    ranked_date: Optional[datetime]
    storyboard: Optional[bool]
    submitted_date: Optional[datetime]
    tags: Optional[str]
    ratings: Optional[list[int]]
    has_favourited: Optional[bool]
    beatmaps: Optional[list[Beatmap]]

    @property
    def url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.id}"

    @property
    def discussion_url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.id}/discussion"

    @classmethod
    def _from_api_v1(cls, data: Any) -> Beatmapset:
        return cls.parse_obj(
            {
                "id": data["beatmapset_id"],
                "artist": data["artist"],
                "artist_unicode": data["artist"],
                "covers": BeatmapCovers._from_api_v1(data),
                "favourite_count": data["favourite_count"],
                "creator": data["creator"],
                "play_count": data["playcount"],
                "preview_url": f"//b.ppy.sh/preview/{data['beatmapset_id']}.mp3",
                "source": data["source"],
                "status": int(data["approved"]),
                "title": data["title"],
                "title_unicode": data["title"],
                "user_id": data["creator_id"],
                "video": data["video"],
                "submitted_date": data["submit_date"],
                "ranked_date": data["approved_date"],
                "last_updated": data["last_update"],
                "tags": data["tags"],
                "storyboard": data["storyboard"],
                "availabiliy": BeatmapAvailability._from_api_v1(data),
                "beatmaps": [Beatmap._from_api_v1(data)],
            },
        )


class BeatmapsetSearchResponse(CursorModel):
    beatmapsets: list[Beatmapset]


class BeatmapUserPlaycount(BaseModel):
    count: int
    beatmap_id: int
    beatmap: Optional[Beatmap]
    beatmapset: Optional[Beatmapset]


class BeatmapsetDiscussionPost(BaseModel):
    id: int
    user_id: int
    system: bool
    message: str
    created_at: datetime
    beatmap_discussion_id: Optional[int]
    last_editor_id: Optional[int]
    deleted_by_id: Optional[int]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]


class BeatmapsetDiscussion(BaseModel):
    id: int
    beatmapset_id: int
    user_id: int
    message_type: BeatmapsetDisscussionType
    resolved: bool
    can_be_resolved: bool
    can_grant_kudosu: bool
    created_at: datetime
    beatmap_id: Optional[int]
    deleted_by_id: Optional[int]
    parent_id: Optional[int]
    timestamp: Optional[int]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    last_post_at: Optional[datetime]
    kudosu_denied: Optional[bool]
    starting_post: Optional[BeatmapsetDiscussionPost]


class BeatmapsetVoteEvent(BaseModel):
    score: int
    user_id: int
    id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    beatmapset_discussion_id: Optional[int]


class BeatmapsetEventComment(BaseModel):
    beatmap_discussion_id: Optional[int]
    beatmap_discussion_post_id: Optional[int]
    new_vote: Optional[BeatmapsetVoteEvent]
    votes: Optional[list[BeatmapsetVoteEvent]]
    mode: Optional[Gamemode]
    reason: Optional[str]
    source_user_id: Optional[int]
    source_user_username: Optional[str]
    nominator_ids: Optional[list[int]]
    new: Optional[str]
    old: Optional[str]
    new_user_id: Optional[int]
    new_user_username: Optional[str]


class BeatmapsetEvent(BaseModel):
    id: int
    type: BeatmapsetEventType
    r"""Information on types: https://github.com/ppy/osu-web/blob/master/resources/assets/lib/interfaces/beatmapset-event-json.ts"""
    created_at: datetime
    user_id: int
    beatmapset: Optional[Beatmapset]
    discussion: Optional[BeatmapsetDiscussion]
    comment: Optional[dict]


class BeatmapsetDiscussionResponse(CursorModel):
    beatmaps: list[Beatmap]
    discussions: list[BeatmapsetDiscussion]
    included_discussions: list[BeatmapsetDiscussion]
    users: list[User]
    max_blocks: int

    @root_validator(pre=True)
    def _set_max_blocks(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["max_blocks"] = values["reviews_config"]["max_blocks"]
        return values


class BeatmapsetDiscussionPostResponse(CursorModel):
    beatmapsets: list[Beatmapset]
    posts: list[BeatmapsetDiscussionPost]
    users: list[User]


class BeatmapsetDiscussionVoteResponse(CursorModel):
    votes: list[BeatmapsetVoteEvent]
    discussions: list[BeatmapsetDiscussion]
    users: list[User]


Beatmap.update_forward_refs()
