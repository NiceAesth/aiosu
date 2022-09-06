from __future__ import annotations

from multiprocessing.sharedctypes import Value
from typing import Any
from typing import Callable
from typing import TypeVar

T = TypeVar("T")


def from_list(f: Callable[[Any], T], x: Any) -> list[T]:
    if not isinstance(x, list):
        raise TypeError("Wrong type received. Expected list.")
    return [f(y) for y in x]
