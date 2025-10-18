"""
This module contains models for featured artists.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import BaseModel
from .beatmap import Beatmapset
from .common import CursorModel

__all__ = (
    "Artist",
    "ArtistAlbum",
    "ArtistLabel",
    "ArtistSearch",
    "ArtistSortType",
    "ArtistTrack",
    "ArtistTracksResponse",
)

ArtistSortType = Literal[
    "album_asc",
    "album_desc",
    "artist_asc",
    "artist_desc",
    "bpm_asc",
    "bpm_desc",
    "genre_asc",
    "genre_desc",
    "length_asc",
    "length_desc",
    "relevance_asc",
    "relevance_desc",
    "title_asc",
    "title_desc",
    "update_asc",
    "update_desc",
]


class ArtistSearch(BaseModel):
    is_default_sort: bool
    sort: ArtistSortType


class ArtistLabel(BaseModel):
    id: int
    artists: list[Artist]
    name: str
    description: str
    icon_url: str
    header_url: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    soundcloud: str | None = None
    website: str | None = None


class Artist(BaseModel):
    id: int
    name: str
    user_id: int | None = None
    description: str | None = None
    visible: bool | None = None
    header_url: str | None = None
    cover_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    beatmapsets: list[Beatmapset] | None = None
    label: ArtistLabel | None = None
    albums: list[ArtistAlbum] | None = None
    tracks: list[ArtistTrack] | None = None
    bandcamp: str | None = None
    facebook: str | None = None
    patreon: str | None = None
    soundcloud: str | None = None
    spotify: str | None = None
    twitter: str | None = None
    website: str | None = None
    youtube: str | None = None
    video_url: str | None = None


class ArtistAlbum(BaseModel):
    id: int
    artist_id: int
    title: str
    title_romanized: str
    genre: str
    is_new: bool
    cover_url: str


class ArtistTrack(BaseModel):
    id: int
    artist_id: int
    bpm: float
    cover_url: str
    exclusive: bool
    genre: str
    is_new: bool
    length: str
    title: str
    artist: Artist
    osz_url: str = Field(alias="osz")
    preview_url: str = Field(alias="preview")
    album: ArtistAlbum | None = None
    album_id: int | None = None
    updated_at: datetime | None = None
    version: str | None = None


class ArtistTracksResponse(CursorModel):
    """Artist response model."""

    artist_tracks: list[ArtistTrack]
    search: ArtistSearch | None = None
