"""
This module contains base models for objects.
"""
from __future__ import annotations

import pydantic
from pydantic import ConfigDict

__all__ = (
    "BaseModel",
    "FrozenModel",
)


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
