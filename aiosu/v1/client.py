from __future__ import annotations

import asyncio
from typing import Union

import orjson

from ..classes import Beatmap
from ..classes import Beatmapset
from ..classes import Score
from ..classes import Session
from ..classes import User


class Client:
    def __init__(self, token, **kwargs) -> None:
        self.__token = token
        self.__base_url = kwargs.pop("base_url", "https://osu.ppy.sh/api")
        self.__session = Session()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.__session.close())
            else:
                loop.run_until_complete(self.__session.close())
        except Exception:
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.__session.close()

    async def get_user(self, query: Union[str, int], **kwargs) -> list[User]:
        if (qtype := kwargs.pop("qtype", None)) not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None',
            )
        url = f"{self.__base_url}/get_user"
        params = {
            "k": self.__token,
            "u": query,
            "m": kwargs.pop("mode", 0),
            "event_days": kwargs.pop("event_days", 1),
        }
        if qtype:
            params["type"] = qtype
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    async def __get_type_scores(
        self, query: Union[str, int], request_type: str, **kwargs
    ) -> list[Score]:
        if request_type not in ("best", "recent"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        if (qtype := kwargs.pop("qtype", None)) not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None',
            )
        url = f"{self.__base_url}/get_user_{request_type}"
        params = {
            "k": self.__token,
            "u": query,
            "m": kwargs.pop("mode", 0),
            "limit": kwargs.pop("limit", 10),
        }
        if qtype:
            params["type"] = qtype
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    async def get_user_recent(self, query: Union[str, int], **kwargs) -> list[Score]:
        if not 1 <= kwargs.get("limit") <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        return self.__get_type_scores(query, "recent", **kwargs)

    async def get_user_best(self, query: Union[str, int], **kwargs) -> list[Score]:
        if not 1 <= kwargs.get("limit") <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        return self.__get_type_scores(query, "best", **kwargs)

    async def get_beatmaps(self, **kwargs) -> Union[list[Beatmap], list[Beatmapset]]:
        if not 1 <= kwargs.get("limit") <= 500:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 500")
        if (qtype := kwargs.get("qtype", None)) not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None',
            )
        url = f"{self.__base_url}/get_beatmaps"
        params = {
            "k": self.__token,
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
            if qtype:
                params["type"] = kwargs.pop("qtype")
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

    async def get_scores(self, beatmap_id, **kwargs) -> list[Score]:
        if not 1 <= kwargs.get("limit") <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if (qtype := kwargs.get("qtype", None)) not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None',
            )
        url = f"{self.__base_url}/get_scores"
        params = {
            "k": self.__token,
            "b": beatmap_id,
            "m": kwargs.pop("mode", 0),
            "limit": kwargs.pop("limit", 50),
        }
        if "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if qtype:
                params["type"] = kwargs.pop("qtype")
        if "mods" in kwargs:
            params["mods"] = kwargs.pop("mods")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    async def get_match(self, match_id: int):
        url = f"{self.__base_url}/get_match"
        params = {
            "k": self.__token,
            "mp": match_id,
        }
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json

    async def get_replay(self, **kwargs):
        if (qtype := kwargs.get("qtype", None)) not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None',
            )
        url = f"{self.__base_url}/get_match"
        params = {"k": self.__token, "m": kwargs.pop("mode", 0)}
        if "score_id" in kwargs:
            params["s"] = kwargs.pop("score_id")
        elif "beatmap_id" in kwargs and "user_query" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
            params["u"] = kwargs.pop("user_query")
            if qtype:
                params["type"] = kwargs.pop("qtype")
        else:
            raise ValueError(
                "Either score_id or beatmap_id + user_id must be specified.",
            )
        if "mods" in kwargs:
            params["mods"] = kwargs.pop("mods")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json
