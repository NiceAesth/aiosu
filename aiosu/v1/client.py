"""
This module handles API requests for API v1.

You can read more about it here: https://github.com/ppy/osu-api/wiki
"""
from __future__ import annotations

from types import TracebackType
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import Union

import aiohttp
from aiolimiter import AsyncLimiter

from .. import helpers
from ..classes import APIException
from ..classes import Beatmap
from ..classes import Beatmapset
from ..classes import Gamemode
from ..classes import Mods
from ..classes import Score
from ..classes import User
from ..classes import UserQueryType
from ..classes.legacy import Replay


class Client:
    def __init__(self, token: str, **kwargs: Any) -> None:
        self.token: str = token
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self.__session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.__session.close()

    @staticmethod
    def rate_limited(func: Callable) -> Callable:
        async def _rate_limited(*args: Any, **kwargs: Any) -> Any:
            self = args[0]
            async with self._limiter:
                return await func(*args, **kwargs)

        return _rate_limited

    @rate_limited
    async def get_user(self, user_query: Union[str, int], **kwargs: Any) -> list[User]:
        url = f"{self.base_url}/get_user"
        params = {
            "k": self.token,
            "u": user_query,
            "event_days": kwargs.pop("event_days", 1),
        }
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
            params["type"] = qtype.old_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(User._from_api_v1, json)

    @rate_limited
    async def __get_type_scores(
        self, user_query: Union[str, int], request_type: str, **kwargs: Any
    ) -> list[Score]:
        if request_type not in ("recent", "best"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        url = f"{self.base_url}/get_user_{request_type}"
        params = {
            "k": self.token,
            "u": user_query,
            "limit": kwargs.pop("limit", 10),
        }
        mode = Gamemode(kwargs.pop("mode", 0))  # type: ignore
        params["m"] = int(mode)
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
            params["type"] = qtype.old_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            score_conv = lambda x: Score._from_api_v1(x, mode)
            return helpers.from_list(score_conv, json)

    async def get_user_recents(
        self, user_query: Union[str, int], **kwargs: Any
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 50) <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        return await self.__get_type_scores(user_query, "recent", **kwargs)

    async def get_user_bests(
        self, user_query: Union[str, int], **kwargs: Any
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        return await self.__get_type_scores(user_query, "best", **kwargs)

    @rate_limited
    async def get_beatmap(self, **kwargs: Any) -> list[Beatmapset]:
        if not 1 <= kwargs.get("limit", 500) <= 500:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 500")
        url = f"{self.base_url}/get_beatmaps"
        params = {
            "k": self.token,
            "limit": kwargs.pop("limit", 500),
            "a": int(kwargs.pop("converts", False)),
        }
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        if "beatmap_id" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
        elif "beatmapset_id" in kwargs:
            params["s"] = kwargs.pop("beatmapset_id")
        elif "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        elif "since" in kwargs:
            params["since"] = kwargs.pop("since")
        elif "hash" in kwargs:
            params["h"] = kwargs.pop("hash")
        else:
            raise ValueError(
                "Either hash, since, user_query, beatmap_id or beatmapset_id must be specified.",
            )
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Beatmapset._from_api_v1, json)

    @rate_limited
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs: Any) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        url = f"{self.base_url}/get_scores"
        params = {
            "k": self.token,
            "b": beatmap_id,
            "limit": kwargs.pop("limit", 50),
        }
        mode = Gamemode(kwargs.pop("mode", 0))  # type: ignore
        params["m"] = int(mode)
        if "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            score_conv = lambda x: Score._from_api_v1(x, mode)
            return helpers.from_list(score_conv, json)

    @rate_limited
    async def get_match(self, match_id: int) -> Any:
        url = f"{self.base_url}/get_match"
        params = {
            "k": self.token,
            "mp": match_id,
        }
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return json

    @rate_limited
    async def get_replay(self, **kwargs: Any) -> Replay:
        url = f"{self.base_url}/get_replay"
        params = {"k": self.token}
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "score_id" in kwargs:
            params["s"] = kwargs.pop("score_id")
        elif "beatmap_id" in kwargs and "user_query" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        else:
            raise ValueError(
                "Either score_id or beatmap_id + user_id must be specified.",
            )
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Replay.parse_obj(json)
