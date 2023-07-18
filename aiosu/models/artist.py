"""
This module contains models for featured artists.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseModel
from .common import CursorModel

__all__ = (
    "ArtistTrack",
    "ArtistResponse",
)


class ArtistSearch(BaseModel):
    is_default_sort: bool
    sort: str


class Artist(BaseModel):
    id: int
    name: str


class Album(BaseModel):
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
    album: Optional[Album] = None
    album_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    version: Optional[str] = None


class ArtistResponse(CursorModel):
    """Artist response model."""

    artist_tracks: list[ArtistTrack]
    search: Optional[ArtistSearch] = None
