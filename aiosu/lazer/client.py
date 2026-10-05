"""This module contains the client for interfacing with the osu!lazer WebSocket API."""

from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING

import aiohttp
import orjson

from ..models import BeatmapStateWebSocketMessage
from ..models import OsuWebSocketMessage
from ..models import UserActivityWebSocketMessage

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from typing import Any

__all__ = ("Client",)


class Client:
    __slots__ = ("_base_url", "_session", "_listeners", "_task", "socket")

    def __init__(self, **kwargs: Any) -> None:
        r"""osu!lazer WebSocket client.
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *base_url* (``str``) --
                Optional, base websocket URL, defaults to "ws://localhost:49727/"
        """
        self._base_url: str = kwargs.pop("base_url", "ws://localhost:49727/")
        self._session: aiohttp.ClientSession | None = None
        self._listeners: dict[str, Callable] = {}
        self._task: asyncio.Task[None] | None = None
        self.socket: aiohttp.ClientWebSocketResponse | None = None

    def on_beatmap_state(self, func: Callable) -> Callable:
        r"""Returns a callable that is called when the beatmap state is updated, to be used as:
        @client.on_beatmap_state
        async def beatmap_state(event: BeatmapStateWebSocketMessage):
        """

        @functools.wraps(func)
        async def wrapper(data: dict) -> Any:
            return await func(BeatmapStateWebSocketMessage.model_validate(data))

        self._listeners["BeatmapStateWebSocketMessage"] = wrapper
        return wrapper

    def on_user_activity(self, func: Callable) -> Callable:
        r"""Returns a callable that is called when the user activity is updated, to be used as:
        @client.on_user_activity
        async def user_activity(event: UserActivityWebSocketMessage):
        """

        @functools.wraps(func)
        async def wrapper(data: dict) -> Any:
            return await func(UserActivityWebSocketMessage.model_validate(data))

        self._listeners["UserActivityWebSocketMessage"] = wrapper
        return wrapper

    def on_raw_message(self, func: Callable) -> Callable:
        r"""Returns a callable that is called when a websocket message is received, to be used as:
        @client.on_raw_message
        async def raw_message(data: str):
        """

        @functools.wraps(func)
        async def wrapper(data: str) -> Any:
            return await func(data)

        self._listeners["raw_message"] = wrapper
        return wrapper

    async def __aenter__(self) -> Client:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def connect(self) -> None:
        r"""Connects to the websocket server.

        :return: None
        """
        if self.socket is not None and not self.socket.closed:
            return
        if self._task is not None:
            await self.aclose()
        if self._session is None:
            self._session = aiohttp.ClientSession()
        try:
            self.socket = await self._session.ws_connect(self._base_url)
        except BaseException:
            await self._session.close()
            self._session = None
            raise
        self._task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        assert self.socket is not None
        try:
            async for message in self.socket:
                if message.type == aiohttp.WSMsgType.TEXT:
                    await self._process_message(message.data)
                elif message.type == aiohttp.WSMsgType.ERROR:
                    error = self.socket.exception()
                    if error is not None:
                        raise error
                    raise ConnectionError("WebSocket receive failed.")
        finally:
            await self._close_connection()

    async def _process_message(self, data: str) -> None:
        if "raw_message" in self._listeners:
            await self._listeners["raw_message"](data)
        payload = orjson.loads(data)
        message = OsuWebSocketMessage.model_validate(payload)
        if message.type in self._listeners:
            await self._listeners[message.type](payload)

    async def _close_connection(self) -> None:
        try:
            if self.socket is not None:
                await self.socket.close()
        finally:
            if self._session is not None:
                await self._session.close()

    async def aclose(self) -> None:
        r"""Closes the client.

        :return: None
        """
        task = self._task
        if task is asyncio.current_task():
            await self._close_connection()
            return
        try:
            if task is not None:
                if not task.done():
                    task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        finally:
            await self._close_connection()
            self._task = None
            self.socket = None
            self._session = None
