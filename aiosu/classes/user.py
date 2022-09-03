from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional

from classes import Common

from .gamemode import Gamemode


@dataclass(frozen=True)
class Userpage:
    html: str
    raw: Optional[str] = None


@dataclass(frozen=True)
class UserLevel:
    current: int
    progress: int


@dataclass(frozen=True)
class UserKudosu:
    total: int
    available: int


@dataclass(frozen=True)
class UserRankHistoryElement:
    mode: str
    data: List[int]

    @property
    def average_gain(self):
        return (self.data[1] - self.data[-1]) / len(self.data)


@dataclass(frozen=True)
class UserProfileCover:
    url: str
    custom_url: Optional[str] = None
    id: Optional[str] = None


@dataclass(frozen=True)
class UserProfileTournamentBanner:
    tournament_id: int
    image: str
    id: Optional[int] = None


@dataclass(frozen=True)
class UserBadge:
    awarded_at: datetime
    description: str
    image_url: str
    url: str


@dataclass(frozen=True)
class UserAccountHistory:
    description: str
    id: int
    length: int
    timestamp: datetime.datetime
    type: str


@dataclass(frozen=True)
class UserGradeCounts:
    ss: int
    ssh: int
    s: int
    sh: int
    a: int


@dataclass(frozen=True)
class UserGroup:
    id: int
    identifier: str
    name: str
    short_name: str
    description: str
    colour: str
    is_probationary: Optional[bool] = None


@dataclass(frozen=True)
class UserStats:
    level: UserLevel
    pp: float
    ranked_score: int
    hit_accuracy: float
    play_count: int
    play_time: int
    total_score: int
    total_hits: int
    maximum_combo: int
    replays_watched_by_others: int
    is_ranked: bool
    grade_counts: UserGradeCounts
    global_rank: Optional[int]
    country_rank: Optional[int]
    user: Optional[User] = None


@dataclass(frozen=True)
class User:
    avatar_url: str
    country_code: str
    default_group: str
    id: int
    is_active: bool
    is_bot: bool
    is_online: bool
    is_supporter: bool
    pm_friends_only: bool
    profile_colour: str
    name: str
    is_deleted: Optional[bool] = None
    last_visit: Optional[datetime.datetime] = None
    discord: Optional[str] = None
    has_supported: Optional[bool] = None
    interests: Optional[str] = None
    join_date: Optional[datetime.datetime] = None
    kudosu: Optional[UserKudosu] = None
    location: Optional[str] = None
    max_blocks: Optional[int] = None
    max_friends: Optional[int] = None
    occupation: Optional[str] = None
    playmode: Optional[Gamemode] = None
    playstyle: Optional[List[str]] = None
    post_count: Optional[int] = None
    profile_order: Optional[List[str]] = None
    title: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    country: Optional[Common.Country] = None
    cover: Optional[UserProfileCover] = None
    is_restricted: Optional[bool] = None
    account_history: Optional[List[Any]] = None
    active_tournament_banner: Optional[UserProfileTournamentBanner] = None
    badges: Optional[List[UserBadge]] = None
    beatmap_playcounts_count: Optional[int] = None
    favourite_beatmapset_count: Optional[int] = None
    follower_count: Optional[int] = None
    graveyard_beatmapset_count: Optional[int] = None
    groups: Optional[List[UserGroup]] = None
    loved_beatmapset_count: Optional[int] = None
    monthly_playcounts: Optional[List[Common.TimestampedCount]] = None
    page: Optional[Userpage] = None
    pending_beatmapset_count: Optional[int] = None
    previous_usernames: Optional[List[Any]] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[List[Common.TimestampedCount]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional[UserStats] = None
    support_level: Optional[int] = None
    user_achievements: Optional[List[Common.Achievement]] = None
    rank_history: Optional[UserRankHistoryElement] = None
