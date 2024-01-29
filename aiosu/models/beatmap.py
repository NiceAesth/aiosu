"""
This module contains models for Beatmap objects.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from enum import unique
from functools import cached_property
from typing import Literal
from typing import Optional

from pydantic import computed_field
from pydantic import Field
from pydantic import model_validator

from .base import BaseModel
from .base import cast_int
from .common import CurrentUserAttributes
from .common import CursorModel
from .gamemode import Gamemode
from .user import User

__all__ = (
    "Beatmap",
    "BeatmapAvailability",
    "BeatmapCovers",
    "BeatmapDescription",
    "BeatmapDifficultyAttributes",
    "BeatmapFailtimes",
    "BeatmapGenre",
    "BeatmapHype",
    "BeatmapLanguage",
    "BeatmapNominations",
    "BeatmapPack",
    "BeatmapPackType",
    "BeatmapPackUserCompletion",
    "BeatmapPacksResponse",
    "BeatmapRankStatus",
    "BeatmapUserPlaycount",
    "Beatmapset",
    "BeatmapsetBundleFilterType",
    "BeatmapsetCategory",
    "BeatmapsetDiscussion",
    "BeatmapsetDiscussionPost",
    "BeatmapsetDiscussionPostResponse",
    "BeatmapsetDiscussionResponse",
    "BeatmapsetDiscussionVoteResponse",
    "BeatmapsetDiscussionVoteScoreType",
    "BeatmapsetDisscussionType",
    "BeatmapsetEvent",
    "BeatmapsetEventComment",
    "BeatmapsetEventType",
    "BeatmapsetGenre",
    "BeatmapsetLanguage",
    "BeatmapsetRequestStatus",
    "BeatmapsetSearchResponse",
    "BeatmapsetSortType",
    "BeatmapsetVoteEvent",
    "UserBeatmapType",
)

BeatmapsetSortType = Literal[
    "title_asc",
    "title_desc",
    "artist_asc",
    "artist_desc",
    "difficulty_asc",
    "difficulty_desc",
    "ranked_asc",
    "ranked_desc",
    "rating_asc",
    "rating_desc",
    "plays_asc",
    "plays_desc",
    "favourites_asc",
    "favourites_desc",
]

BeatmapsetCategory = Literal[
    "any",
    "leaderboard",
    "ranked",
    "qualified",
    "loved",
    "favourites",
    "pending",
    "wip",
    "graveyard",
    "mine",
]

BeatmapsetBundleFilterType = Literal[
    "any",
    "currently",
    "previously",
    "never",
]

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

BeatmapsetDiscussionVoteScoreType = Literal[
    "1",
    "-1",
]

UserBeatmapType = Literal["favourite", "graveyard", "loved", "ranked", "pending"]

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
class BeatmapsetGenre(Enum):
    UNSPECIFIED = 1
    VIDEO_GAME = 2
    ANIME = 3
    ROCK = 4
    POP = 5
    OTHER = 6
    NOVELTY = 7
    HIP_HOP = 9
    ELECTRONIC = 10
    METAL = 11
    CLASSICAL = 12
    FOLK = 13
    JAZZ = 14

    @classmethod
    def _missing_(cls, _: object) -> BeatmapsetGenre:
        return BeatmapsetGenre.UNSPECIFIED


@unique
class BeatmapsetLanguage(Enum):
    UNSPECIFIED = 1
    ENGLISH = 2
    JAPANESE = 3
    CHINESE = 4
    INSTRUMENTAL = 5
    KOREAN = 6
    FRENCH = 7
    GERMAN = 8
    SWEDISH = 9
    SPANISH = 10
    ITALIAN = 11
    RUSSIAN = 12
    POLISH = 13
    OTHER = 14

    @classmethod
    def _missing_(cls, _: object) -> BeatmapsetLanguage:
        return BeatmapsetLanguage.UNSPECIFIED


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
    def _missing_(cls, query: object) -> BeatmapRankStatus:
        if isinstance(query, int):
            for status in list(BeatmapRankStatus):
                if status.id == query:
                    return status
        elif isinstance(query, str):
            for status in list(BeatmapRankStatus):
                if status.name_api == query.lower():
                    return status
        raise ValueError(f"BeatmapRankStatus {query} does not exist.")


@unique
class BeatmapPackType(Enum):
    STANDARD = ("S", "Standard")
    FEATURED = ("F", "Featured Artist")
    TOURNAMENT = ("P", "Tournament")
    LOVED = ("L", "Project Loved")
    CHART = ("R", "Spotlights")
    THEME = ("T", "Theme")
    ARTIST = ("A", "Artist/Album")

    def __init__(self, tag: str, description: str) -> None:
        self.tag = tag
        self.description = description

    @classmethod
    def from_tag(cls, tag: str) -> BeatmapPackType:
        beatmap_pack_type = next((x for x in cls if x.tag == tag), None)
        if beatmap_pack_type is None:
            raise ValueError(f"BeatmapPackType {tag} does not exist.")
        return beatmap_pack_type

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def _missing_(cls, query: object) -> BeatmapPackType:
        if isinstance(query, cls):
            return query
        if isinstance(query, str):
            query = query.upper()
            try:
                return BeatmapPackType[query]
            except KeyError:
                return cls.from_tag(query)

        raise ValueError(f"BeatmapPackType {query} does not exist.")


class BeatmapDescription(BaseModel):
    bbcode: Optional[str] = None
    description: Optional[str] = None


class BeatmapGenre(BaseModel):
    name: str
    id: Optional[int] = None


class BeatmapLanguage(BaseModel):
    name: str
    id: Optional[int] = None


class BeatmapAvailability(BaseModel):
    more_information: Optional[str] = None
    download_disabled: Optional[bool] = None

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> BeatmapAvailability:
        return cls.model_validate({"download_disabled": data["download_unavailable"]})


class BeatmapNominations(BaseModel):
    current: Optional[int] = None
    required: Optional[int] = None


class BeatmapNomination(BaseModel):
    beatmapset_id: int
    reset: bool
    user_id: int
    rulesets: Optional[list[Gamemode]] = None


class BeatmapCovers(BaseModel):
    cover: str
    card: str
    list: str
    slimcover: str
    cover_2_x: Optional[str] = Field(default=None, alias="cover@2x")
    card_2_x: Optional[str] = Field(default=None, alias="card@2x")
    list_2_x: Optional[str] = Field(default=None, alias="list@2x")
    slimcover_2_x: Optional[str] = Field(default=None, alias="slimcover@2x")

    @classmethod
    def from_beatmapset_id(cls, beatmapset_id: int) -> BeatmapCovers:
        base_url = "https://assets.ppy.sh/beatmaps/"
        return cls.model_validate(
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
    def _from_api_v1(cls, data: Mapping[str, object]) -> BeatmapCovers:
        return cls.from_beatmapset_id(cast_int(data["beatmapset_id"]))


class BeatmapHype(BaseModel):
    current: int
    required: int


class BeatmapFailtimes(BaseModel):
    exit: Optional[list[int]] = None
    fail: Optional[list[int]] = None


class BeatmapDifficultyAttributes(BaseModel):
    max_combo: int
    star_rating: float
    # osu standard
    aim_difficulty: Optional[float] = None
    approach_rate: Optional[float] = None  # osu catch + standard
    flashlight_difficulty: Optional[float] = None
    overall_difficulty: Optional[float] = None
    slider_factor: Optional[float] = None
    speed_difficulty: Optional[float] = None
    speed_note_count: Optional[float] = None
    # osu taiko
    stamina_difficulty: Optional[float] = None
    rhythm_difficulty: Optional[float] = None
    colour_difficulty: Optional[float] = None
    # osu mania
    great_hit_window: Optional[float] = None
    score_multiplier: Optional[float] = None


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
    accuracy: Optional[float] = None
    ar: Optional[float] = None
    cs: Optional[float] = None
    bpm: Optional[float] = None
    convert: Optional[bool] = None
    count_circles: Optional[int] = None
    count_sliders: Optional[int] = None
    count_spinners: Optional[int] = None
    deleted_at: Optional[datetime] = None
    drain: Optional[float] = None
    hit_length: Optional[int] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[datetime] = None
    passcount: Optional[int] = None
    play_count: Optional[int] = Field(default=None, alias="playcount")
    checksum: Optional[str] = None
    max_combo: Optional[int] = None
    beatmapset: Optional[Beatmapset] = None
    failtimes: Optional[BeatmapFailtimes] = None

    @property
    def discussion_url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.beatmapset_id}/discussion/{self.id}/general"

    @computed_field  # type: ignore
    @cached_property
    def count_objects(self) -> Optional[int]:
        """Total count of the objects.

        :return: Sum of counts of all objects. None if no object count information.
        :rtype: Optional[int]
        """
        if (
            self.count_circles is None
            or self.count_spinners is None
            or self.count_sliders is None
        ):
            return None
        return self.count_spinners + self.count_circles + self.count_sliders

    @model_validator(mode="before")
    @classmethod
    def _set_url(cls, values: dict[str, object]) -> dict[str, object]:
        if values.get("url") is None:
            id = values["id"]
            beatmapset_id = values["beatmapset_id"]
            mode = Gamemode(values["mode"])
            values["url"] = (
                f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#{mode}/{id}"
            )
        return values

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> Beatmap:
        return cls.model_validate(
            {
                "beatmapset_id": data["beatmapset_id"],
                "difficulty_rating": data["difficultyrating"],
                "id": data["beatmap_id"],
                "mode": cast_int(data["mode"]),
                "status": cast_int(data["approved"]),
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
    nsfw: Optional[bool] = None
    hype: Optional[BeatmapHype] = None
    availability: Optional[BeatmapAvailability] = None
    bpm: Optional[float] = None
    can_be_hyped: Optional[bool] = None
    discussion_enabled: Optional[bool] = None
    discussion_locked: Optional[bool] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[datetime] = None
    legacy_thread_url: Optional[str] = None
    nominations: Optional[BeatmapNominations] = None
    current_nominations: Optional[list[BeatmapNomination]] = None
    ranked_date: Optional[datetime] = None
    storyboard: Optional[bool] = None
    submitted_date: Optional[datetime] = None
    tags: Optional[str] = None
    pack_tags: Optional[list[str]] = None
    track_id: Optional[int] = None
    user: Optional[User] = None
    related_users: Optional[list[User]] = None
    current_user_attributes: Optional[CurrentUserAttributes] = None
    description: Optional[BeatmapDescription] = None
    genre: Optional[BeatmapGenre] = None
    language: Optional[BeatmapLanguage] = None
    ratings: Optional[list[int]] = None
    recent_favourites: Optional[list[User]] = None
    discussions: Optional[list[BeatmapsetDiscussion]] = None
    events: Optional[list[BeatmapsetEvent]] = None
    has_favourited: Optional[bool] = None
    beatmaps: Optional[list[Beatmap]] = None
    converts: Optional[list[Beatmap]] = None

    @computed_field  # type: ignore
    @property
    def url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.id}"

    @computed_field  # type: ignore
    @property
    def discussion_url(self) -> str:
        return f"https://osu.ppy.sh/beatmapsets/{self.id}/discussion"

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> Beatmapset:
        return cls.model_validate(
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
                "status": cast_int(data["approved"]),
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
    beatmap: Optional[Beatmap] = None
    beatmapset: Optional[Beatmapset] = None


class BeatmapsetDiscussionPost(BaseModel):
    id: int
    user_id: int
    system: bool
    message: str
    created_at: datetime
    beatmap_discussion_id: Optional[int] = None
    last_editor_id: Optional[int] = None
    deleted_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class BeatmapsetDiscussion(BaseModel):
    id: int
    beatmapset_id: int
    user_id: int
    message_type: BeatmapsetDisscussionType
    resolved: bool
    can_be_resolved: bool
    can_grant_kudosu: bool
    created_at: datetime
    beatmap_id: Optional[int] = None
    deleted_by_id: Optional[int] = None
    parent_id: Optional[int] = None
    timestamp: Optional[int] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    last_post_at: Optional[datetime] = None
    kudosu_denied: Optional[bool] = None
    starting_post: Optional[BeatmapsetDiscussionPost] = None


class BeatmapsetVoteEvent(BaseModel):
    score: int
    user_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    beatmapset_discussion_id: Optional[int] = None


class BeatmapsetEventComment(BaseModel):
    beatmap_discussion_id: Optional[int] = None
    beatmap_discussion_post_id: Optional[int] = None
    new_vote: Optional[BeatmapsetVoteEvent] = None
    votes: Optional[list[BeatmapsetVoteEvent]] = None
    mode: Optional[Gamemode] = None
    reason: Optional[str] = None
    source_user_id: Optional[int] = None
    source_user_username: Optional[str] = None
    nominator_ids: Optional[list[int]] = None
    new: Optional[str] = None
    old: Optional[str] = None
    new_user_id: Optional[int] = None
    new_user_username: Optional[str] = None


class BeatmapsetEvent(BaseModel):
    id: int
    type: BeatmapsetEventType
    r"""Information on types: https://github.com/ppy/osu-web/blob/master/resources/js/interfaces/beatmapset-event-json.ts"""
    created_at: datetime
    user_id: int
    beatmapset: Optional[Beatmapset] = None
    discussion: Optional[BeatmapsetDiscussion] = None
    comment: Optional[dict] = None


class BeatmapPackUserCompletion(BaseModel):
    beatmapset_ids: list[int]
    completed: bool


class BeatmapPack(BaseModel):
    author: str
    date: datetime
    name: str
    no_diff_reduction: bool
    tag: str
    url: str
    ruleset_id: Optional[int] = None
    beatmapsets: Optional[list[Beatmapset]] = None
    user_completion_data: Optional[BeatmapPackUserCompletion] = None

    @property
    def mode(self) -> Optional[Gamemode]:
        if self.ruleset_id is None:
            return None
        return Gamemode(self.ruleset_id)

    @property
    def pack_type(self) -> BeatmapPackType:
        return BeatmapPackType.from_tag(self.tag[0])

    @property
    def id(self) -> int:
        return int(self.tag[1:])


class BeatmapPacksResponse(CursorModel):
    beatmap_packs: list[BeatmapPack]


class BeatmapsetDiscussionResponse(CursorModel):
    beatmaps: list[Beatmap]
    discussions: list[BeatmapsetDiscussion]
    included_discussions: list[BeatmapsetDiscussion]
    users: list[User]
    max_blocks: int

    @model_validator(mode="before")
    @classmethod
    def _set_max_blocks(cls, values: dict[str, object]) -> dict[str, object]:
        if isinstance(values["reviews_config"], Mapping):
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
