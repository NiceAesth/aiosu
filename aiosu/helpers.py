"""
This module contains miscellaneous helper functions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import TypeVar
    from collections.abc import Mapping
    from collections.abc import MutableMapping

    T = TypeVar("T")

__all__ = (
    "add_param",
    "append_param",
    "from_list",
)


def from_list(f: Callable[[Any], T], x: list) -> list[T]:
    r"""Applies a function to all elements in a list.

    :param f: Function to apply on list elements
    :type f: Callable[[Any], T]
    :param x: List of objects
    :type x: list[object]
    :raises TypeError: If x is not a list
    :return: New list
    :rtype: list[T]
    """
    if not isinstance(x, list):
        raise TypeError("Wrong type received. Expected list.")
    return [f(y) for y in x]


def append_param(
    value: object,
    l: list,
    append: bool = True,
) -> None:
    r"""Appends a value to a list if it is not None and append is True.

    :param value: Value to append
    :type value: object
    :param l: List to append to
    :type l: list[object]
    :param append: Whether to append or not, defaults to True
    :type append: bool, optional, defaults to True
    """
    if value is None:
        return
    if append:
        l.append(value)


def add_param(
    params: MutableMapping[str, Any],
    kwargs: Mapping[str, object],
    key: str,
    param_name: Optional[str] = None,
    converter: Optional[Callable[[Any], T]] = None,
) -> bool:
    r"""Adds a parameter to a dictionary if it exists in kwargs.

    :param params: Dictionary to add parameter to
    :type params: Mapping[str, Any]
    :param kwargs: Dictionary to get parameter from
    :type kwargs: Mapping[str, Any]
    :param key: Key to get parameter from
    :type key: str
    :param param_name: Name of parameter to add to dictionary, defaults to None
    :type param_name: Optional[str]
    :param converter: Function to convert parameter, defaults to None
    :type converter: Optional[Callable[[Any], T]]
    :return: True if parameter was added, False otherwise
    :rtype: bool
    """
    if key not in kwargs:
        return False

    value = kwargs[key]
    if converter:
        value = converter(value)

    params[param_name or key] = value
    return True
