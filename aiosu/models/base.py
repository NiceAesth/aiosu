"""
This module contains base models for objects.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TypeVar

import pydantic
from pydantic import ConfigDict
from pydantic import field_serializer
from pydantic import field_validator
from pydantic import FieldSerializationInfo
from pydantic import FieldValidationInfo

from .mods import Mods


if TYPE_CHECKING:
    from .lazer import LazerMod

__all__ = (
    "BaseModel",
    "FrozenModel",
)

T = TypeVar("T")


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    def model_validate_file(self, path: str) -> BaseModel:
        """Validates a model from a file.

        :param path: The path to the file
        :type path: str
        :raises TypeError: If the file is not a JSON file
        :return: The validated model
        :rtype: aiosu.models.base.BaseModel
        """
        with open(path) as f:
            return self.model_validate_json(f.read())


class FrozenModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        frozen=True,
    )
