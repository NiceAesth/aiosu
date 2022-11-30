from __future__ import annotations

import datetime
from typing import Union

import aiohttp
from aiolimiter import AsyncLimiter

from .. import helpers
from ..classes import APIException
from ..classes import Beatmap
from ..classes import BeatmapDifficultyAttributes
from ..classes import Gamemode
from ..classes import Mods
from ..classes import OAuthToken
from ..classes import Score
from ..classes import User
from ..classes import UserQueryType


class Client:
    def __init__(self, **kwargs) -> None:
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.token: OAuthToken = kwargs.pop("token", OAuthToken())
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api/v2")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self.__session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.token.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        await self.__session.close()

    @staticmethod
    def check_token(func):
        async def _check_token(*args, **kwargs):
            self = args[0]
            if datetime.datetime.now() > self.token.expires_on:
                print("refreshing token")
                self.__session.headers[
                    "Authorization"
                ] = f"Bearer {self.token.access_token}"
            return await func(*args, **kwargs)

        return _check_token

    @staticmethod
    def rate_limited(func):
        async def _rate_limited(*args, **kwargs):
            self = args[0]
            async with self._limiter:
                return await func(*args, **kwargs)

        return _rate_limited

    @rate_limited
    @check_token
    async def get_me(self) -> User:
        url = f"{self.base_url}/me"
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    @rate_limited
    @check_token
    async def get_user(self, user_query: Union[str, int], **kwargs) -> User:
        url = f"{self.base_url}/{user_query}"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            url += f"/{mode}"
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))
            params["type"] = qtype.new_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    @rate_limited
    @check_token
    async def __get_type_scores(
        self, user_id: int, request_type: str, **kwargs
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if request_type not in ("recent", "best", "firsts"):
            raise ValueError(
                f'"{request_type}" is not a valid request_type. Valid options are: "recent", "best", "firsts"',
            )
        url = f"{self.base_url}/users/{user_id}/scores/{request_type}"
        params = {
            "include_fails": kwargs.pop("include_fails", False),
            "offset": kwargs.pop("offset", 0),
            "limit": kwargs.pop("limit", 100),
        }
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = str(mode)
        if "limit" in kwargs:
            params["limit"] = kwargs.pop("mode")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json)

    async def get_user_recents(self, user_id: int, **kwargs) -> list[Score]:
        return await self.__get_type_scores(user_id, "recent", **kwargs)

    async def get_user_bests(self, user_id: int, **kwargs) -> list[Score]:
        return await self.__get_type_scores(user_id, "best", **kwargs)

    async def get_user_firsts(self, user_id: int, **kwargs) -> list[Score]:
        return await self.__get_type_scores(user_id, "firsts", **kwargs)

    @rate_limited
    @check_token
    async def get_user_beatmap_scores(self, user_id: int, beatmap_id: int, **kwargs):
        url = f"{self.base_url}/beatmaps/{beatmap_id}/scores/users/{user_id}/all"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = str(mode)
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json.get("scores", []))

    @rate_limited
    @check_token
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs):
        url = f"{self.base_url}/beatmaps/{beatmap_id}/scores"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = str(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        if "type" in kwargs:
            params["type"] = kwargs.pop("type")
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json.get("scores", []))

    @rate_limited
    @check_token
    async def get_beatmap(self, beatmap_id: int) -> Beatmap:
        url = f"{self.base_url}/beatmaps/{beatmap_id}"
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Beatmap.parse_obj(json)

    @rate_limited
    @check_token
    async def get_beatmap_attributes(
        self,
        beatmap_id: int,
    ) -> BeatmapDifficultyAttributes:
        url = f"{self.base_url}/beatmaps/{beatmap_id}/attributes"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = str(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        if "type" in kwargs:
            params["type"] = kwargs.pop("type")
        async with self.__session.post(url, data=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return BeatmapDifficultyAttributes.parse_obj(json.get("attributes"))
