"""
This module contains base models for objects.
"""
from __future__ import annotations

from typing import Any

import orjson
import pydantic

from .mods import Mods


def orjson_dumps(v: object, *, default: Any) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class BaseModel(pydantic.BaseModel):
    class Config:
        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        json_encoders = {
            Mods: lambda v: str(v),
        }


class FrozenModel(BaseModel):
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.__config__.frozen = True
