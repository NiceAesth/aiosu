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
    "GithubUser",
    "UpdateStream",
    "Version",
    "ChangelogListing",
    "ChangelogSearch",
    "ChangelogMessageFormats",
)

ChangelogMessageFormats = Literal["markdown", "html"]


class GithubUser(BaseModel):
    display_name: str
    github_url: Optional[str]
    id: Optional[int]
    osu_username: Optional[str]
    user_id: Optional[int]
    user_url: Optional[str]


class ChangelogEntry(BaseModel):
    type: str
    category: str
    major: bool
    id: Optional[int]
    title: Optional[str]
    created_at: Optional[datetime]
    url: Optional[str]
    github_url: Optional[str]
    github_pull_request_id: Optional[int]
    repository: Optional[str]
    message: Optional[str]
    message_html: Optional[str]
    github_user: Optional[GithubUser]


class Version(BaseModel):
    next: Optional[Build]
    previous: Optional[Build]


class UpdateStream(BaseModel):
    id: int
    is_featured: bool
    name: str
    display_name: Optional[str]
    user_count: Optional[int]
    latest_build: Optional[Build]


class Build(BaseModel):
    id: int
    created_at: datetime
    display_version: str
    users: int
    version: str
    update_stream: Optional[UpdateStream]
    changelog_entries: Optional[list[ChangelogEntry]]
    versions: Optional[Version]


class ChangelogSearch(BaseModel):
    limit: int
    fro: Optional[str] = Field(alias="from")
    to: Optional[str]
    max_id: Optional[int]
    stream: Optional[str]


class ChangelogListing(CursorModel):
    builds: list[Build]
    search: ChangelogSearch
    streams: list[UpdateStream]


Version.update_forward_refs()
UpdateStream.update_forward_refs()
