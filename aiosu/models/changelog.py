"""
This module contains models for changelog objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import Field

from .base import BaseModel
from .common import CursorModel


__all__ = (
    "Build",
    "ChangelogEntry",
    "ChangelogEntryType",
    "ChangelogListing",
    "ChangelogMessageFormat",
    "ChangelogSearch",
    "GithubUser",
    "UpdateStream",
    "Version",
)

ChangelogMessageFormat = Literal["markdown", "html"]
ChangelogEntryType = Literal["add", "fix"]


class GithubUser(BaseModel):
    display_name: str
    github_url: Optional[str] = None
    id: Optional[int] = None
    osu_username: Optional[str] = None
    user_id: Optional[int] = None
    user_url: Optional[str] = None


class ChangelogEntry(BaseModel):
    type: ChangelogEntryType
    category: str
    major: bool
    id: Optional[int] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    url: Optional[str] = None
    github_url: Optional[str] = None
    github_pull_request_id: Optional[int] = None
    repository: Optional[str] = None
    message: Optional[str] = None
    message_html: Optional[str] = None
    github_user: Optional[GithubUser] = None


class Version(BaseModel):
    next: Optional[Build] = None
    previous: Optional[Build] = None


class UpdateStream(BaseModel):
    id: int
    is_featured: bool
    name: str
    display_name: Optional[str] = None
    user_count: Optional[int] = None
    latest_build: Optional[Build] = None


class Build(BaseModel):
    id: int
    created_at: datetime
    display_version: str
    users: int
    version: str
    youtube_id: Optional[str] = None
    update_stream: Optional[UpdateStream] = None
    changelog_entries: Optional[list[ChangelogEntry]] = None
    versions: Optional[Version] = None


class ChangelogSearch(BaseModel):
    limit: int
    fro: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    max_id: Optional[int] = None
    stream: Optional[str] = None


class ChangelogListing(CursorModel):
    builds: list[Build]
    search: ChangelogSearch
    streams: list[UpdateStream]


Version.model_rebuild()
UpdateStream.model_rebuild()
