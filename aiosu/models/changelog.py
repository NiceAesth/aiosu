"""
This module contains models for changelog objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

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
    github_url: str | None = None
    id: int | None = None
    osu_username: str | None = None
    user_id: int | None = None
    user_url: str | None = None


class ChangelogEntry(BaseModel):
    type: ChangelogEntryType
    category: str
    major: bool
    id: int | None = None
    title: str | None = None
    created_at: datetime | None = None
    url: str | None = None
    github_url: str | None = None
    github_pull_request_id: int | None = None
    repository: str | None = None
    message: str | None = None
    message_html: str | None = None
    github_user: GithubUser | None = None


class Version(BaseModel):
    next: Build | None = None
    previous: Build | None = None


class UpdateStream(BaseModel):
    id: int
    is_featured: bool
    name: str
    display_name: str | None = None
    user_count: int | None = None
    latest_build: Build | None = None


class Build(BaseModel):
    id: int
    created_at: datetime
    display_version: str
    users: int
    version: str
    youtube_id: str | None = None
    update_stream: UpdateStream | None = None
    changelog_entries: list[ChangelogEntry] | None = None
    versions: Version | None = None


class ChangelogSearch(BaseModel):
    limit: int
    fro: str | None = Field(default=None, alias="from")
    to: str | None = None
    max_id: int | None = None
    stream: str | None = None


class ChangelogListing(CursorModel):
    builds: list[Build]
    search: ChangelogSearch
    streams: list[UpdateStream]
