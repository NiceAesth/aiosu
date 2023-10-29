"""
This module contains models for API v2 scopes.
"""
from __future__ import annotations

from enum import IntFlag
from enum import unique

__all__ = (
    "OWN_CLIENT_SCOPES",
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
    CHAT_READ = 1 << 5
    CHAT_WRITE = 1 << 6
    CHAT_WRITE_MANAGE = 1 << 7
    LAZER = 1 << 8  # unused, lazer endpoints are not planned for support

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
    "chat.read": Scopes.CHAT_READ,
    "chat.write": Scopes.CHAT_WRITE,
    "chat.write_manage": Scopes.CHAT_WRITE_MANAGE,
    "lazer": Scopes.LAZER,
}
VALID_CLIENT_SCOPES = Scopes.PUBLIC | Scopes.DELEGATE
OWN_CLIENT_SCOPES = Scopes.CHAT_READ | Scopes.CHAT_WRITE | Scopes.CHAT_WRITE_MANAGE
