from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import IntEnum
from enum import unique

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from ..base import BaseModel
from ..base import cast_int
from ..gamemode import Gamemode
from ..mods import Mods
from ..score import ScoreStatistics

__all__ = (
    "Match",
    "MatchGame",
    "MatchScore",
    "MatchScoringType",
    "MatchTeam",
    "MatchTeamType",
)


@unique
class MatchTeam(IntEnum):
    NONE = 0
    BLUE = 1
    RED = 2


@unique
class MatchScoringType(IntEnum):
    SCORE = 0
    ACCURACY = 1
    COMBO = 2
    SCOREV2 = 3


@unique
class MatchTeamType(IntEnum):
    HEADTOHEAD = 0
    COOP = 1
    TEAMVS = 2
    TAGTEAMVS = 3


class MatchScore(BaseModel):
    slot: int
    team: MatchTeam
    user_id: int
    score: int
    max_combo: int = Field(alias="maxcombo")
    passed: bool = Field(alias="pass")
    perfect: bool
    enabled_mods: Mods
    statistics: ScoreStatistics

    def get_full_mods(self, game: MatchGame) -> Mods:
        r"""Get the mods including globals from the match.

        :param game: The match the score took place in
        :type game: MatchGame
        :return: Mods list of Mod objects
        :rtype: Mods
        """
        return Mods(self.enabled_mods | game.mods)

    @model_validator(mode="before")
    @classmethod
    def _set_statistics(cls, values: dict[str, object]) -> dict[str, object]:
        values["statistics"] = ScoreStatistics._from_api_v1(values)
        return values

    @field_validator("enabled_mods", mode="before")
    @classmethod
    def _set_enabled_mods(cls, v: object) -> int:
        return cast_int(v)

    @field_validator("team", mode="before")
    @classmethod
    def _set_team(cls, v: object) -> int:
        return cast_int(v)


class MatchGame(BaseModel):
    """Multiplayer game API object."""

    id: int = Field(alias="game_id")
    start_time: datetime
    beatmap_id: int
    mode: Gamemode = Field(alias="play_mode")
    match_type: int
    scoring_type: MatchScoringType
    team_type: MatchTeamType
    scores: list[MatchScore]
    mods: Mods
    end_time: datetime | None = None
    """None if game was aborted."""

    @field_validator("mode", mode="before")
    @classmethod
    def _set_mode(cls, v: object) -> int:
        return cast_int(v)

    @field_validator("mods", mode="before")
    @classmethod
    def _set_mods(cls, v: object) -> int:
        return cast_int(v)

    @field_validator("scoring_type", mode="before")
    @classmethod
    def _set_scoring_type(cls, v: object) -> int:
        return cast_int(v)

    @field_validator("team_type", mode="before")
    @classmethod
    def _set_team_type(cls, v: object) -> int:
        return cast_int(v)


class Match(BaseModel):
    """Multiplayer match API object."""

    id: int = Field(alias="match_id")
    name: str
    start_time: datetime
    games: list[MatchGame]
    end_time: datetime | None = None
    """None if game is ongoing."""

    @model_validator(mode="before")
    @classmethod
    def _format_values(cls, values: dict[str, object]) -> dict[str, object]:
        match = values["match"]
        if not isinstance(match, Mapping):
            raise ValueError(f"Invalid match type: {type(match)}")

        return {**match, "games": values["games"]}
