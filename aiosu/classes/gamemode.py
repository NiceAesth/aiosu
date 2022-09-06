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

    def __repr__(self) -> str:
        return self.name_api

    def __format__(self, spec):
        if spec == "f":
            return self.name_full
        if spec == "s":
            return self.name_short
        return self.name_api

    @classmethod
    def _missing_(cls, query) -> Gamemode:
        for mode in list(Gamemode):
            if query in (mode.name_api, mode.name_short, mode.id):
                return mode
