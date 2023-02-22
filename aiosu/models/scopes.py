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
    PUBLIC = 0
    IDENTIFY = 1 << 0
    FRIENDS_READ = 1 << 1
    FORUM_WRITE = 1 << 2
    DELEGATE = 1 << 3
    CHAT_WRITE = 1 << 4
    LAZER = 1 << 5  # unused, lazer endpoints are not planned for support

    def __flags__(self) -> list[Scopes]:
        scopes_list = [scope for scope in Scopes if self & scope]
        if self.PUBLIC not in scopes_list:
            scopes_list.append(Scopes.PUBLIC)
        return scopes_list

    def __str__(self) -> str:
        return " ".join(
            scope for scope, value in API_SCOPE_NAMES.items() if self & value
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
