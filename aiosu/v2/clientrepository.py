"""
This module handles CRUD operations for API v2 Client sessions.
"""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from . import Client

if TYPE_CHECKING:
    from typing import Optional

__all__ = ("BaseClientRepository", "SimpleClientRepository")


class BaseClientRepository(ABC):
    """Base class for Client repositories. Implement this to use your own repository."""

    @abstractmethod
    async def exists(self, client_id: int) -> bool:
        ...

    @abstractmethod
    async def add(self, client_id: int, client: Client) -> Client:
        ...

    @abstractmethod
    async def get(self, client_id: int) -> Optional[Client]:
        ...

    @abstractmethod
    async def get_all(self) -> list[Client]:
        ...

    @abstractmethod
    async def update(self, client_id: int, client: Client) -> None:
        ...

    @abstractmethod
    async def delete(self, client_id: int) -> None:
        ...


class SimpleClientRepository(BaseClientRepository):
    """Simple in-memory client repository."""

    def __init__(self) -> None:
        self.clients: dict[int, Client] = {}

    async def exists(self, client_id: int) -> bool:
        return client_id in self.clients

    async def add(self, client_id: int, client: Client) -> Client:
        self.clients[client_id] = client
        return client

    async def get(self, client_id: int) -> Optional[Client]:
        return self.clients.get(client_id)

    async def get_all(self) -> list[Client]:
        return list(self.clients.values())

    async def update(self, client_id: int, client: Client) -> None:
        self.clients[client_id] = client

    async def delete(self, client_id: int) -> None:
        del self.clients[client_id]
