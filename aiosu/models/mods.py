"""
This module contains models for mods.
"""

from __future__ import annotations

from collections import UserList
from typing import Any

from pydantic import ConfigDict
from pydantic import Field
from pydantic import GetCoreSchemaHandler
from pydantic import field_validator
from pydantic import model_validator
from pydantic_core import CoreSchema
from pydantic_core import core_schema

from .base import BaseModel

__all__ = (
    "FreemodAllowed",
    "KeyMod",
    "Mod",
    "Mods",
    "ScoreIncreaseMods",
    "SpeedChangingMods",
)

_legacy_mods = {
    "NM": "NoMod",
    "NF": "NoFail",
    "EZ": "Easy",
    "TD": "TouchDevice",
    "HD": "Hidden",
    "HR": "HardRock",
    "SD": "SuddenDeath",
    "DT": "DoubleTime",
    "RX": "Relax",
    "HT": "HalfTime",
    "NC": "Nightcore",
    "FL": "Flashlight",
    "AT": "Autoplay",
    "SO": "SpunOut",
    "AP": "Autopilot",
    "PF": "Perfect",
    "4K": "Key4",
    "5K": "Key5",
    "6K": "Key6",
    "7K": "Key7",
    "8K": "Key8",
    "FI": "FadeIn",
    "RD": "Random",
    "CN": "Cinema",
    "TP": "Target",
    "9K": "Key9",
    "CO": "KeyCoop",
    "1K": "Key1",
    "3K": "Key3",
    "2K": "Key2",
    "V2": "ScoreV2",
    "MR": "Mirror",
}


class _LegacyModFlags:
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


class Mod(BaseModel, _LegacyModFlags):
    """An osu! mod with optional settings."""

    model_config = ConfigDict(frozen=True)
    acronym: str
    settings: dict[str, Any] = Field(default_factory=dict)
    __hash__: Any = None

    def __init__(self, acronym: str | int, **data: Any) -> None:
        super().__init__(acronym=acronym, **data)

    @property
    def name(self) -> str:
        return _legacy_mods.get(self.acronym, self.acronym)

    @property
    def value(self) -> int:
        return int(self)

    @property
    def bitmask(self) -> int:
        return int(self)

    @property
    def short_name(self) -> str:
        if self.acronym == "V2":
            return "SV2"
        return self.acronym

    @classmethod
    def from_type(cls, __o: object) -> Mod:
        """Get a Mod from a string or int.

        :param __o: The string or int to get the Mod from
        :type __o: object
        :return: The Mod
        :rtype: Mod
        :raises ValueError: If the Mod does not exist
        """
        if isinstance(__o, cls):
            return __o
        return cls.model_validate(__o)

    def __str__(self) -> str:
        return self.short_name

    def __int__(self) -> int:
        if self.settings:
            raise ValueError(
                f"Mod {self.acronym!r} has settings which cannot be represented by a legacy flag",
            )
        if self.acronym not in _legacy_mods:
            raise ValueError(f"Mod {self.acronym!r} has no legacy flag")
        return getattr(type(self), _legacy_mods[self.acronym])

    def __index__(self) -> int:
        return int(self)

    def __bool__(self) -> bool:
        return self.acronym != "NM"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mod):
            return self.acronym == other.acronym and self.settings == other.settings
        if isinstance(other, int):
            if self.settings:
                return False
            if self.acronym not in _legacy_mods:
                return False
            return int(self) == other
        return NotImplemented

    def __and__(self, other: object) -> Mods:
        return Mods([self]).__and__(other)

    def __rand__(self, other: object) -> Mods:
        return Mods([self]).__rand__(other)

    def __or__(self, other: object) -> Mods:
        return Mods([self]).__or__(other)

    def __ror__(self, other: object) -> Mods:
        return Mods([self]).__ror__(other)

    def __xor__(self, other: object) -> Mods:
        return Mods([self]).__xor__(other)

    def __rxor__(self, other: object) -> Mods:
        return Mods([self]).__rxor__(other)

    def __invert__(self) -> Mods:
        return ~Mods([self])

    @model_validator(mode="before")
    @classmethod
    def _from_value(cls, value: Any) -> Any:
        if isinstance(value, (str, int)):
            return {"acronym": value}
        return value

    @field_validator("acronym", mode="before")
    @classmethod
    def _convert_acronym(cls, value: Any) -> Any:
        if isinstance(value, int):
            for acronym, name in _legacy_mods.items():
                if getattr(cls, name) == value:
                    return acronym
            raise ValueError(f"Mod {value!r} does not exist.")
        if value == "SV2":
            return "V2"
        return value


class Mods(UserList[Mod]):
    """List of Mod objects"""

    def __init__(self, mods: list[Any] | str | int | Mod | Mods = "") -> None:
        super().__init__()

        if isinstance(mods, Mod):
            mods = [mods]
        elif isinstance(mods, str):
            mods = self._parse_string(mods)
        elif isinstance(mods, int):
            mods = self._parse_bitmask(mods)
        elif not isinstance(mods, (list, Mods)):
            raise TypeError(
                f"Mods must be a list of Mod types, a string, or an int. Not {type(mods)}",
            )

        for value in mods:
            self.data.append(Mod.from_type(value))

        self._add_implied_mods()

    @property
    def bitwise(self) -> int:
        r"""Bitwise representation.

        :return: Bitwise representation of the mod combination
        :rtype: int
        """
        result = 0
        for mod in self:
            result |= int(mod)
        if Mod.Nightcore in self:
            result |= int(Mod.DoubleTime)
        if Mod.Perfect in self:
            result |= int(Mod.SuddenDeath)
        return result

    def to_api(self) -> list[dict[str, object]]:
        result = []
        for mod in self.data:
            if mod.acronym == "NM":
                continue
            if self._is_implied(mod):
                continue
            result.append(mod.model_dump(exclude_unset=True))
        return result

    def to_acronyms(self) -> list[str]:
        acronyms = []
        for mod in self.data:
            if mod.acronym == "NM" or self._is_implied(mod):
                continue
            acronyms.append(mod.acronym)
        return acronyms

    def __str__(self) -> str:
        acronyms = []
        for mod in self.data:
            if self._is_implied(mod):
                continue
            acronyms.append(str(mod))

        if not acronyms:
            return "NM"
        return "".join(acronyms)

    def __int__(self) -> int:
        return self.bitwise

    def __index__(self) -> int:
        return int(self)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, int):
            try:
                item = Mod(item)
            except ValueError:
                return False

        if isinstance(item, Mod):
            if item.settings:
                return super().__contains__(item)
            item = item.acronym

        if isinstance(item, str):
            if item == "SV2":
                item = "V2"
            for mod in self.data:
                if mod.acronym == item:
                    return True
            return False

        return super().__contains__(item)

    def __and__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented

        mods: list[Mod] = []
        for mod in self:
            if not mod:
                continue
            for match in other_mods:
                if mod.acronym != match.acronym:
                    continue
                if mod.settings and match.settings and mod != match:
                    continue
                selected = mod if mod.settings else match
                if selected not in mods:
                    mods.append(selected)
        return self._operation_result(mods)

    def __rand__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented
        return other_mods & self

    def __or__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented

        mods: list[Mod] = []
        for mod in (*self, *other_mods):
            if not mod:
                continue
            if mod in mods:
                continue
            if mod.settings:
                mods = [
                    item
                    for item in mods
                    if item.acronym != mod.acronym or item.settings
                ]
            elif any(item.acronym == mod.acronym for item in mods):
                continue
            mods.append(mod)
        return self._operation_result(mods)

    def __ror__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented
        return other_mods | self

    def __xor__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented

        mods: list[Mod] = []
        for mod in self:
            if mod and other_mods._matching_mod(mod) is None and mod not in mods:
                mods.append(mod)
        for mod in other_mods:
            if mod and self._matching_mod(mod) is None and mod not in mods:
                mods.append(mod)
        return self._operation_result(mods)

    def __rxor__(self, other: object) -> Mods:
        other_mods = self._from_operand(other)
        if other_mods is None:
            return NotImplemented
        return other_mods ^ self

    def __invert__(self) -> Mods:
        mods: list[Mod] = []
        for acronym in _legacy_mods:
            if acronym == "NM" or acronym in self:
                continue
            if acronym == "NC" and "DT" in self:
                continue
            if acronym == "PF" and "SD" in self:
                continue
            mods.append(Mod(acronym))
        return self._operation_result(mods)

    @staticmethod
    def _from_operand(value: object) -> Mods | None:
        if isinstance(value, Mods):
            return value
        if isinstance(value, (Mod, int)):
            return Mods(value)
        return None

    def _matching_mod(self, value: Mod) -> Mod | None:
        if not value:
            return None
        for mod in self:
            if mod.acronym != value.acronym:
                continue
            if not mod.settings or not value.settings or mod == value:
                return mod
        return None

    @staticmethod
    def _operation_result(mods: list[Mod]) -> Mods:
        result = Mods()
        result.data = mods
        return result

    @staticmethod
    def _parse_string(value: str) -> list[str]:
        acronyms = []
        position = 0
        while position < len(value):
            if value.startswith("SV2", position):
                acronyms.append("SV2")
                position += 3
            else:
                acronyms.append(value[position : position + 2])
                position += 2
        return acronyms

    @staticmethod
    def _parse_bitmask(value: int) -> list[Mod]:
        mods = []
        for name in _legacy_mods.values():
            bitmask = getattr(Mod, name)
            if bitmask & value:
                mods.append(Mod(bitmask))
        return mods

    def _add_implied_mods(self) -> None:
        if Mod.Nightcore in self and Mod.DoubleTime not in self:
            self.data.append(Mod(Mod.DoubleTime))
        if Mod.Perfect in self and Mod.SuddenDeath not in self:
            self.data.append(Mod(Mod.SuddenDeath))

    def _is_implied(self, mod: Mod) -> bool:
        if mod.settings:
            return False
        if mod.acronym == "DT":
            return Mod.Nightcore in self
        if mod.acronym == "SD":
            return Mod.Perfect in self
        return False

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type[object],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        input_schema = core_schema.union_schema(
            [
                core_schema.is_instance_schema(cls),
                core_schema.is_instance_schema(Mod),
                core_schema.int_schema(),
                core_schema.str_schema(),
                core_schema.list_schema(),
            ],
        )
        serializer = core_schema.plain_serializer_function_ser_schema(
            cls.to_api,
            when_used="json",
        )
        return core_schema.no_info_after_validator_function(
            cls,
            input_schema,
            serialization=serializer,
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
