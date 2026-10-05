"""
This module contains models for Score objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

from pydantic import Field
from pydantic import PrivateAttr
from pydantic import computed_field
from pydantic import field_serializer
from pydantic import model_serializer
from pydantic import model_validator

from ..utils.accuracy import CatchAccuracyCalculator
from ..utils.accuracy import ManiaAccuracyCalculator
from ..utils.accuracy import OsuAccuracyCalculator
from ..utils.accuracy import TaikoAccuracyCalculator
from .base import BaseModel
from .base import cast_int
from .beatmap import BeatmapExtended
from .beatmap import Beatmapset
from .beatmap import LegacyBeatmap
from .beatmap import LegacyBeatmapset
from .common import CurrentUserAttributes
from .common import CursorModel
from .common import ScoreType
from .gamemode import Gamemode
from .mods import Mods
from .user import UserCompact

if TYPE_CHECKING:
    from typing import Self

    from pydantic import ModelWrapValidatorHandler
    from pydantic import SerializationInfo
    from pydantic import SerializerFunctionWrapHandler
    from pydantic import ValidationInfo

    from .. import v1

__all__ = (
    "Score",
    "ScoreMatch",
    "ScoreRoomSummary",
    "ScoreScoresAround",
    "ScoreScoresParams",
    "ScoreScoresResponse",
    "ScoreStatistics",
    "ScoreWeight",
    "calculate_score_completion",
)

accuracy_calculators = {
    "osu": OsuAccuracyCalculator(),
    "mania": ManiaAccuracyCalculator(),
    "taiko": TaikoAccuracyCalculator(),
    "fruits": CatchAccuracyCalculator(),
}


def calculate_score_completion(
    mode: Gamemode,
    statistics: ScoreStatistics,
    beatmap: BeatmapExtended | LegacyBeatmap,
) -> float | None:
    """Calculates completion for a score.

    :param mode: The gamemode of the score
    :type mode: aiosu.models.gamemode.Gamemode
    :param statistics: The statistics of the score
    :type statistics: aiosu.models.score.ScoreStatistics
    :param beatmap: The beatmap of the score
    :type beatmap: aiosu.models.beatmap.Beatmap
    :raises ValueError: If the gamemode is unknown
    :return: Completion for the given score
    :rtype: Optional[float]
    """
    if not beatmap.count_objects:
        return None

    if mode == Gamemode.STANDARD:
        return (
            (
                statistics.count_300
                + statistics.count_100
                + statistics.count_50
                + statistics.count_miss
            )
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.TAIKO:
        return (
            (statistics.count_300 + statistics.count_100 + statistics.count_miss)
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.CTB:
        return (
            (statistics.count_300 + statistics.count_100 + statistics.count_miss)
            / beatmap.count_objects
        ) * 100
    elif mode == Gamemode.MANIA:
        return (
            (
                statistics.count_300
                + statistics.count_100
                + statistics.count_50
                + statistics.count_miss
                + statistics.count_geki
                + statistics.count_katu
            )
            / beatmap.count_objects
        ) * 100

    raise ValueError("Unknown mode specified.")


class ScoreWeight(BaseModel):
    percentage: float
    pp: float


class ScoreMatch(BaseModel):

    slot: int
    team: str
    passed: bool = Field(validation_alias="pass")


class ScoreStatistics(BaseModel):
    miss: int = 0
    meh: int = 0
    ok: int = 0
    good: int = 0
    great: int = 0
    perfect: int = 0
    small_tick_miss: int = 0
    small_tick_hit: int = 0
    large_tick_hit: int = 0
    small_bonus: int = 0
    large_bonus: int = 0
    ignore_miss: int = 0
    ignore_hit: int = 0
    combo_break: int = 0
    large_tick_miss: int | None = None
    slider_tail_hit: int | None = None
    legacy_combo_increase: int = 0
    _uses_hit_results: bool = PrivateAttr(default=False)
    _mode: Gamemode = PrivateAttr(default=Gamemode.STANDARD)
    _taiko_count_katu: int = PrivateAttr(default=0)

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        copied = super().model_copy(update=update, deep=deep)
        for name, value in (update or {}).items():
            attribute = getattr(type(self), name, None)
            if isinstance(attribute, property) and attribute.fset is not None:
                copied.__dict__.pop(name, None)
                copied.model_fields_set.discard(name)
                setattr(copied, name, value)
        return copied

    def _with_mode(self, mode: Gamemode) -> Self:
        if self._mode == mode:
            return self
        if not self._uses_hit_results:
            return type(self).model_validate(
                self.model_dump(exclude_none=True),
                context={"mode": mode},
            )
        statistics = self.model_copy()
        statistics._mode = mode
        statistics._taiko_count_katu = 0
        return statistics

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_300(self) -> int:
        return self.great

    @count_300.setter
    def count_300(self, value: int) -> None:
        self.great = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_100(self) -> int:
        if self._mode == Gamemode.CTB:
            return self.large_tick_hit
        return self.ok

    @count_100.setter
    def count_100(self, value: int) -> None:
        if self._mode == Gamemode.CTB:
            self.large_tick_hit = value
        else:
            self.ok = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_50(self) -> int:
        if self._mode == Gamemode.CTB:
            return self.small_tick_hit
        return self.meh

    @count_50.setter
    def count_50(self, value: int) -> None:
        if self._mode == Gamemode.CTB:
            self.small_tick_hit = value
        else:
            self.meh = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_geki(self) -> int:
        if self._mode == Gamemode.TAIKO:
            return self.large_bonus - self._taiko_count_katu
        return self.perfect

    @count_geki.setter
    def count_geki(self, value: int) -> None:
        if self._mode == Gamemode.TAIKO:
            self.large_bonus = value + self._taiko_count_katu
        else:
            self.perfect = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_katu(self) -> int:
        if self._mode == Gamemode.CTB:
            return self.small_tick_miss
        if self._mode == Gamemode.TAIKO:
            return self._taiko_count_katu
        return self.good

    @count_katu.setter
    def count_katu(self, value: int) -> None:
        if self._mode == Gamemode.CTB:
            self.small_tick_miss = value
        elif self._mode == Gamemode.TAIKO:
            if self._uses_hit_results:
                raise ValueError("Set large_bonus directly for modern taiko scores")
            self.large_bonus = self.count_geki + value
            self._taiko_count_katu = value
        else:
            self.good = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_miss(self) -> int:
        if self._mode == Gamemode.CTB:
            return self.miss + cast_int(self.large_tick_miss)
        return self.miss

    @count_miss.setter
    def count_miss(self, value: int) -> None:
        if self._mode == Gamemode.CTB:
            if self._uses_hit_results:
                raise ValueError(
                    "Set miss or large_tick_miss separately for catch scores",
                )
            self.miss = value - cast_int(self.large_tick_miss)
        else:
            self.miss = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_large_tick_miss(self) -> int | None:
        return self.large_tick_miss

    @count_large_tick_miss.setter
    def count_large_tick_miss(self, value: int | None) -> None:
        if self._mode == Gamemode.CTB and not self._uses_hit_results:
            self.miss += cast_int(self.large_tick_miss) - cast_int(value)
        self.large_tick_miss = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count_slider_tail_hit(self) -> int | None:
        return self.slider_tail_hit

    @count_slider_tail_hit.setter
    def count_slider_tail_hit(self, value: int | None) -> None:
        self.slider_tail_hit = value

    @classmethod
    def _from_api_v1(
        cls,
        data: Mapping[str, object],
        mode: Gamemode = Gamemode.STANDARD,
    ) -> ScoreStatistics:
        return cls.model_validate(
            {
                "count_50": data["count50"],
                "count_100": data["count100"],
                "count_300": data["count300"],
                "count_geki": data["countgeki"],
                "count_katu": data["countkatu"],
                "count_miss": data["countmiss"],
            },
            context={"mode": mode},
        )

    @model_validator(mode="wrap")
    @classmethod
    def _normalize_statistics(
        cls,
        values: Any,
        handler: ModelWrapValidatorHandler[ScoreStatistics],
        info: ValidationInfo,
    ) -> ScoreStatistics:
        if not isinstance(values, Mapping):
            return handler(values)

        data = dict(values)
        # Lazer API returns null for some statistics
        for name, count in data.items():
            if count is None:
                data[name] = 0

        uses_hit_results = True
        for name in data:
            if name.startswith("count_"):
                uses_hit_results = False
                break

        context = info.context or {}
        mode = Gamemode(context.get("mode", Gamemode.STANDARD))
        if uses_hit_results:
            data.setdefault("large_tick_miss", 0)
            data.setdefault("slider_tail_hit", 0)
        else:
            for name in (
                "count_miss",
                "count_50",
                "count_100",
                "count_300",
                "count_geki",
                "count_katu",
            ):
                if name not in data:
                    raise ValueError(f"Missing legacy statistic {name!r}")
            data = cls._hit_results_from_legacy_counts(data, mode)

        statistics = handler(data)
        statistics._uses_hit_results = uses_hit_results
        statistics._mode = mode
        if not uses_hit_results and mode == Gamemode.TAIKO:
            statistics._taiko_count_katu = cast_int(values.get("count_katu"))
        return statistics

    @model_serializer(mode="wrap")
    def _serialize_statistics(
        self,
        handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ) -> dict[str, Any]:
        data = handler(self)
        result = {}
        for name, count in data.items():
            is_legacy_count = name.startswith("count_")
            if self._uses_hit_results and is_legacy_count:
                continue
            if not self._uses_hit_results:
                if not is_legacy_count:
                    continue
                if name in ("count_large_tick_miss", "count_slider_tail_hit"):
                    if info.exclude_defaults and count is None:
                        continue
                    if info.exclude_unset and name[6:] not in self.model_fields_set:
                        continue
            result[name] = count
        return result

    @staticmethod
    def _hit_results_from_legacy_counts(
        data: Mapping[str, Any],
        mode: Gamemode,
    ) -> dict[str, Any]:
        hit_results = {
            "great": data.get("count_300", 0),
            "miss": data.get("count_miss", 0),
        }

        if "count_large_tick_miss" in data:
            hit_results["large_tick_miss"] = data["count_large_tick_miss"]
        if "count_slider_tail_hit" in data:
            hit_results["slider_tail_hit"] = data["count_slider_tail_hit"]

        if mode == Gamemode.CTB:
            hit_results["miss"] = cast_int(data.get("count_miss")) - cast_int(
                data.get("count_large_tick_miss"),
            )
            hit_results["perfect"] = data.get("count_geki", 0)
            hit_results["large_tick_hit"] = data.get("count_100", 0)
            hit_results["small_tick_hit"] = data.get("count_50", 0)
            hit_results["small_tick_miss"] = data.get("count_katu", 0)
            return hit_results

        hit_results["ok"] = data.get("count_100", 0)
        hit_results["meh"] = data.get("count_50", 0)
        if mode == Gamemode.TAIKO:
            hit_results["large_bonus"] = cast_int(data.get("count_geki")) + cast_int(
                data.get("count_katu"),
            )
        else:
            hit_results["perfect"] = data.get("count_geki", 0)
            hit_results["good"] = data.get("count_katu", 0)

        return hit_results


class ScoreRoomSummary(BaseModel):
    playlist_item_id: int
    is_realtime: bool
    room_id: int
    room_name: str


class ScoreScoresParams(BaseModel):
    limit: int
    sort: Literal["score_asc", "score_desc"]


class ScoreScoresResponse(CursorModel):
    scores: list[Score]
    params: ScoreScoresParams


class ScoreScoresAround(BaseModel):
    higher: ScoreScoresResponse
    lower: ScoreScoresResponse


class Score(BaseModel):
    user_id: int
    accuracy: float
    mods: Mods
    score: int
    max_combo: int
    passed: bool
    perfect: bool
    statistics: ScoreStatistics
    rank: str
    created_at: datetime
    mode: Gamemode
    replay: bool
    type: ScoreType = "solo_score"
    id: int | None = None
    """Always present except for API v1 recent scores."""
    pp: float | None = 0
    best_id: int | None = None
    beatmap: BeatmapExtended | LegacyBeatmap | None = None
    beatmapset: Beatmapset | LegacyBeatmapset | None = None
    weight: ScoreWeight | None = None
    user: UserCompact | None = None
    rank_global: int | None = None
    rank_country: int | None = None
    current_user_attributes: CurrentUserAttributes | None = None
    beatmap_id: int | None = None
    """Only present on API v1"""
    replay_views: int | None = None
    is_perfect_combo: bool | None = None
    maximum_statistics: ScoreStatistics | None = None
    classic_total_score: int | None = None
    total_score_without_mods: int | None = None
    legacy_score_id: int | None = None
    legacy_total_score: int | None = None
    build_id: int | None = None
    preserve: bool | None = None
    processed: bool | None = None
    position: int | None = None
    ranked: bool | None = None
    playlist_item_id: int | None = None
    room_id: int | None = None
    solo_score_id: int | None = None
    started_at: datetime | None = None
    match: ScoreMatch | None = None
    room_summary: ScoreRoomSummary | None = None
    scores_around: ScoreScoresAround | None = None

    _is_lazer: bool = PrivateAttr(default=False)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "mode":
            value = Gamemode(value)
            for field in ("statistics", "maximum_statistics"):
                statistics = self.__dict__.get(field)
                if isinstance(statistics, ScoreStatistics):
                    super().__setattr__(field, statistics._with_mode(value))
        super().__setattr__(name, value)

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        copied = super().model_copy(update=update, deep=deep)
        for name, value in (update or {}).items():
            attribute = getattr(type(self), name, None)
            if name == "mode":
                copied.mode = Gamemode(value)
            elif isinstance(attribute, property) and attribute.fset is not None:
                copied.__dict__.pop(name, None)
                copied.model_fields_set.discard(name)
                setattr(copied, name, value)
        return copied

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_score(self) -> int:
        return self.score

    @total_score.setter
    def total_score(self, value: int) -> None:
        self.score = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ended_at(self) -> datetime:
        return self.created_at

    @ended_at.setter
    def ended_at(self, value: datetime) -> None:
        self.created_at = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_replay(self) -> bool:
        return self.replay

    @has_replay.setter
    def has_replay(self, value: bool) -> None:
        self.replay = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ruleset_id(self) -> int:
        return int(self.mode)

    @ruleset_id.setter
    def ruleset_id(self, value: int) -> None:
        self.mode = Gamemode(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def legacy_perfect(self) -> bool:
        return self.perfect

    @legacy_perfect.setter
    def legacy_perfect(self, value: bool) -> None:
        self.perfect = value

    @property
    def mods_str(self) -> str:
        return str(self.mods)

    @property
    def score_url(self) -> str | None:
        r"""Link to the score.

        :return: Link to the score on the osu! website
        :rtype: Optional[str]
        """
        if not self.id:
            return None
        if self.type == "solo_score":
            return f"https://osu.ppy.sh/scores/{self.id}"

        if not self.best_id or not self.passed:  # Legacy URL format
            return None
        return f"https://osu.ppy.sh/scores/{self.mode.name_api}/{self.best_id}"

    @property
    def replay_url(self) -> str | None:
        r"""Link to the replay.

        :return: Link to download the replay on the osu! website
        :rtype: Optional[str]
        """
        if not self.replay:
            return None
        score_url = self.score_url
        if not score_url:
            return None
        return score_url + "/download"

    @computed_field  # type: ignore
    @cached_property
    def completion(self) -> float | None:
        """Beatmap completion.

        :raises ValueError: If mode is unknown
        :return: Beatmap completion of a score (%). 100% for passes. None if no beatmap.
        :rtype: Optional[float]
        """
        if not self.beatmap:
            return None

        if self.passed:
            return 100.0

        return calculate_score_completion(self.mode, self.statistics, self.beatmap)

    async def request_beatmap(self, client: v1.Client) -> None:
        r"""For v1 Scores: requests the beatmap from the API and sets it.

        :param client: An API v1 Client
        :type client: aiosu.v1.client.Client
        """
        if self.beatmap_id is None:
            raise ValueError("Score has unknown beatmap ID")
        if self.beatmap is None and self.beatmapset is None:
            sets = await client.get_beatmap(
                mode=self.mode,
                beatmap_id=self.beatmap_id,
            )
            self.beatmapset = sets[0]
            self.beatmap = sets[0].beatmaps[0]  # type: ignore

    @classmethod
    def _from_api_v1(
        cls,
        data: Mapping[str, object],
        mode: Gamemode,
    ) -> Score:
        statistics = ScoreStatistics._from_api_v1(data, mode)
        score = cls.model_validate(
            {
                "id": data["score_id"],
                "user_id": data["user_id"],
                "accuracy": 0.0,
                "mods": cast_int(data["enabled_mods"]),
                "score": data["score"],
                "pp": data.get("pp", 0.0),
                "max_combo": data["maxcombo"],
                "passed": data["rank"] != "F",
                "perfect": data["perfect"],
                "statistics": statistics,
                "rank": data["rank"],
                "created_at": data["date"],
                "mode": mode,
                "beatmap_id": data.get("beatmap_id"),
                "replay": data.get("replay_available", False),
            },
        )
        score.accuracy = accuracy_calculators[str(mode)].calculate(score)
        return score

    @model_validator(mode="wrap")
    @classmethod
    def _record_format(
        cls,
        values: Any,
        handler: ModelWrapValidatorHandler[Score],
        info: ValidationInfo,
    ) -> Score:
        score = handler(values)
        if isinstance(values, Mapping):
            score._is_lazer = "ruleset_id" in values
        return score

    @model_validator(mode="before")
    @classmethod
    def _normalize_score(cls, values: Any) -> Any:
        if not isinstance(values, Mapping):
            return values
        values = dict(values)
        if "ruleset_id" in values:
            values["mode"] = values["ruleset_id"]
            if "total_score" in values:
                values["score"] = values["total_score"]
            if "ended_at" in values:
                values["created_at"] = values["ended_at"]

            if "has_replay" in values:
                values["replay"] = values["has_replay"]
            elif "replay" not in values:
                values["replay"] = False

            if "legacy_perfect" in values:
                values["perfect"] = values["legacy_perfect"]
            else:
                values["perfect"] = values.get("is_perfect_combo", False)

        if values.get("mode") is None:
            return values
        mode = Gamemode(values["mode"])
        statistics = values.get("statistics")
        if isinstance(statistics, ScoreStatistics):
            statistics = statistics.model_dump(exclude_none=True)
        if isinstance(statistics, Mapping):
            values["statistics"] = ScoreStatistics.model_validate(
                statistics,
                context={"mode": mode},
            )

        maximum_statistics = values.get("maximum_statistics")
        if isinstance(maximum_statistics, ScoreStatistics):
            maximum_statistics = maximum_statistics.model_dump(exclude_none=True)
        if isinstance(maximum_statistics, Mapping):
            values["maximum_statistics"] = ScoreStatistics.model_validate(
                maximum_statistics,
                context={"mode": mode},
            )
        return values

    @model_validator(mode="before")
    @classmethod
    def _fail_rank(cls, values: Any) -> Any:
        if not isinstance(values, Mapping):
            return values
        values = dict(values)
        if values.get("passed") is False:
            values["rank"] = "F"
        return values

    @field_serializer("mods", when_used="json")
    def _serialize_mods(self, mods: Mods) -> Any:
        if not self._is_lazer:
            return mods.to_acronyms()
        return mods.to_api()

    @model_serializer(mode="wrap")
    def _serialize_score(
        self,
        handler: SerializerFunctionWrapHandler,
    ) -> dict[str, Any]:
        data = handler(self)
        if self._is_lazer:
            for key in ("score", "created_at", "replay", "mode", "perfect"):
                data.pop(key, None)
        else:
            for key in (
                "total_score",
                "ended_at",
                "has_replay",
                "ruleset_id",
                "is_perfect_combo",
                "legacy_perfect",
                "maximum_statistics",
                "classic_total_score",
                "total_score_without_mods",
                "legacy_score_id",
                "legacy_total_score",
                "build_id",
                "preserve",
                "processed",
                "position",
                "ranked",
                "playlist_item_id",
                "room_id",
                "solo_score_id",
                "started_at",
                "match",
                "room_summary",
                "scores_around",
            ):
                if key not in self.model_fields_set:
                    data.pop(key, None)
        return data
