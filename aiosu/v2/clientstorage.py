"""
This module handles multiple API v2 Client sessions.
"""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from . import BaseClientRepository
from . import Client
from . import SimpleClientRepository
from ..events import ClientAddEvent
from ..events import ClientUpdateEvent
from ..events import Eventable
from ..models import OAuthToken
from ..models import Scopes

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import Type
    from typing import Union

__all__ = ("ClientStorage",)


class ClientStorage(Eventable):
    r"""OAuth sessions manager.

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *client_secret* (``str``)
        * *client_id* (``int``)
        * *base_url* (``str``) --
            Optional, base API URL, defaults to "https://osu.ppy.sh"
        * *create_app_client* (``bool``) --
            Optional, whether to automatically create guest clients, defaults to True
        * *default_scopes* (``Scopes``) --
            Optional, default scopes to use when creating a client, defaults to Scopes.PUBLIC | Scopes.IDENTIFY
        * *client_repository* (``aiosu.v2.clientrepository.BaseClientRepository``) --
            Optional, client repository to use, defaults to ``aiosu.v2.clientrepository.SimpleClientRepository``
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self._register_event(ClientAddEvent)
        self._register_event(ClientUpdateEvent)
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh").rstrip("/")
        self.__create_app_client: bool = kwargs.pop("create_app_client", True)
        self.default_scopes: Scopes = kwargs.pop(
            "default_scopes",
            Scopes.PUBLIC | Scopes.IDENTIFY,
        )
        self.client_repository: BaseClientRepository = kwargs.pop(
            "client_repository",
            SimpleClientRepository(),
        )

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

            @client_storage.on_client_add

            async def func(event: ClientAddEvent)
        """
        self._register_listener(func, ClientAddEvent)

        @functools.wraps(func)
        async def _on_client_add(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_add

    def on_client_update(self, func: Callable) -> Callable:
        """
        A decorator that is called whenever any stored client is updated, to be used as:

            @client_storage.on_client_update

            async def func(event: ClientUpdateEvent)
        """
        self._register_listener(func, ClientUpdateEvent)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_update

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

        if not await self.client_exists(0):
            new_client = Client(
                token=OAuthToken(scopes=self.default_scopes),
                **self._get_client_args(),
            )
            await self.client_repository.add(0, new_client)
            await self._process_event(
                ClientAddEvent(client_id=0, client=new_client),
            )

        client = await self.client_repository.get(0)
        if not client:
            raise ValueError("App client not found.")
        return client

    async def client_exists(self, client_uid: int) -> bool:
        r"""Checks if a client exists.

        :param client_uid: The ID of the client
        :type client_uid: int
        :return: Whether the client with the given ID exists
        :rtype: bool
        """
        return await self.client_repository.exists(client_uid)

    async def add_client(
        self,
        token: OAuthToken,
        **kwargs: Any,
    ) -> Client:
        r"""Adds a client to storage.

        :param token: Token object for the client
        :type token: aiosu.models.oauthtoken.OAuthToken
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *id* (``int``) --
                Optional, the ID of the client, defaults to None
            * *scopes* (``Scopes``) --
                Optional, the scopes of the client, defaults to storage default scopes

        :return: The added client
        :rtype: aiosu.v2.client.Client
        """
        scopes = kwargs.pop("scopes", self.default_scopes)
        client_id: int = kwargs.pop("id", None)
        client = Client(token=token, **self._get_client_args(), scopes=scopes)
        client._register_listener(self._process_event, ClientUpdateEvent)
        if client_id is None:
            client_user = await client.get_me()
            client_id = client_user.id
        await self.client_repository.add(client_id, client)
        await self._process_event(
            ClientAddEvent(client_id=client_id, client=client),
        )
        return client

    async def get_client(self, **kwargs: Any) -> Client:
        r"""Gets a client from storage.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *id* (``int``) --
                Optional, the ID of the client, defaults to None
            * *token* (``aiosu.models.oauthtoken.OAuthToken``) --
                Optional, token of client to add, defaults to None

        :raises ValueError: If neither id nor token are specified
        :return: The requested client
        :rtype: aiosu.v2.client.Client
        """
        client_id: int = kwargs.pop("id", None)
        token: OAuthToken = kwargs.pop("token", None)
        if await self.client_exists(client_id):
            client = await self.client_repository.get(client_id)
            if not client:
                raise ValueError("Client not found. This should never happen.")
            return client
        if token is not None:
            return await self.add_client(token)
        raise ValueError("Either id or token must be specified.")

    async def close(self) -> None:
        r"""Closes all client sessions."""
        for client in await self.client_repository.get_all():
            await client.close()
