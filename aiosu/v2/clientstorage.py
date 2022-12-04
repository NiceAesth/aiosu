"""
This module handles multiple API v2 Client sessions.
"""
from __future__ import annotations

import functools
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import Union

from . import Client
from ..classes import OAuthToken
from ..classes.events import BaseEvent
from ..classes.events import ClientAddEvent
from ..classes.events import ClientUpdateEvent
from ..classes.events import Eventable


class ClientStorage(Eventable):
    r"""OAuth sessions manager.

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *client_secret* (``str``)
        * *client_id* (``int``)
        * *base_url* (``str``) --
            Optional, base API URL, defaults to \"https://osu.ppy.sh/api/v2/\"
        * *create_app_client* (``bool``) --
            Optional, whether to automatically create guest clients, defaults to False
        * *app_client* (``aiosu.v2.client.Client``) --
            Optional, guest client, defaults to None
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api/v2")
        self.__create_app_client: bool = kwargs.pop("create_app_client", False)
        self.clients: dict[int, Client] = {}
        if _app_client := kwargs.pop("app_client", None):
            self.clients[0] = _app_client
        self._redirected_listeners: list[Callable] = []

    async def __aenter__(self) -> ClientStorage:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    def on_client_add(self, func: Callable) -> Callable:
        """
        A decorator that is called whenever a client is added, to be used as:

            @clientsession.on_client_add

            async def func(event: ClientAddEvent)
        """
        self._listeners.append(func)

        @functools.wraps(func)
        async def _on_client_add(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_add

    def on_client_update(self, func: Callable) -> Callable:
        """
        A decorator that is called whenever any stored client is updated, to be used as:

            @clientsession.on_client_update

            async def func(event: ClientUpdateEvent)
        """
        self._redirected_listeners.append(func)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_update

    async def _process_event(self, event: BaseEvent) -> None:
        if isinstance(event, ClientAddEvent):
            for func in self._listeners:
                await func(event)
            return
        if isinstance(event, ClientUpdateEvent):
            for func in self._redirected_listeners:
                await func(event)
            return
        raise NotImplementedError(f"{event!r}")

    @property
    async def app_client(self) -> Client:
        r"""Client credentials guest client.

        :raises NotImplementedError: If no app client is provided and creation is disabled
        :return: Client credentials guest client session
        :rtype: aiosu.v1.client.Client
        """
        if not (_app_client := self.clients.get(0)):
            raise NotImplementedError("Client credential grant creation is still WIP")
            await self._process_event(
                ClientAddEvent(client_id=0, client=self._app_client),
            )

        return _app_client

    def _get_client_args(self) -> dict[str, Union[str, int]]:
        return {
            "client_secret": self.client_secret,
            "client_id": self.client_id,
            "base_url": self.base_url,
        }

    def client_exists(self, client_uid: int) -> bool:
        r"""Checks if a client exists.

        :param client_uid: The owner user ID of the client
        :type client_uid: int
        :return: Whether the client with the given ID exists
        :rtype: bool
        """
        return client_uid in self.clients

    async def add_client(self, token: OAuthToken) -> Client:
        r"""Adds a client to storage.

        :param token: Token object for the client
        :type token: aiosu.classes.token.OAuthToken
        :return: The added client
        :rtype: aiosu.v1.client.Client
        """
        client = Client(token=token, **self._get_client_args())
        client._listeners.append(self._process_event)
        client_user = await client.get_me()
        self.clients[client_user.id] = client
        await self._process_event(
            ClientAddEvent(client_id=client_user.id, client=client),
        )
        return client

    async def get_client(self, **kwargs: Any) -> Client:
        r"""Gets a client from storage.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *id* (``int``) --
                Optional, whether to automatically create guest clients, defaults False
            * *token* (``aiosu.classes.token.OAuthToken``) --
                Optional, token of client to add, defaults to None

        :raises ValueError: If neither id nor token are specified
        :return: The requested client
        :rtype: aiosu.v1.client.Client
        """
        client_uid: int = kwargs.pop("id", None)
        token: OAuthToken = kwargs.pop("token", None)
        if self.client_exists(client_uid):
            return self.clients[client_uid]
        if token is not None:
            return await self.add_client(token)
        raise ValueError("Either id or token must be specified.")

    async def close(self) -> None:
        r"""Closes all client sessions."""
        for client in self.clients.values():
            await client.close()
