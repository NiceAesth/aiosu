import asyncio
from typing import Union

import orjson

from ..classes import Session


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

    async def get_user(self, query: Union[str, int], **kwargs):
        qtype = kwargs.pop("qtype", None)
        if qtype not in ("string", "id", None):
            raise ValueError(
                'Invalid qtype specified. Valid options are: "string", "id", None'
            )
        url = f"{self.__base_url}/get_user"
        params = {
            "k": self.__token,
            "u": query,
            "m": int(kwargs.pop("mode", 0)),
            "event_days": kwargs.pop("event_days", 1),
        }
        if qtype:
            params["type"] = qtype
        async with self.__session.get(url, params=params) as resp:
            json = await resp.json()
        return json
