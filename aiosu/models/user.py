"""
This module contains models for User objects.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from enum import unique
from typing import Any
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import Field

from .base import BaseModel
from .common import Country
from .common import HTMLBody
from .common import TimestampedCount
from .gamemode import Gamemode

if TYPE_CHECKING:
    from typing import Callable

__all__ = (
    "User",
    "UserAccountHistory",
    "UserBadge",
    "UserGradeCounts",
    "UserGroup",
    "UserKudosu",
    "UserLevel",
    "UserProfileCover",
    "UserProfileTournamentBanner",
    "UserQueryType",
    "UserRankHistoryElement",
    "UserStats",
    "UserAccountHistoryType",
    "UserRankHighest",
)


cast_int: Callable[..., int] = lambda x: int(x or 0)
cast_float: Callable[..., float] = lambda x: float(x or 0)

UserAccountHistoryType = Literal[
    "note",
    "restriction",
    "silence",
    "tournament_ban",
]

OLD_QUERY_TYPES = {
    "ID": "id",
    "USERNAME": "string",
}


@unique
class UserQueryType(Enum):
    ID = "id"
    USERNAME = "username"

    @property
    def old_api_name(self) -> str:
        return OLD_QUERY_TYPES[self.name]

    @property
    def new_api_name(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, query: object) -> Any:
        if isinstance(query, str):
            query = query.lower()
        for q in list(UserQueryType):
            if query in (q.old_api_name, q.new_api_name):
                return q
        raise ValueError(f"UserQueryType {query} does not exist.")


class UserLevel(BaseModel):
    current: int
    progress: float

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserLevel:
        level = cast_float(data["level"])
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
        r"""Average rank gain.

        :return: Average rank gain for a user
        :rtype: float
        """
        return (self.data[1] - self.data[-1]) / len(self.data)


class UserRankHighest(BaseModel):
    rank: int
    updated_at: datetime


class UserProfileCover(BaseModel):
    url: str
    custom_url: Optional[str]
    id: Optional[str]


class UserProfileTournamentBanner(BaseModel):
    tournament_id: int
    id: Optional[int]
    image: Optional[str]
    image_2_x: Optional[str] = Field(alias="image@2x")


class UserBadge(BaseModel):
    awarded_at: datetime
    description: str
    image_url: str
    url: str


class UserAccountHistory(BaseModel):
    id: int
    timestamp: datetime
    length: int
    permanent: bool
    type: UserAccountHistoryType
    description: Optional[str]


class UserGradeCounts(BaseModel):
    ssh: Optional[int]
    """Number of Silver SS ranks achieved."""
    ss: Optional[int]
    """Number of SS ranks achieved."""
    sh: Optional[int]
    """Number of Silver S ranks achieved."""
    s: Optional[int]
    """Number of S ranks achieved."""
    a: Optional[int]
    """Number of A ranks achieved."""

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserGradeCounts:
        return cls.parse_obj(
            {
                "ss": cast_int(data["count_rank_ss"]),
                "ssh": cast_int(data["count_rank_ssh"]),
                "s": cast_int(data["count_rank_s"]),
                "sh": cast_int(data["count_rank_sh"]),
                "a": cast_int(data["count_rank_a"]),
            },
        )


class UserGroup(BaseModel):
    id: int
    identifier: str
    name: str
    short_name: str
    has_listing: bool
    has_playmodes: bool
    is_probationary: bool
    colour: Optional[str]
    playmodes: Optional[list[Gamemode]]
    description: Optional[str]


class UserStats(BaseModel):
    """Fields are marked as optional since they might be missing from rankings other than performance."""

    ranked_score: Optional[int]
    play_count: Optional[int]
    grade_counts: Optional[UserGradeCounts]
    total_hits: Optional[int]
    is_ranked: Optional[bool]
    total_score: Optional[int]
    level: Optional[UserLevel]
    hit_accuracy: Optional[float]
    play_time: Optional[int]
    pp: Optional[float]
    pp_exp: Optional[float]
    replays_watched_by_others: Optional[int]
    maximum_combo: Optional[int]
    global_rank: Optional[int]
    global_rank_exp: Optional[int]
    country_rank: Optional[int]
    user: Optional[User]
    count_300: Optional[int]
    count_100: Optional[int]
    count_50: Optional[int]
    count_miss: Optional[int]

    @property
    def pp_per_playtime(self) -> float:
        r"""PP per playtime.

        :return: PP per playtime
        :rtype: float
        """
        if not self.play_time or not self.pp:
            return 0
        return self.pp / self.play_time * 3600

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserStats:
        """Some fields can be None, we want to force them to cast to a value."""
        return cls.parse_obj(
            {
                "level": UserLevel._from_api_v1(data),
                "pp": cast_float(data["pp_raw"]),
                "global_rank": cast_int(data["pp_rank"]),
                "country_rank": cast_int(data["pp_country_rank"]),
                "ranked_score": cast_int(data["ranked_score"]),
                "hit_accuracy": cast_float(data["accuracy"]),
                "play_count": cast_int(data["playcount"]),
                "play_time": cast_int(data["total_seconds_played"]),
                "total_score": cast_int(data["total_score"]),
                "total_hits": cast_int(data["count300"])
                + cast_int(data["count100"])
                + cast_int(data["count50"]),
                "is_ranked": cast_float(data["pp_raw"]) != 0,
                "grade_counts": UserGradeCounts._from_api_v1(data),
                "count_300": cast_int(data["count300"]),
                "count_100": cast_int(data["count100"]),
                "count_50": cast_int(data["count50"]),
            },
        )


class UserAchievmement(BaseModel):
    achieved_at: datetime
    achievement_id: int


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
    is_deleted: Optional[bool]
    last_visit: Optional[datetime]
    discord: Optional[str]
    has_supported: Optional[bool]
    interests: Optional[str]
    join_date: Optional[datetime]
    kudosu: Optional[UserKudosu]
    location: Optional[str]
    max_blocks: Optional[int]
    max_friends: Optional[int]
    occupation: Optional[str]
    playmode: Optional[Gamemode]
    playstyle: Optional[list[str]]
    post_count: Optional[int]
    profile_order: Optional[list[str]]
    title: Optional[str]
    twitter: Optional[str]
    website: Optional[str]
    country: Optional[Country]
    cover: Optional[UserProfileCover]
    is_restricted: Optional[bool]
    account_history: Optional[list[UserAccountHistory]]
    active_tournament_banner: Optional[UserProfileTournamentBanner]
    badges: Optional[list[UserBadge]]
    beatmap_playcounts_count: Optional[int]
    favourite_beatmapset_count: Optional[int]
    follower_count: Optional[int]
    graveyard_beatmapset_count: Optional[int]
    groups: Optional[list[UserGroup]]
    loved_beatmapset_count: Optional[int]
    monthly_playcounts: Optional[list[TimestampedCount]]
    page: Optional[HTMLBody]
    pending_beatmapset_count: Optional[int]
    previous_usernames: Optional[list[str]]
    ranked_beatmapset_count: Optional[int]
    replays_watched_counts: Optional[list[TimestampedCount]]
    scores_best_count: Optional[int]
    scores_first_count: Optional[int]
    scores_recent_count: Optional[int]
    statistics: Optional[UserStats]
    support_level: Optional[int]
    user_achievements: Optional[list[UserAchievmement]]
    rank_history: Optional[UserRankHistoryElement]
    rank_highest: Optional[UserRankHighest]

    @property
    def url(self) -> str:
        return f"https://osu.ppy.sh/users/{self.id}"

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


UserStats.update_forward_refs()
