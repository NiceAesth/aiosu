"""
This module contains models for API v2 scopes.
"""
from __future__ import annotations

from enum import IntFlag
from enum import unique

__all__ = (
    "Scopes",
    "VALID_CLIENT_SCOPES",
)


@unique
class Scopes(IntFlag):
    NONE = 0
    PUBLIC = 1 << 0
    IDENTIFY = 1 << 1
    FRIENDS_READ = 1 << 2
    FORUM_WRITE = 1 << 3
    DELEGATE = 1 << 4
    CHAT_WRITE = 1 << 5
    LAZER = 1 << 6  # unused, lazer endpoints are not planned for support

    def __flags__(self) -> list[Scopes]:
        scopes_list = [scope for scope in Scopes if self & scope]
        return scopes_list

    def __str__(self) -> str:
        return " ".join(
            scope_name
            for scope_name, scope in API_SCOPE_NAMES.items()
            if scope in self.__flags__()
        )

    @classmethod
    def from_api_list(cls, scopes: list[str]) -> Scopes:
        return cls(sum(API_SCOPE_NAMES[scope] for scope in scopes))


API_SCOPE_NAMES = {
    "public": Scopes.PUBLIC,
    "identify": Scopes.IDENTIFY,
    "friends.read": Scopes.FRIENDS_READ,
    "forum.write": Scopes.FORUM_WRITE,
    "delegate": Scopes.DELEGATE,
    "chat.write": Scopes.CHAT_WRITE,
    "lazer": Scopes.LAZER,
}
VALID_CLIENT_SCOPES = Scopes.PUBLIC | Scopes.DELEGATE
