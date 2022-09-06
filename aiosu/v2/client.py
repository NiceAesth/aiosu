from __future__ import annotations

import asyncio
import datetime

from ..classes import APIException
from ..classes import Gamemode
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
    async def get_user(self, **kwargs) -> User:
        url = f'{self.__base_url}/{kwargs.pop("query")}'
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

    @check_token
    async def get_scores(self, **kwargs) -> list[Score]:
        pass
