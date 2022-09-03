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

    @staticmethod
    def from_id(id) -> Gamemode:
        if not isinstance(id, int):
            id = int(id)

        for mode in list(Gamemode):
            if mode.id == id:
                return mode

    @staticmethod
    def from_name_short(name_short) -> Gamemode:
        for mode in list(Gamemode):
            if mode.name_short == name_short:
                return mode

    @staticmethod
    def from_api_name(name_api) -> Gamemode:
        for mode in list(Gamemode):
            if mode.name_api == name_api:
                return mode
