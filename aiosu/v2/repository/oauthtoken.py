"""This module contains a repository for API v2 token objects."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from ...models import OAuthToken

__all__ = ("BaseTokenRepository", "SimpleTokenRepository")


class BaseTokenRepository(ABC):
    """Base token repository. Allows for custom token storage."""

    @abstractmethod
    async def exists(self, session_id: int) -> bool:
        """Check if a token exists."""
        ...

    @abstractmethod
    async def add(self, session_id: int, token: OAuthToken) -> OAuthToken:
        """Add a token."""
        ...

    @abstractmethod
    async def get(self, session_id: int) -> OAuthToken:
        """Get a token."""
        ...

    @abstractmethod
    async def update(self, session_id: int, token: OAuthToken) -> OAuthToken:
        """Update a token."""
        ...


class SimpleTokenRepository(BaseTokenRepository):
    """Simple in-memory token repository."""

    def __init__(self) -> None:
        self._tokens: dict[int, OAuthToken] = {}

    async def exists(self, session_id: int) -> bool:
        """Check if a token exists."""
        return session_id in self._tokens

    async def add(self, session_id: int, token: OAuthToken) -> OAuthToken:
        """Add a token."""
        self._tokens[session_id] = token
        return token

    async def get(self, session_id: int) -> OAuthToken:
        """Get a token."""
        return self._tokens[session_id]

    async def update(self, session_id: int, token: OAuthToken) -> OAuthToken:
        """Update a token."""
        self._tokens[session_id] = token
        return token
