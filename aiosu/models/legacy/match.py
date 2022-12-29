from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import Field
from pydantic import root_validator
from pydantic import validator

from ..base import BaseModel
from ..gamemode import Gamemode
from ..mods import Mods
from ..score import ScoreStatistics

if TYPE_CHECKING:
    from typing import Any


class MatchTeam(Enum):
    NONE = 0
    BLUE = 1
    RED = 2


class MatchScoringType(Enum):
    SCORE = 0
    ACCURACY = 1
    COMBO = 2
    SCOREV2 = 3


class MatchTeamType(Enum):
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
        """Get the mods including globals from the match.

        :param game: The match the score took place in
        :type game: MatchGame
        :return: Mods list of Mod objects
        :rtype: Mods
        """
        return Mods(self.enabled_mods | game.mods)

    @root_validator(pre=True)
    def _set_statistics(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["statistics"] = ScoreStatistics._from_api_v1(values)
        return values

    @validator("enabled_mods", pre=True)
    def _set_enabled_mods(cls, v: Any) -> int:
        if v is not None:
            return int(v)
        return 0

    @validator("team", pre=True)
    def _set_team(cls, v: Any) -> int:
        return int(v)


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
    end_time: Optional[datetime]
    """None if game was aborted."""

    @validator("mode", pre=True)
    def _set_mode(cls, v: Any) -> int:
        return int(v)

    @validator("mods", pre=True)
    def _set_mods(cls, v: Any) -> int:
        if v is not None:
            return int(v)
        return 0

    @validator("scoring_type", pre=True)
    def _set_scoring_type(cls, v: Any) -> int:
        return int(v)

    @validator("team_type", pre=True)
    def _set_team_type(cls, v: Any) -> int:
        return int(v)


class Match(BaseModel):
    """Multiplayer match API object."""

    id: int = Field(alias="match_id")
    name: str
    start_time: datetime
    games: list[MatchGame]
    end_time: Optional[datetime]
    """None if game is ongoing."""

    @root_validator(pre=True)
    def _format_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        return {**values["match"], "games": values["games"]}
