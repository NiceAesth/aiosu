"""
This module contains models for Gamemode objects.
"""
from __future__ import annotations

from enum import Enum


class Gamemode(Enum):
    STANDARD = (0, "https://i.imgur.com/lT2nqls.png", "Standard", "STD", "osu")
    TAIKO = (1, "https://i.imgur.com/G6bzM0X.png", "Taiko", "Taiko", "taiko")
    CTB = (2, "https://i.imgur.com/EsanYkH.png", "Catch the Beat", "CTB", "fruits")
    MANIA = (3, "https://i.imgur.com/0uZM1PZ.png", "Mania", "Mania", "mania")

    def __init__(
        self,
        id: int,
        icon: str,
        name_full: str,
        name_short: str,
        name_api: str,
    ) -> None:
        self.id: int = id
        self.icon: str = icon
        self.name_full: str = name_full
        self.name_short: str = name_short
        self.name_api: str = name_api

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
        :rtype: aiosu.classes.gamemode.Gamemode
        """
        if isinstance(__o, cls):
            return __o
        for mode in list(Gamemode):
            if __o in (mode.name_api, mode.name_short, mode.id):
                return mode
        raise ValueError(f"Gamemode {__o} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> Gamemode:
        return cls.from_type(query)
