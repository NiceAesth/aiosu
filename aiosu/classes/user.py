"""
This module contains models for User objects.
"""
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

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserLevel:
        level = float(data["level"])
        current = int(level)
        progress = (level - current) * 100
        return cls.parse_obj({"current": current, "progress": progress})


class UserKudosu(BaseModel):
    total: int
    available: int


class UserRankHistoryElement(BaseModel):
    mode: str
    data: list[int]

    @property
    def average_gain(self) -> float:
        """Average rank gain.

        :return: Average rank gain for a user
        :rtype: float
        """
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
    id: int
    description: str
    length: int
    timestamp: datetime.datetime
    type: str


class UserGradeCounts(BaseModel):
    ssh: int
    """Number of Silver SS ranks achieved."""
    ss: int
    """Number of SS ranks achieved."""
    sh: int
    """Number of Silver S ranks achieved."""
    s: int
    """Number of S ranks achieved."""
    a: int
    """Number of A ranks achieved."""

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserGradeCounts:
        return cls.parse_obj(
            {
                "ss": data["count_rank_ss"],
                "ssh": data["count_rank_ssh"],
                "s": data["count_rank_s"],
                "sh": data["count_rank_sh"],
                "a": data["count_rank_a"],
            },
        )


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
    is_ranked: bool
    grade_counts: UserGradeCounts
    replays_watched_by_others: Optional[int]
    maximum_combo: Optional[int]
    global_rank: Optional[int]
    country_rank: Optional[int]
    user: Optional[User] = None

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserStats:
        return cls.parse_obj(
            {
                "level": UserLevel._from_api_v1(data),
                "pp": data["pp_raw"],
                "ranked_score": data["ranked_score"],
                "hit_accuracy": data["accuracy"],
                "play_count": data["playcount"],
                "play_time": data["total_seconds_played"],
                "total_score": data["total_score"],
                "total_hits": data["count300"] + data["count100"] + data["count50"],
                "is_ranked": data["pp_raw"] != "0",
                "grade_counts": UserGradeCounts._from_api_v1(data),
            },
        )


class User(BaseModel):
    avatar_url: str
    country_code: str
    id: int
    username: str
    default_group: Optional[str]
    is_active: Optional[bool]
    is_bot: Optional[bool]
    is_online: Optional[bool]
    is_supporter: Optional[bool]
    pm_friends_only: Optional[bool]
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
    account_history: Optional[list[Any]] = None  # Unsure what this is
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
    previous_usernames: Optional[list[str]] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[list[TimestampedCount]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional[UserStats] = None
    support_level: Optional[int] = None
    user_achievements: Optional[list[Achievement]] = None
    rank_history: Optional[UserRankHistoryElement] = None

    @classmethod
    def _from_api_v1(cls, data: Any) -> User:
        return cls.parse_obj(
            {
                "avatar_url": f"https://s.ppy.sh/a/{data['user_id']}",
                "country_code": data["country"],
                "id": data["user_id"],
                "username": data["username"],
                "join_date": data["join_date"],
                "statistics": UserStats._from_api_v1(data),
            },
        )
