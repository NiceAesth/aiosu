"""
This module contains models for User objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from enum import unique
from functools import cached_property
from typing import Literal

from pydantic import Field
from pydantic import computed_field

from .base import BaseModel
from .base import cast_float
from .base import cast_int
from .common import Country
from .common import HTMLBody
from .common import TimestampedCount
from .gamemode import Gamemode

__all__ = (
    "DailyChallengeUserStats",
    "LegacyUser",
    "ManiaStatsVariantsType",
    "MatchmakingPool",
    "MatchmakingUserEloHistory",
    "MatchmakingUserStats",
    "Season",
    "SeasonDivision",
    "SeasonUserStats",
    "User",
    "UserAccountHistory",
    "UserAccountHistoryType",
    "UserBadge",
    "UserCompact",
    "UserCurrentAttributes",
    "UserGlobalRank",
    "UserGradeCounts",
    "UserGroup",
    "UserKudosu",
    "UserLevel",
    "UserPreferences",
    "UserProfileCover",
    "UserProfileTournamentBanner",
    "UserQueryType",
    "UserRankHighest",
    "UserRankHistoryElement",
    "UserRelation",
    "UserStatisticsRank",
    "UserStats",
    "UserStatsRulesets",
    "UserStatsVariant",
    "UserTeam",
)


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
    def _missing_(cls, query: object) -> UserQueryType:
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
    def _from_api_v1(cls, data: Mapping[str, object]) -> UserLevel:
        level = cast_float(data["level"])
        current = int(level)
        progress = (level - current) * 100
        return cls.model_validate({"current": current, "progress": int(progress)})


class UserKudosu(BaseModel):
    total: int
    available: int
    rank: int | None = None


class UserRankHistoryElement(BaseModel):
    mode: str
    data: list[int]

    @computed_field  # type: ignore
    @cached_property
    def average_gain(self) -> float:
        r"""Average rank gain.

        :return: Average rank gain for a user
        :rtype: float
        """
        if not self.data:
            return 0.0
        return (self.data[0] - self.data[-1]) / len(self.data)


class UserRankHighest(BaseModel):
    rank: int
    updated_at: datetime


class UserProfileCover(BaseModel):
    url: str
    custom_url: str | None = None
    id: str | None = None


class UserProfileTournamentBanner(BaseModel):
    tournament_id: int
    id: int | None = None
    image: str | None = None
    image_2_x: str | None = Field(default=None, alias="image@2x")


class UserBadge(BaseModel):
    awarded_at: datetime
    description: str
    image_url: str
    image_2x_url: str = Field(alias="image@2x_url")
    url: str


class UserAccountHistory(BaseModel):
    id: int
    timestamp: datetime
    length: int
    permanent: bool
    type: UserAccountHistoryType
    description: str | None = None
    actor: UserCompact | None = None
    supporting_url: str | None = None


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
    def _from_api_v1(cls, data: Mapping[str, object]) -> UserGradeCounts:
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
    colour: str | None = None
    playmodes: list[Gamemode] | None = None
    description: HTMLBody | None = None


class UserStatsVariant(BaseModel):
    mode: Gamemode
    variant: str
    pp: float
    country_rank: int | None = None
    global_rank: int | None = None


class UserStatisticsRank(BaseModel):
    country: int | None


class UserStats(BaseModel):
    """Fields are marked as optional since they might be missing from rankings other than performance."""

    ranked_score: int | None = None
    play_count: int | None = None
    grade_counts: UserGradeCounts | None = None
    total_hits: int | None = None
    is_ranked: bool | None = None
    total_score: int | None = None
    level: UserLevel | None = None
    hit_accuracy: float | None = None
    play_time: int | None = None
    pp: float | None = None
    pp_exp: float | None = None
    replays_watched_by_others: int | None = None
    maximum_combo: int | None = None
    global_rank: int | None = None
    global_rank_exp: int | None = None
    country_rank: int | None = None
    user: UserCompact | None = None
    count_300: int | None = None
    count_100: int | None = None
    count_50: int | None = None
    count_miss: int | None = None
    variants: list[UserStatsVariant] | None = None
    accuracy: float | None = None
    global_rank_percent: float | None = None
    rank: UserStatisticsRank | None = None
    rank_change_since_30_days: int | None = None

    @computed_field  # type: ignore
    @cached_property
    def pp_per_playtime(self) -> float:
        r"""PP per playtime.

        :return: PP per playtime
        :rtype: float
        """
        if not self.play_time or not self.pp:
            return 0.0
        return self.pp / self.play_time * 3600

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> UserStats:
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


class UserStatsRulesets(BaseModel):
    osu: UserStats | None = None
    taiko: UserStats | None = None
    fruits: UserStats | None = None
    mania: UserStats | None = None


class UserAchievmement(BaseModel):
    achieved_at: datetime
    achievement_id: int


class UserRelation(BaseModel):
    target_id: int
    relation_type: str
    mutual: bool
    target: UserCompact | None = None


class UserTeam(BaseModel):
    id: int
    name: str
    short_name: str
    flag_url: str | None = None


class DailyChallengeUserStats(BaseModel):
    user_id: int
    daily_streak_best: int
    daily_streak_current: int
    weekly_streak_best: int
    weekly_streak_current: int
    playcount: int
    top_10p_placements: int
    top_50p_placements: int
    last_update: datetime | None = None
    last_weekly_streak: datetime | None = None


class MatchmakingPool(BaseModel):
    id: int
    name: str
    active: bool
    ruleset_id: int
    type: str
    variant_id: int


class MatchmakingUserEloHistory(BaseModel):
    id: int
    created_at: datetime | None
    elo_after: int
    result: str
    room_id: int


class MatchmakingUserStats(BaseModel):
    user_id: int
    pool_id: int
    first_placements: int
    is_rating_provisional: bool
    plays: int
    rank: int | None = None
    rank_percent: float | None = None
    rating: int | None = None
    total_points: int | None = None
    pool: MatchmakingPool | None = None
    recent_history: list[MatchmakingUserEloHistory] | None = None


class Season(BaseModel):
    id: int
    name: str
    room_count: int
    start_date: datetime | None
    end_date: datetime | None


class SeasonDivision(BaseModel):
    id: int
    name: str
    colour_tier: str
    image_url: str
    threshold: float


class SeasonUserStats(BaseModel):
    division: SeasonDivision
    rank: int
    season: Season
    total_score: float


class UserCurrentAttributes(BaseModel):
    has_blocked: bool


class UserGlobalRank(BaseModel):
    rank: int | None
    ruleset_id: int


class UserPreferences(BaseModel):
    audio_autoplay: bool
    audio_muted: bool
    audio_volume: float
    beatmapset_card_size: Literal["normal", "extra"]
    beatmapset_download: Literal["all", "no_video", "direct"]
    beatmapset_show_anime_cover: bool
    beatmapset_show_nsfw: bool
    beatmapset_title_show_original: bool
    comments_show_deleted: bool
    forum_posts_show_deleted: bool
    legacy_score_only: bool
    profile_cover_expanded: bool
    profile_detail_v2: bool
    scoring_mode: Literal["standardised", "classic"]
    user_list_filter: Literal["all", "online", "offline"]
    user_list_sort: Literal["last_visit", "rank", "username"]
    user_list_view: Literal["card", "list", "brick"]


class _UserBase(BaseModel):
    avatar_url: str | None
    country_code: str | None
    id: int | None
    username: str
    default_group: str | None = None
    profile_colour: str | None = None
    last_visit: datetime | None = None
    kudosu: UserKudosu | None = None
    country: Country | None = None
    cover: UserProfileCover | None = None
    is_restricted: bool | None = None
    account_history: list[UserAccountHistory] | None = None
    active_tournament_banner: UserProfileTournamentBanner | None = None
    active_tournament_banners: list[UserProfileTournamentBanner] | None = None
    badges: list[UserBadge] | None = None
    comments_count: int | None = None
    daily_challenge_user_stats: DailyChallengeUserStats | None = None
    matchmaking_stats: list[MatchmakingUserStats] | None = None
    current_season_stats: SeasonUserStats | None = None
    guest_beatmapset_count: int | None = None
    nominated_beatmapset_count: int | None = None
    ranked_and_approved_beatmapset_count: int | None = None
    unranked_beatmapset_count: int | None = None
    scores_pinned_count: int | None = None
    beatmap_playcounts_count: int | None = None
    favourite_beatmapset_count: int | None = None
    follow_user_mapping: list[int] | None = None
    follower_count: int | None = None
    friends: list[UserRelation] | None = None
    graveyard_beatmapset_count: int | None = None
    groups: list[UserGroup] | None = None
    loved_beatmapset_count: int | None = None
    mapping_follower_count: int | None = None
    monthly_playcounts: list[TimestampedCount] | None = None
    page: HTMLBody | None = None
    pending_beatmapset_count: int | None = None
    previous_usernames: list[str] | None = None
    rank_highest: UserRankHighest | None = None
    rank_history: UserRankHistoryElement | None = None
    ranked_beatmapset_count: int | None = None
    replays_watched_counts: list[TimestampedCount] | None = None
    scores_best_count: int | None = None
    scores_first_count: int | None = None
    scores_recent_count: int | None = None
    statistics: UserStats | None = None
    statistics_rulesets: UserStatsRulesets | None = None
    support_level: int | None = None
    team: UserTeam | None = None
    unread_pm_count: int | None = None
    user_achievements: list[UserAchievmement] | None = None

    blocks: list[UserRelation] | None = None
    current_user_attributes: UserCurrentAttributes | None = None
    global_rank: UserGlobalRank | None = None
    is_admin: bool | None = None
    is_bng: bool | None = None
    is_full_bn: bool | None = None
    is_gmt: bool | None = None
    is_limited_bn: bool | None = None
    is_moderator: bool | None = None
    is_nat: bool | None = None
    is_silenced: bool | None = None
    score_processing_notice_url: str | None = None
    session_verified: bool | None = None
    session_verification_method: str | None = None
    user_preferences: UserPreferences | None = None

    @computed_field  # type: ignore
    @property
    def url(self) -> str:
        return f"https://osu.ppy.sh/users/{self.id}"


class UserCompact(_UserBase):
    avatar_url: str | None
    country_code: str | None
    id: int | None
    is_active: bool
    is_bot: bool
    is_deleted: bool
    is_online: bool
    is_supporter: bool
    pm_friends_only: bool
    default_group: str | None = Field(...)
    last_visit: datetime | None = Field(...)
    profile_colour: str | None = Field(...)


class User(UserCompact):
    avatar_url: str
    country_code: str
    id: int
    country: Country | None = Field(...)
    cover: UserProfileCover
    cover_url: str
    discord: str | None
    has_supported: bool
    interests: str | None
    join_date: datetime
    kudosu: UserKudosu
    location: str | None
    max_blocks: int
    max_friends: int
    occupation: str | None
    playmode: Gamemode
    playstyle: list[str] | None
    post_count: int
    profile_hue: int | None
    profile_order: list[str]
    title: str | None
    title_url: str | None
    twitter: str | None
    website: str | None


class LegacyUser(_UserBase):
    is_active: bool | None = None
    is_bot: bool | None = None
    is_deleted: bool | None = None
    is_online: bool | None = None
    is_supporter: bool | None = None
    pm_friends_only: bool | None = None
    avatar_url: str
    country_code: str
    id: int
    discord: str | None = None
    has_supported: bool | None = None
    interests: str | None = None
    join_date: datetime | None = None
    location: str | None = None
    max_blocks: int | None = None
    max_friends: int | None = None
    occupation: str | None = None
    playmode: Gamemode | None = None
    playstyle: list[str] | None = None
    post_count: int | None = None
    profile_hue: int | None = None
    profile_order: list[str] | None = None
    title: str | None = None
    twitter: str | None = None
    website: str | None = None
    cover_url: str | None = None
    title_url: str | None = None

    @classmethod
    def _from_api_v1(cls, data: Mapping[str, object]) -> LegacyUser:
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
