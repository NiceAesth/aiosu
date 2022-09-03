from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List
from typing import Optional

from .gamemode import Gamemode


class BeatmapRankStatus(Enum):
    GRAVEYARD = (-2, "graveyard")
    WIP = (-1, "wip")
    PENDING = (0, "pending")
    RANKED = (1, "ranked")
    APPROVED = (2, "approved")
    QUALIFIED = (3, "qualified")
    LOVED = (4, "loved")

    def __init__(self, id: int, name_api: str):
        self.id: int = id
        self.name_api: str = name_api

    def __int__(self):
        return self.id

    @staticmethod
    def from_id(id) -> BeatmapRankStatus:
        if not isinstance(id, int):
            id = int(id)

        for status in list(BeatmapRankStatus):
            if status.id == id:
                return status

    @staticmethod
    def from_name_api(name_api) -> BeatmapRankStatus:
        for status in list(BeatmapRankStatus):
            if status.name_api == name_api:
                return status


@dataclass
class BeatmapAvailability:
    more_information: Optional[str] = None
    download_disabled: Optional[bool] = None


@dataclass
class BeatmapNominations:
    current: Optional[int] = None
    required: Optional[int] = None


@dataclass(frozen=True)
class BeatmapCovers:
    cover: str
    cover_2_x: str
    card: str
    card_2_x: str
    list: str
    list_2_x: str
    slimcover: str
    slimcover_2_x: str


@dataclass(frozen=True)
class BeatmapHype:
    current: int
    required: int


@dataclass
class BeatmapFailtimes:
    exit: Optional[List[int]] = None
    fail: Optional[List[int]] = None


@dataclass(frozen=True)
class Beatmap:
    beatmapset_id: int = None
    difficulty_rating: float = None
    id: int = None
    mode: Gamemode = None
    status: BeatmapRankStatus = None
    total_length: int = None
    user_id: int = None
    version: str = None
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
    def count_objects(self):
        return self.count_spinners + self.count_circles + self.count_sliders


@dataclass(frozen=True)
class Beatmapset:
    artist: str = None
    artist_unicode: str = None
    covers: BeatmapCovers = None
    creator: str = None
    favourite_count: int = None
    id: int = None
    nsfw: bool = None
    play_count: int = None
    preview_url: str = None
    source: str = None
    status: BeatmapRankStatus = None
    title: str = None
    title_unicode: str = None
    user_id: int = None
    video: bool = None
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
    ratings: Optional[List[int]] = None
    has_favourited: Optional[bool] = None
    beatmaps: Optional[List[Beatmap]] = None
