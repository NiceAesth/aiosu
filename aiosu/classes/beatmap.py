"""
This module contains models for Beatmap objects.
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any
from typing import Optional

from .gamemode import Gamemode
from .models import BaseModel


class BeatmapRankStatus(Enum):
    GRAVEYARD = (-2, "graveyard")
    WIP = (-1, "wip")
    PENDING = (0, "pending")
    RANKED = (1, "ranked")
    APPROVED = (2, "approved")
    QUALIFIED = (3, "qualified")
    LOVED = (4, "loved")

    def __init__(self, id: int, name_api: str) -> None:
        self.id: int = id
        self.name_api: str = name_api

    def __int__(self) -> int:
        return self.id

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


class BeatmapAvailability(BaseModel):
    more_information: Optional[str] = None
    download_disabled: Optional[bool] = None

    @classmethod
    def _from_api_v1(cls, data: Any) -> BeatmapAvailability:
        return cls.parse_obj({"download_disabled": data["download_unavailable"]})


class BeatmapNominations(BaseModel):
    current: Optional[int] = None
    required: Optional[int] = None


class BeatmapCovers(BaseModel):
    cover: str
    card: str
    list: str
    slimcover: str
    cover_2_x: Optional[str]
    card_2_x: Optional[str]
    list_2_x: Optional[str]
    slimcover_2_x: Optional[str]

    @classmethod
    def _from_api_v1(cls, data: Any) -> BeatmapCovers:
        base_url = "https://assets.ppy.sh/beatmaps/"
        return cls.parse_obj(
            {
                "cover": f"{base_url}{data['beatmapset_id']}/covers/cover.jpg",
                "card": f"{base_url}{data['beatmapset_id']}/covers/card.jpg",
                "list": f"{base_url}{data['beatmapset_id']}/covers/list.jpg",
                "slimcover": f"{base_url}{data['beatmapset_id']}/covers/slimcover.jpg",
                "cover_2_x": f"{base_url}{data['beatmapset_id']}/covers/cover@2x.jpg",
                "card_2_x": f"{base_url}{data['beatmapset_id']}/covers/card@2x.jpg",
                "list_2_x": f"{base_url}{data['beatmapset_id']}/covers/list@2x.jpg",
                "slimcover_2_x": f"{base_url}{data['beatmapset_id']}/covers/slimcover@2x.jpg",
            },
        )


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
    mode: Gamemode
    beatmapset_id: int
    difficulty_rating: float
    status: BeatmapRankStatus
    total_length: int
    user_id: int
    version: str
    accuracy: Optional[float] = None
    ar: Optional[float] = None
    bpm: Optional[float] = None
    convert: Optional[bool] = None
    count_circles: Optional[int] = None
    count_sliders: Optional[int] = None
    count_spinners: Optional[int] = None
    cs: Optional[float] = None
    deleted_at: Optional[datetime.datetime] = None
    drain: Optional[float] = None
    hit_length: Optional[int] = None
    is_scoreable: Optional[bool] = None
    last_updated: Optional[datetime.datetime] = None
    passcount: Optional[int] = None
    playcount: Optional[int] = None
    url: Optional[str] = None
    checksum: Optional[str] = None
    max_combo: Optional[int] = None
    beatmapset: Optional[Beatmapset] = None
    failtimes: Optional[BeatmapFailtimes] = None

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

    # Support both since API decided to name them differently for Beatmap and Beatmapset
    @property
    def play_count(self) -> Optional[int]:
        """Alias for playcount.

        :return: Playcount of the beatmap
        :rtype: Optional[int]
        """
        return self.playcount

    @play_count.setter
    def play_count(self, new_value: int) -> None:
        self.playcount = new_value

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
                "mode": int(data["mode"]),
                "playcount": data["playcount"],
                "passcount": data["passcount"],
                "count_circles": data["count_normal"],
                "count_sliders": data["count_slider"],
                "count_spinners": data["count_spinner"],
                "max_combo": data["max_combo"],
            },
        )


class Beatmapset(BaseModel):
    artist: str
    artist_unicode: str
    covers: BeatmapCovers
    creator: str
    favourite_count: int
    id: int
    play_count: int
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
    last_updated: Optional[datetime.datetime] = None
    legacy_thread_url: Optional[str] = None
    nominations_summary: Optional[BeatmapNominations] = None
    ranked_date: Optional[datetime.datetime] = None
    storyboard: Optional[bool] = None
    submitted_date: Optional[datetime.datetime] = None
    tags: Optional[str] = None
    ratings: Optional[list[int]] = None
    has_favourited: Optional[bool] = None
    beatmaps: Optional[list[Beatmap]] = None

    @property
    def playcount(self) -> int:
        """Alias for play_count

        :return: Playcount of the beatmap
        :rtype: int
        """
        return self.playcount

    @playcount.setter
    def playcount(self, new_value: int) -> None:
        self.playcount = new_value

    @classmethod
    def _from_api_v1(cls, data: Any) -> Beatmapset:
        return cls.parse_obj(
            {
                "artist": data["artist"],
                "artist_unicode": data["artist"],
                "covers": BeatmapCovers._from_api_v1(data),
                "favourite_count": data["favourite_count"],
                "id": data["beatmapset_id"],
                "creator": data["creator"],
                "play_count": data["playcount"],
                "preview_url": f"https://b.ppy.sh/preview/{data['beatmapset_id']}.mp3",
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


Beatmap.update_forward_refs()
