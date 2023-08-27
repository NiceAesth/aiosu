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

from pydantic import computed_field
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
    "UserStatsVariant",
    "UserStats",
    "UserAccountHistoryType",
    "UserRankHighest",
    "ManiaStatsVariantsType",
)


cast_int: Callable[..., int] = lambda x: int(x or 0)
cast_float: Callable[..., float] = lambda x: float(x or 0)

UserAccountHistoryType = Literal[
    "note",
    "restriction",
    "silence",
    "tournament_ban",
]

ManiaStatsVariantsType = Literal[
    "4k",
    "7k",
]

OLD_QUERY_TYPES = {
    "ID": "id",
    "USERNAME": "string",
}


@unique
class UserQueryType(Enum):
    ID = "id"
    USERNAME = "username"

    @computed_field  # type: ignore
    @property
    def old_api_name(self) -> str:
        return OLD_QUERY_TYPES[self.name]

    @computed_field  # type: ignore
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
    progress: int

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserLevel:
        level = cast_float(data["level"])
        current = int(level)
        progress = (level - current) * 100
        return cls.model_validate({"current": current, "progress": int(progress)})


class UserKudosu(BaseModel):
    total: int
    available: int


class UserRankHistoryElement(BaseModel):
    mode: str
    data: list[int]

    @computed_field  # type: ignore
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
    custom_url: Optional[str] = None
    id: Optional[str] = None


class UserProfileTournamentBanner(BaseModel):
    tournament_id: int
    id: Optional[int] = None
    image: Optional[str] = None
    image_2_x: Optional[str] = Field(default=None, alias="image@2x")


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
    description: Optional[str] = None


class UserGradeCounts(BaseModel):
    ssh: Optional[int] = None
    """Number of Silver SS ranks achieved."""
    ss: Optional[int] = None
    """Number of SS ranks achieved."""
    sh: Optional[int] = None
    """Number of Silver S ranks achieved."""
    s: Optional[int] = None
    """Number of S ranks achieved."""
    a: Optional[int] = None
    """Number of A ranks achieved."""

    @classmethod
    def _from_api_v1(cls, data: Any) -> UserGradeCounts:
        return cls.model_validate(
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
    colour: Optional[str] = None
    playmodes: Optional[list[Gamemode]] = None
    description: Optional[str] = None


class UserStatsVariant(BaseModel):
    mode: Gamemode
    variant: str
    pp: float
    country_rank: Optional[int] = None
    global_rank: Optional[int] = None


class UserStats(BaseModel):
    """Fields are marked as optional since they might be missing from rankings other than performance."""

    ranked_score: Optional[int] = None
    play_count: Optional[int] = None
    grade_counts: Optional[UserGradeCounts] = None
    total_hits: Optional[int] = None
    is_ranked: Optional[bool] = None
    total_score: Optional[int] = None
    level: Optional[UserLevel] = None
    hit_accuracy: Optional[float] = None
    play_time: Optional[int] = None
    pp: Optional[float] = None
    pp_exp: Optional[float] = None
    replays_watched_by_others: Optional[int] = None
    maximum_combo: Optional[int] = None
    global_rank: Optional[int] = None
    global_rank_exp: Optional[int] = None
    country_rank: Optional[int] = None
    user: Optional[User] = None
    count_300: Optional[int] = None
    count_100: Optional[int] = None
    count_50: Optional[int] = None
    count_miss: Optional[int] = None
    variants: Optional[list[UserStatsVariant]] = None

    @computed_field  # type: ignore
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
        return cls.model_validate(
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
    default_group: Optional[str] = None
    is_active: Optional[bool] = None
    is_bot: Optional[bool] = None
    is_online: Optional[bool] = None
    is_supporter: Optional[bool] = None
    pm_friends_only: Optional[bool] = None
    profile_colour: Optional[str] = None
    is_deleted: Optional[bool] = None
    last_visit: Optional[datetime] = None
    discord: Optional[str] = None
    has_supported: Optional[bool] = None
    interests: Optional[str] = None
    join_date: Optional[datetime] = None
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
    account_history: Optional[list[UserAccountHistory]] = None
    active_tournament_banner: Optional[UserProfileTournamentBanner] = None
    badges: Optional[list[UserBadge]] = None
    beatmap_playcounts_count: Optional[int] = None
    favourite_beatmapset_count: Optional[int] = None
    follower_count: Optional[int] = None
    graveyard_beatmapset_count: Optional[int] = None
    groups: Optional[list[UserGroup]] = None
    loved_beatmapset_count: Optional[int] = None
    monthly_playcounts: Optional[list[TimestampedCount]] = None
    page: Optional[HTMLBody] = None
    pending_beatmapset_count: Optional[int] = None
    previous_usernames: Optional[list[str]] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[list[TimestampedCount]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional[UserStats] = None
    support_level: Optional[int] = None
    user_achievements: Optional[list[UserAchievmement]] = None
    rank_history: Optional[UserRankHistoryElement] = None
    rank_highest: Optional[UserRankHighest] = None

    @computed_field  # type: ignore
    @property
    def url(self) -> str:
        return f"https://osu.ppy.sh/users/{self.id}"

    @classmethod
    def _from_api_v1(cls, data: Any) -> User:
        return cls.model_validate(
            {
                "avatar_url": f"https://s.ppy.sh/a/{data['user_id']}",
                "country_code": data["country"],
                "id": data["user_id"],
                "username": data["username"],
                "join_date": data["join_date"],
                "statistics": UserStats._from_api_v1(data),
            },
        )


UserStats.model_rebuild()
