"""
This module contains models for Gamemode objects.
"""
from __future__ import annotations

from enum import Enum
from enum import unique

__all__ = ("Gamemode",)

GAMEMODE_NAMES = {
    0: "Standard",
    1: "Taiko",
    2: "Catch the Beat",
    3: "Mania",
}

GAMEMODE_SHORT_NAMES = {
    0: "STD",
    1: "Taiko",
    2: "CTB",
    3: "Mania",
}

GAMEMODE_API_NAMES = {
    0: "osu",
    1: "taiko",
    2: "fruits",
    3: "mania",
}


@unique
class Gamemode(Enum):
    STANDARD = 0
    TAIKO = 1
    CTB = 2
    MANIA = 3

    @property
    def id(self) -> int:
        return self.value

    @property
    def name_full(self) -> str:
        return GAMEMODE_NAMES[self.id]

    @property
    def name_short(self) -> str:
        return GAMEMODE_SHORT_NAMES[self.id]

    @property
    def name_api(self) -> str:
        return GAMEMODE_API_NAMES[self.id]

    def __int__(self) -> int:
        return self.id

    def __str__(self) -> str:
        return self.name_api

    def __format__(self, spec: str) -> str:
        if spec == "f":
            return self.name_full
        if spec == "s":
            return self.name_short
        return self.name_api

    @classmethod
    def from_type(cls, __o: object) -> Gamemode:
        """Gets a gamemode.

        :param __o: Object to search for
        :type __o: object
        :raises ValueError: If object cannot be converted to Gamemode
        :return: A Gamemode object. Will search by name_api, name_short, id
        :rtype: aiosu.models.gamemode.Gamemode
        """
        if isinstance(__o, cls):
            return __o
        for mode in list(Gamemode):
            if __o in (mode.name_api, mode.name_short, mode.name_full, mode.id):
                return mode
        raise ValueError(f"Gamemode {__o} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> Gamemode:
        return cls.from_type(query)
