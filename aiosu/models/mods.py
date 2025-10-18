"""
This module contains models for mods.
"""

from __future__ import annotations

from collections import UserList
from enum import IntEnum
from enum import unique
from functools import reduce
from typing import TYPE_CHECKING

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema
from pydantic_core import core_schema

if TYPE_CHECKING:
    pass

__all__ = (
    "FreemodAllowed",
    "KeyMod",
    "Mod",
    "Mods",
    "ScoreIncreaseMods",
    "SpeedChangingMods",
)

_mod_short_names = {
    "NoMod": "NM",
    "NoFail": "NF",
    "Easy": "EZ",
    "TouchDevice": "TD",
    "Hidden": "HD",
    "HardRock": "HR",
    "SuddenDeath": "SD",
    "DoubleTime": "DT",
    "Relax": "RX",
    "HalfTime": "HT",
    "Nightcore": "NC",
    "Flashlight": "FL",
    "Autoplay": "AT",
    "SpunOut": "SO",
    "Autopilot": "AP",
    "Perfect": "PF",
    "Key4": "4K",
    "Key5": "5K",
    "Key6": "6K",
    "Key7": "7K",
    "Key8": "8K",
    "FadeIn": "FI",
    "Random": "RD",
    "Cinema": "CN",
    "Target": "TP",
    "Key9": "9K",
    "KeyCoop": "CO",
    "Key1": "1K",
    "Key3": "3K",
    "Key2": "2K",
    "ScoreV2": "SV2",
    "Mirror": "MR",
}


@unique
class Mod(IntEnum):
    """Bitwise Flags representing osu! mods."""

    NoMod = 0
    NoFail = 1 << 0
    Easy = 1 << 1
    TouchDevice = 1 << 2
    Hidden = 1 << 3
    HardRock = 1 << 4
    SuddenDeath = 1 << 5
    DoubleTime = 1 << 6
    Relax = 1 << 7
    HalfTime = 1 << 8
    Nightcore = 1 << 9
    """Only set along with DoubleTime. i.e: NC only gives 576"""
    Flashlight = 1 << 10
    Autoplay = 1 << 11
    SpunOut = 1 << 12
    Autopilot = 1 << 13
    """Called Relax2 on osu! API documentation"""
    Perfect = 1 << 14
    """Only set along with SuddenDeath. i.e: PF only gives 16416"""
    Key4 = 1 << 15
    Key5 = 1 << 16
    Key6 = 1 << 17
    Key7 = 1 << 18
    Key8 = 1 << 19
    FadeIn = 1 << 20
    Random = 1 << 21
    Cinema = 1 << 22
    Target = 1 << 23
    Key9 = 1 << 24
    KeyCoop = 1 << 25
    Key1 = 1 << 26
    Key3 = 1 << 27
    Key2 = 1 << 28
    ScoreV2 = 1 << 29
    Mirror = 1 << 30

    @property
    def bitmask(self) -> int:
        return self.value

    @property
    def short_name(self) -> str:
        return _mod_short_names[self.name]

    def __str__(self) -> str:
        return self.short_name

    @classmethod
    def from_type(cls, __o: object) -> Mod:
        """Get a Mod from a string or int.

        :param __o: The string or int to get the Mod from
        :type __o: object
        :return: The Mod
        :rtype: Mod
        :raises ValueError: If the Mod does not exist
        """
        from .lazer import LazerMod  # Lazy import to avoid circular imports

        if isinstance(__o, cls):
            return __o
        if isinstance(__o, LazerMod):  # Attempt lossy conversion to stable mods
            try:
                return cls.from_type(__o.acronym)
            except ValueError:
                return cls.NoMod
        for mod in list(Mod):
            if __o == mod.short_name or __o == mod.bitmask:
                return mod
        raise ValueError(f"Mod {__o!r} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> Mod:
        return cls.from_type(query)


class Mods(UserList):
    """List of Mod objects"""

    def __init__(self, mods: list[str] | str | int) -> None:
        super().__init__(self)
        self.data = []
        if isinstance(mods, str):  # string of mods
            mods = [mods[i : i + 2] for i in range(0, len(mods), 2)]

        if isinstance(mods, int):  # Bitwise representation of mods
            self.data = [mod for mod in list(Mod) if mod & mods]
        elif isinstance(mods, list) or isinstance(mods, Mods):  # List of Mod types
            self.data = [Mod(mod) for mod in mods]  # type: ignore
        else:
            raise TypeError(
                f"Mods must be a list of Mod types, a string, or an int. Not {type(mods)}",
            )

        if Mod.Nightcore in self and Mod.DoubleTime not in self:
            self.data.append(Mod.DoubleTime)
        if Mod.Perfect in self and Mod.SuddenDeath not in self:
            self.data.append(Mod.SuddenDeath)

    @property
    def bitwise(self) -> int:
        r"""Bitwise representation.

        :return: Bitwise representation of the mod combination
        :rtype: int
        """
        return reduce(lambda x, y: int(x) | int(y), self, 0)

    def __str__(self) -> str:
        if len(self) == 0:
            return "NM"

        result: str = ""
        for mod in self:
            if Mod.Nightcore in self and mod is Mod.DoubleTime:
                continue
            if Mod.Perfect in self and mod is Mod.SuddenDeath:
                continue

            result += mod.short_name
        return result

    def __int__(self) -> int:
        return self.bitwise

    def __and__(self, __o: object) -> int:
        if isinstance(__o, (int, Mod, Mods)):
            return int(self) & int(__o)

        return NotImplemented

    def __or__(self, __o: object) -> int:
        if isinstance(__o, (int, Mod, Mods)):
            return int(self) | int(__o)

        return NotImplemented

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type[object],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_before_validator_function(
            cls,
            core_schema.json_or_python_schema(
                json_schema=core_schema.list_schema(),
                python_schema=handler(source_type),
            ),
            serialization=core_schema.to_string_ser_schema(when_used="json"),
        )


KeyMod = (
    Mod.Key1
    | Mod.Key2
    | Mod.Key3
    | Mod.Key4
    | Mod.Key5
    | Mod.Key6
    | Mod.Key7
    | Mod.Key8
    | Mod.Key9
    | Mod.KeyCoop
)
FreemodAllowed = (
    Mod.NoFail
    | Mod.Easy
    | Mod.Hidden
    | Mod.HardRock
    | Mod.SuddenDeath
    | Mod.Flashlight
    | Mod.Relax
    | Mod.SpunOut
    | Mod.Autopilot
    | Mod.Perfect
    | Mod.Key4
    | Mod.Key5
    | Mod.Key6
    | Mod.Key7
    | Mod.Key8
    | Mod.FadeIn
    | Mod.Random
    | Mod.Key9
    | Mod.KeyCoop
    | Mod.Key1
    | Mod.Key3
    | Mod.Key2
    | Mod.Mirror
)
ScoreIncreaseMods = Mod.Hidden | Mod.HardRock | Mod.DoubleTime | Mod.Flashlight
SpeedChangingMods = Mod.DoubleTime | Mod.HalfTime | Mod.Nightcore
