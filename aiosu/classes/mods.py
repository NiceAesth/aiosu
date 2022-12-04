"""
This module contains models for mods.
"""
from __future__ import annotations

from collections import UserList
from collections.abc import Generator
from enum import Enum
from functools import reduce
from typing import Any
from typing import Union


class Mod(Enum):
    """Bitwise Flags representing osu! mods."""

    NoMod = (0, "")
    NoFail = (1, "NF")
    Easy = (2, "EZ")
    TouchDevice = (4, "TD")
    Hidden = (8, "HD")
    HardRock = (16, "HR")
    SuddenDeath = (32, "SD")
    DoubleTime = (64, "DT")
    Relax = (128, "RX")
    HalfTime = (256, "HT")
    Nightcore = (512, "NC")  # Only set along with DoubleTime. i.e: NC only gives 576
    Flashlight = (1024, "FL")
    Autoplay = (2048, "AT")
    SpunOut = (4096, "SO")
    Autopilot = (8192, "AP")  # Called Relax2 on osu! API documentation
    Perfect = (16384, "PF")  # Only set along with SuddenDeath. i.e: PF only gives 16416
    Key4 = (32768, "4K")
    Key5 = (65536, "5K")
    Key6 = (131072, "6K")
    Key7 = (262144, "7K")
    Key8 = (524288, "8K")
    FadeIn = (1048576, "FI")
    Random = (2097152, "RD")
    Key9 = (16777216, "9K")
    KeyCoop = (33554432, "CK")
    Key1 = (67108864, "1K")
    Key3 = (134217728, "3K")
    Key2 = (268435456, "2K")
    Mirror = (1073741824, "MR")

    def __init__(self, value: int, short_name: str = "") -> None:
        self.bitmask = value
        self.short_name = short_name

    def __int__(self) -> int:
        return self.bitmask

    def __str__(self) -> str:
        return self.short_name

    def __and__(self, __o: int) -> int:
        return int(self) & __o

    def __or__(self, __o: int) -> int:
        return int(self) | __o

    @classmethod
    def from_type(cls, __o: object) -> Mod:
        if isinstance(__o, cls):
            return __o
        for mod in list(Mod):
            if __o in mod.value:
                return mod
        raise ValueError(f"Mod {__o!r} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> Mod:
        return cls.from_type(query)


class Mods(UserList):
    """List of Mod objects"""

    def __init__(self, mods: Union[list[str], str, int] = []) -> None:
        super().__init__(self)
        self.data = []
        if isinstance(mods, str):  # string of mods
            mods = [mods[i : i + 2] for i in range(0, len(mods), 2)]
        if isinstance(mods, list):  # List of Mod types
            self.data = [Mod(mod) for mod in mods]  # type: ignore
        if isinstance(mods, int):  # Bitwise representation of mods
            self.data = [mod for mod in list(Mod) if mod & mods]

    @property
    def bitwise(self) -> int:
        """Bitwise representation.

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

    def __and__(self, __o: Any) -> int:
        if isinstance(__o, int):
            return int(self) & __o
        if isinstance(__o, Mod):
            return int(self) & int(__o)
        if isinstance(__o, Mods):
            return int(self) & int(__o)
        raise ValueError(f"Object {__o!r} is of invalid type.")

    def __or__(self, __o: Any) -> int:
        if isinstance(__o, int):
            return int(self) | __o
        if isinstance(__o, Mod):
            return int(self) | int(__o)
        if isinstance(__o, Mods):
            return int(self) | int(__o)
        raise ValueError(f"Object {__o!r} is of invalid type.")

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls._validate

    @classmethod
    def __modify_schema__(cls, field_schema):  # type: ignore
        pass  # Genuinely not sure about implementing this

    @classmethod
    def _validate(cls, v: object) -> Mods:
        if not isinstance(v, (list, str, int)):
            raise TypeError("Invalid type specified ")
        return cls(v)
