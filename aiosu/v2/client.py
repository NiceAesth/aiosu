from __future__ import annotations

import asyncio
import datetime
from typing import Union

from .. import utils
from ..classes import APIException
from ..classes import Beatmap
from ..classes import Gamemode
from ..classes import Mods
from ..classes import OAuthToken
from ..classes import Score
from ..classes import Session
from ..classes import User
from ..classes import UserQueryType


class Client:
    def __init__(self, **kwargs) -> None:
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.token: OAuthToken = kwargs.pop("token", OAuthToken())
        self.__base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api/v2")
        self.__session: Session = Session(
            headers={
                "Authorization": f"Bearer {self.token.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

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

    @staticmethod
    def check_token(func):
        async def _check_token(*args, **kwargs):
            self = args[0]
            if datetime.datetime.now() > self.token.expires_on:
                print("refreshing token")
                self.__session.headers[
                    "Authorization"
                ] = f"Bearer {self.token.access_token}"
            await func(*args, **kwargs)

        return _check_token

    @check_token
    async def get_me(self) -> User:
        url = f"{self.__base_url}/me"
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    @check_token
    async def get_user(self, user_query: Union[str, int], **kwargs) -> User:
        url = f"{self.__base_url}/{user_query}"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            url += f"/{mode}"
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))
            params["type"] = qtype.new_api_name
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    async def __get_type_scores(
        self, user_id: int, request_type: str, **kwargs
    ) -> list[Score]:
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if request_type not in ("best", "firsts" "recent"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        url = f"{self.__base_url}/users/{user_id}/scores/{request_type}"
        params = {
            "include_fails": kwargs.pop("include_fails", False),
            "offset": kwargs.pop("offset", 0),
            "limit": kwargs.pop("limit", 100),
        }
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = repr(mode)
        if "limit" in kwargs:
            params["limit"] = kwargs.pop("mode")
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return utils.from_list(Score.parse_obj, json)

    @check_token
    async def get_user_recents(self, user_id: int, **kwargs) -> list[Score]:
        return self.__get_type_scores(user_id, "recent", **kwargs)

    @check_token
    async def get_user_bests(self, user_id: int, **kwargs) -> list[Score]:
        return self.__get_type_scores(user_id, "best", **kwargs)

    @check_token
    async def get_user_firsts(self, user_id: int, **kwargs) -> list[Score]:
        return self.__get_type_scores(user_id, "firsts", **kwargs)

    @check_token
    async def get_user_beatmap_scores(self, user_id: int, beatmap_id: int, **kwargs):
        url = f"{self.__base_url}/beatmaps/{beatmap_id}/scores/users/{user_id}/all"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = repr(mode)
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return utils.from_list(Score.parse_obj, json.get("scores", []))

    @check_token
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs):
        url = f"{self.__base_url}/beatmaps/{beatmap_id}"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))
            params["mode"] = repr(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = repr(mods)
        if "type" in kwargs:
            params["type"] = kwargs.pop("type")
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return utils.from_list(Score.parse_obj, json.get("scores", []))

    @check_token
    async def get_beatmap(self, beatmap_id: int) -> Beatmap:
        url = f"{self.__base_url}/beatmaps/{beatmap_id}"
        async with self.__session.get(url) as resp:
            json = await resp.json()
            if json.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Beatmap.parse_obj(json)
