from __future__ import annotations

from typing import Union

import aiohttp
from aiolimiter import AsyncLimiter

from ..classes import Beatmap
from ..classes import Beatmapset
from ..classes import Score
from ..classes import User
from ..classes import UserQueryType


class Client:
    def __init__(self, token, **kwargs) -> None:
        self.token: str = token
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self.__session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.__session.close()

    @staticmethod
    def rate_limited(func):
        async def _rate_limited(*args, **kwargs):
            self = args[0]
            async with self._limiter:
                return await func(*args, **kwargs)

        return _rate_limited

    @rate_limited
    async def get_user(self, user_query: Union[str, int], **kwargs) -> list[User]:
        url = f"{self.base_url}/get_user"
        params = {
            "k": self.token,
            "u": user_query,
            "m": kwargs.pop("mode", 0),
            "event_days": kwargs.pop("event_days", 1),
        }
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))
            params["type"] = qtype.old_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    @rate_limited
    async def __get_type_scores(
        self, user_query: Union[str, int], request_type: str, **kwargs
    ) -> list[Score]:
        if request_type not in ("recent", "best"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        url = f"{self.base_url}/get_user_{request_type}"
        params = {
            "k": self.token,
            "u": user_query,
            "m": kwargs.pop("mode", 0),
            "limit": kwargs.pop("limit", 10),
        }
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))
            params["type"] = qtype.old_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    async def get_user_recents(
        self, user_query: Union[str, int], **kwargs
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 50) <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        return self.__get_type_scores(user_query, "recent", **kwargs)

    async def get_user_bests(
        self, user_query: Union[str, int], **kwargs
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        return self.__get_type_scores(user_query, "best", **kwargs)

    @rate_limited
    async def get_beatmaps(self, **kwargs) -> Union[list[Beatmap], list[Beatmapset]]:
        if not 1 <= kwargs.get("limit", 500) <= 500:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 500")
        url = f"{self.base_url}/get_beatmaps"
        params = {
            "k": self.token,
            "m": kwargs.pop("mode", 0),
            "limit": kwargs.pop("limit", 500),
            "a": kwargs.pop("converts", False),
            "mods": kwargs.pop("mods", 0),
        }
        if "beatmap_id" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
        elif "beatmapset_id" in kwargs:
            params["s"] = kwargs.pop("beatmapset_id")
        elif "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))
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
        return json

    @rate_limited
    async def get_scores(self, beatmap_id, **kwargs) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        url = f"{self.base_url}/get_scores"
        params = {
            "k": self.token,
            "b": beatmap_id,
            "m": kwargs.pop("mode", 0),
            "limit": kwargs.pop("limit", 50),
        }
        if "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))
                params["type"] = qtype.old_api_name
        if "mods" in kwargs:
            params["mods"] = kwargs.pop("mods")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    @rate_limited
    async def get_match(self, match_id: int):
        url = f"{self.base_url}/get_match"
        params = {
            "k": self.token,
            "mp": match_id,
        }
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    @rate_limited
    async def get_replay(self, **kwargs):
        url = f"{self.base_url}/get_match"
        params = {"k": self.token, "m": kwargs.pop("mode", 0)}
        if "score_id" in kwargs:
            params["s"] = kwargs.pop("score_id")
        elif "beatmap_id" in kwargs and "user_query" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))
                params["type"] = qtype.old_api_name
        else:
            raise ValueError(
                "Either score_id or beatmap_id + user_id must be specified.",
            )
        if "mods" in kwargs:
            params["mods"] = kwargs.pop("mods")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json
