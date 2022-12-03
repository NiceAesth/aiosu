"""
This module contains miscellaneous helper functions.
"""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import TypeVar

T = TypeVar("T")


def from_list(f: Callable[[Any], T], x: Any) -> list[T]:
    """Applies a function to all elements in a list.

    :param f: Function to apply on list elements
    :type f: Callable[[Any], T]
    :param x: List of objects
    :type x: Any
    :raises TypeError: If x is not a list
    :return: New list
    :rtype: list[T]
    """
    if not isinstance(x, list):
        raise TypeError("Wrong type received. Expected list.")
    return [f(y) for y in x]
