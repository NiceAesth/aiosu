from __future__ import annotations

import datetime
from enum import Enum
from typing import Any
from typing import Optional

from .common import Achievement
from .common import Country
from .common import TimestampedCount
from .gamemode import Gamemode
from .models import BaseModel


class UserQueryType(Enum):
    ID = ("id", "id")
    USERNAME = ("string", "username")

    def __init__(self, old: str, new: str) -> None:
        self.old_api_name = old
        self.new_api_name = new

    @classmethod
    def _missing_(cls, query: object) -> UserQueryType:
        for q in list(UserQueryType):
            if query in q.value:
                return q
        raise ValueError(f"UserQueryType {query} does not exist.")


class Userpage(BaseModel):
    html: str
    raw: Optional[str] = None


class UserLevel(BaseModel):
    current: int
    progress: int


class UserKudosu(BaseModel):
    total: int
    available: int


class UserRankHistoryElement(BaseModel):
    mode: str
    data: list[int]

    @property
    def average_gain(self) -> float:
        return (self.data[1] - self.data[-1]) / len(self.data)


class UserProfileCover(BaseModel):
    url: str
    custom_url: Optional[str] = None
    id: Optional[str] = None


class UserProfileTournamentBanner(BaseModel):
    tournament_id: int
    image: str
    id: Optional[int] = None


class UserBadge(BaseModel):
    awarded_at: datetime.datetime
    description: str
    image_url: str
    url: str


class UserAccountHistory(BaseModel):
    description: str
    id: int
    length: int
    timestamp: datetime.datetime
    type: str


class UserGradeCounts(BaseModel):
    ss: int
    ssh: int
    s: int
    sh: int
    a: int


class UserGroup(BaseModel):
    id: int
    identifier: str
    name: str
    short_name: str
    description: str
    colour: str
    is_probationary: Optional[bool] = None


class UserStats(BaseModel):
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


class User(BaseModel):
    avatar_url: str
    country_code: str
    default_group: str
    id: int
    is_active: bool
    is_bot: bool
    is_online: bool
    is_supporter: bool
    pm_friends_only: bool
    username: str
    profile_colour: Optional[str]
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
    playstyle: Optional[list[str]] = None
    post_count: Optional[int] = None
    profile_order: Optional[list[str]] = None
    title: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    country: Optional[Country] = None
    cover: Optional[UserProfileCover] = None
    is_restricted: Optional[bool] = None
    account_history: Optional[list[Any]] = None
    active_tournament_banner: Optional[UserProfileTournamentBanner] = None
    badges: Optional[list[UserBadge]] = None
    beatmap_playcounts_count: Optional[int] = None
    favourite_beatmapset_count: Optional[int] = None
    follower_count: Optional[int] = None
    graveyard_beatmapset_count: Optional[int] = None
    groups: Optional[list[UserGroup]] = None
    loved_beatmapset_count: Optional[int] = None
    monthly_playcounts: Optional[list[TimestampedCount]] = None
    page: Optional[Userpage] = None
    pending_beatmapset_count: Optional[int] = None
    previous_usernames: Optional[list[Any]] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[list[TimestampedCount]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional[UserStats] = None
    support_level: Optional[int] = None
    user_achievements: Optional[list[Achievement]] = None
    rank_history: Optional[UserRankHistoryElement] = None
