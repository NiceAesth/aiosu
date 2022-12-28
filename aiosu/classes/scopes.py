from __future__ import annotations

from enum import IntFlag
from enum import unique


@unique
class Scopes(IntFlag):
    PUBLIC = 0
    IDENTIFY = 1 << 0
    FRIENDS_READ = 1 << 1
    FORUM_WRITE = 1 << 2
    DELEGATE = 1 << 3
    CHAT_WRITE = 1 << 4
    LAZER = 1 << 5  # unused, lazer endpoints are not planned for support
