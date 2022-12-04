from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from .token import OAuthToken


class Eventable(abc.ABC):
    """Abstract for classes that handle events"""

    def __init__(self) -> None:
        self._listeners: list[Callable] = []

    @abc.abstractmethod
    async def _process_event(self, event: BaseEvent) -> None:
        ...


@dataclasses.dataclass
class BaseEvent(abc.ABC):
    """Abstract for event classes"""


@dataclasses.dataclass
class ClientAddEvent(BaseEvent):
    client_id: int
    """0 if app client"""
    client: Eventable
    """The client that was added"""


@dataclasses.dataclass
class ClientUpdateEvent(BaseEvent):
    client: Eventable
    old_token: OAuthToken
    new_token: OAuthToken
