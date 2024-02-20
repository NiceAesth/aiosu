"""
This module contains models for featured artists.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import Field

from .base import BaseModel
from .beatmap import Beatmapset
from .common import CursorModel

__all__ = (
    "Artist",
    "ArtistAlbum",
    "ArtistLabel",
    "ArtistResponse",
    "ArtistSearch",
    "ArtistSortType",
    "ArtistTrack",
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    soundcloud: Optional[str] = None
    website: Optional[str] = None


class Artist(BaseModel):
    id: int
    name: str
    user_id: Optional[int] = None
    description: Optional[str] = None
    visible: Optional[bool] = None
    header_url: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    beatmapsets: Optional[list[Beatmapset]] = None
    label: Optional[ArtistLabel] = None
    albums: Optional[list[ArtistAlbum]] = None
    tracks: Optional[list[ArtistTrack]] = None
    bandcamp: Optional[str] = None
    facebook: Optional[str] = None
    patreon: Optional[str] = None
    soundcloud: Optional[str] = None
    spotify: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    youtube: Optional[str] = None
    video_url: Optional[str] = None


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
    album: Optional[ArtistAlbum] = None
    album_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    version: Optional[str] = None


class ArtistResponse(CursorModel):
    """Artist response model."""

    artist_tracks: list[ArtistTrack]
    search: Optional[ArtistSearch] = None
