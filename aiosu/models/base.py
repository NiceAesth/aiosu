"""
This module contains base models for objects.
"""
from __future__ import annotations

from typing import SupportsFloat
from typing import SupportsInt

import pydantic
from pydantic import ConfigDict

__all__ = (
    "BaseModel",
    "FrozenModel",
)


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @classmethod
    def model_validate_file(cls, path: str) -> BaseModel:
        """Validates a model from a file.

        :param path: The path to the file
        :type path: str
        :raises TypeError: If the file is not a JSON file
        :return: The validated model
        :rtype: aiosu.models.base.BaseModel
        """
        with open(path) as f:
            return cls.model_validate_json(f.read())


class FrozenModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        frozen=True,
    )


def cast_int(v: object) -> int:
    if v is None:
        return 0
    if isinstance(v, (SupportsInt, str)):
        return int(v)

    raise ValueError(f"{v} is not a valid value.")


def cast_float(v: object) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (SupportsFloat, str)):
        return float(v)

    raise ValueError(f"{v} is not a valid value.")
