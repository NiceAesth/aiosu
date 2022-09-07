from __future__ import annotations

import orjson
import pydantic

from .mods import Mods


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class BaseModel(pydantic.BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        json_encoders = {
            Mods: lambda v: repr(v),
        }


class FrozenModel(pydantic.BaseModel):
    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.__config__.frozen = True
