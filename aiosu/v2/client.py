from __future__ import annotations

import asyncio

import orjson

from ..classes import Session


class Client:
    def __init__(self, **kwargs) -> None:
        self.client_secret = None
        self.client_id = None
        self.__base_url = kwargs.pop("base_url", "https://osu.ppy.sh/api/v2")
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
