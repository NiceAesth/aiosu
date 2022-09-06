from __future__ import annotations

import datetime
from enum import Enum
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

    def __repr__(self) -> str:
        return self.name_api

    @classmethod
    def _missing_(cls, query) -> BeatmapRankStatus:
        if isinstance(query, int):
            for status in list(BeatmapRankStatus):
                if status.id == query:
                    return status
        elif isinstance(query, str):
            for status in list(BeatmapRankStatus):
                if status.name_api == query.lower():
                    return status


class BeatmapAvailability(BaseModel):
    more_information: Optional[str] = None
    download_disabled: Optional[bool] = None


class BeatmapNominations(BaseModel):
    current: Optional[int] = None
    required: Optional[int] = None


class BeatmapCovers(BaseModel):
    cover: str
    cover_2_x: str
    card: str
    card_2_x: str
    list: str
    list_2_x: str
    slimcover: str
    slimcover_2_x: str


class BeatmapHype(BaseModel):
    current: int
    required: int


class BeatmapFailtimes(BaseModel):
    exit: Optional[list[int]] = None
    fail: Optional[list[int]] = None


class Beatmap(BaseModel):
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


class Beatmapset(BaseModel):
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
    ratings: Optional[list[int]] = None
    has_favourited: Optional[bool] = None
    beatmaps: Optional[list[Beatmap]] = None
