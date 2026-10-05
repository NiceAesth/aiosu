"""
This module contains performance point calculators for osu! gamemodes.
"""

from __future__ import annotations

from ...models.gamemode import Gamemode
from ._base import AbstractPerformanceCalculator
from .catch import CatchPerformanceCalculator
from .mania import ManiaPerformanceCalculator
from .osu import OsuPerformanceCalculator
from .taiko import TaikoPerformanceCalculator

__all__ = [
    "CatchPerformanceCalculator",
    "ManiaPerformanceCalculator",
    "OsuPerformanceCalculator",
    "TaikoPerformanceCalculator",
]


def get_calculator(mode: Gamemode) -> type[AbstractPerformanceCalculator]:
    r"""Returns the performance calculator for the given gamemode.

    :param mode: The gamemode to get the calculator for
    :type mode: aiosu.models.gamemode.Gamemode
    :raises ValueError: If the gamemode is unknown
    :return: The performance calculator type for the given gamemode
    :rtype: Type[AbstractPerformanceCalculator]
    """
    if mode == Gamemode.STANDARD:
        return OsuPerformanceCalculator
    elif mode == Gamemode.TAIKO:
        return TaikoPerformanceCalculator
    elif mode == Gamemode.MANIA:
        return ManiaPerformanceCalculator
    elif mode == Gamemode.CTB:
        return CatchPerformanceCalculator
    raise ValueError(f"Unknown gamemode: {mode}")
