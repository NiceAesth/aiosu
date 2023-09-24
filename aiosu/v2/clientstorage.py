"""
This module handles multiple API v2 Client sessions.
"""
from __future__ import annotations

import functools
from collections.abc import Awaitable
from typing import Callable
from typing import cast
from typing import TYPE_CHECKING
from typing import TypeVar

from . import Client
from ..events import ClientAddEvent
from ..events import ClientUpdateEvent
from ..events import Eventable
from ..exceptions import InvalidClientRequestedError
from ..models import OAuthToken
from .repository import BaseTokenRepository
from .repository import SimpleTokenRepository

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from typing import Optional
    from typing import Union

__all__ = ("ClientStorage",)

F = TypeVar("F", bound=Callable[..., Awaitable[object]])


class ClientStorage(Eventable):
    r"""OAuth sessions manager.

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *token_repository* (``BaseTokenRepository``) --
            Optional, defaults to ``aiosu.v2.repository.SimpleTokenRepository()``
        * *client_secret* (``str``)
        * *client_id* (``int``)
        * *base_url* (``str``) --
            Optional, base API URL, defaults to "https://osu.ppy.sh"
        * *create_app_client* (``bool``) --
            Optional, whether to automatically create guest clients, defaults to True
    """

    __slots__ = (
        "_token_repository",
        "client_secret",
        "client_id",
        "base_url",
        "__create_app_client",
        "clients",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self._register_event(ClientAddEvent)
        self._register_event(ClientUpdateEvent)
        self._token_repository: BaseTokenRepository = kwargs.pop(
            "token_repository",
            SimpleTokenRepository(),
        )
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
        self.__create_app_client: bool = kwargs.pop("create_app_client", True)
        self.clients: dict[int, Client] = {}

    async def __aenter__(self) -> ClientStorage:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    def on_client_add(self, func: F) -> F:
        """
        A decorator that is called whenever a client is added, to be used as:

            @client_storage.on_client_add

            async def func(event: ClientAddEvent)
        """
        self._register_listener(func, ClientAddEvent)

        @functools.wraps(func)
        async def _on_client_add(*args: Any, **kwargs: Any) -> object:
            return await func(*args, **kwargs)

        return cast(F, _on_client_add)

    def on_client_update(self, func: F) -> F:
        """
        A decorator that is called whenever any stored client is updated, to be used as:

            @client_storage.on_client_update

            async def func(event: ClientUpdateEvent)
        """
        self._register_listener(func, ClientUpdateEvent)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> object:
            return await func(*args, **kwargs)

        return cast(F, _on_client_update)

    def _get_client_args(self) -> dict[str, Union[str, int]]:
        return {
            "client_secret": self.client_secret,
            "client_id": self.client_id,
            "base_url": self.base_url,
        }

    @property
    async def app_client(self) -> Client:
        r"""Client credentials app client.

        :raises ValueError: If no app client is provided and creation is disabled
        :return: Client credentials app client session
        :rtype: aiosu.v2.client.Client
        """
        if not self.__create_app_client:
            raise ValueError("App clients have been disabled.")

        if 0 not in self.clients:
            client = Client(
                token_repository=self._token_repository,
                session_id=0,
                token=OAuthToken(),
                **self._get_client_args(),
            )
            self.clients[0] = client
            await self._process_event(
                ClientAddEvent(session_id=0, client=client),
            )

        return self.clients[0]

    def client_exists(self, client_uid: int) -> bool:
        r"""Checks if a client exists.

        :param client_uid: The owner user ID of the client
        :type client_uid: int
        :return: Whether the client with the given ID exists
        :rtype: bool
        """
        return client_uid in self.clients

    async def add_client(
        self,
        token: OAuthToken,
        **kwargs: Any,
    ) -> Client:
        r"""Adds a client to storage.

        :param token: The token object of the client
        :type token: aiosu.models.OAuthToken
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *id* (``int``) --
                Optional, the ID of the client session
        :return: The client with the given ID or token
        :rtype: aiosu.v2.client.Client
        """
        session_id: int = kwargs.pop("id", token.owner_id)
        client = Client(
            token_repository=self._token_repository,
            session_id=session_id,
            token=token,
            **self._get_client_args(),
        )
        client._register_listener(self._process_event, ClientUpdateEvent)
        await client._prepare_token()
        await self._process_event(
            ClientAddEvent(session_id=session_id, client=client),
        )
        self.clients[session_id] = client
        return client

    async def get_client(self, **kwargs: Any) -> Client:
        r"""Gets a client from storage.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *id* (``int``) --
                Optional, the owner user ID of the client
            * *token* (``OAuthToken``) --
                Optional, the token object of the client
        :raises InvalidClientRequestedError: If no valid ID or token is provided
        :return: The client with the given ID or token
        :rtype: aiosu.v2.client.Client
        """
        session_id: int = kwargs.pop("id", None)
        token: OAuthToken = kwargs.pop("token", None)
        if self.client_exists(session_id):
            return self.clients[session_id]
        if token is not None:
            return await self.add_client(token, id=session_id)
        if await self._token_repository.exists(session_id):
            token = await self._token_repository.get(session_id)
            return await self.add_client(token, id=session_id)
        raise InvalidClientRequestedError(
            "Either a valid id or token must be specified.",
        )

    async def revoke_client(self, client_uid: int) -> None:
        r"""Revokes a client from storage.

        :param client_uid: The owner user ID of the client
        :type client_uid: int
        :raises InvalidClientRequestedError: If no client exists with the given ID
        """
        if self.client_exists(client_uid):
            await self.clients[client_uid].revoke_token()
            del self.clients[client_uid]
            return

        raise InvalidClientRequestedError(
            "No client exists with the given ID.",
        )

    async def close(self) -> None:
        r"""Closes all client sessions."""
        for client in self.clients.values():
            await client.close()
