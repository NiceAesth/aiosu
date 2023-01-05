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
        return " ".join(scope.name.lower() for scope in self.__flags__())  # type: ignore


VALID_CLIENT_SCOPES = Scopes.PUBLIC | Scopes.DELEGATE
