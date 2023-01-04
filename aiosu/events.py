"""
This module contains base classes for library events.
"""
from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type
    from typing import Callable
    from .models import OAuthToken


class Eventable(abc.ABC):
    """Abstract for classes that handle events"""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable]] = {}

    def _register_event(self, event: Type[BaseEvent]) -> None:
        r"""Registers an event

        :param event: Event type to register
        :type event: Type[BaseEvent]
        """
        self._listeners[event._name] = []

    def _register_listener(self, func: Callable, event: Type[BaseEvent]) -> None:
        r"""Registers an event listener

        :param func: Function to call when event is emitted
        :type func: Callable
        :param event: Event type to listen for
        :type event: Type[BaseEvent]

        :raises NotImplementedError: If event is not implemented
        """
        if event._name not in self._listeners:
            raise NotImplementedError(f"{event!r}")
        self._listeners[event._name].append(func)

    async def _process_event(self, event: BaseEvent) -> None:
        r"""Processes an event

        :param event: Event to process
        :type event: BaseEvent

        :raises NotImplementedError: If event is not implemented
        """
        if event._name not in self._listeners:
            raise NotImplementedError(f"{event!r}")
        for listener in self._listeners[event._name]:
            await listener(event)


@dataclasses.dataclass
class BaseEvent(abc.ABC):
    """Abstract for event classes"""

    _name = "BaseEvent"


@dataclasses.dataclass
class ClientAddEvent(BaseEvent):
    """Event for when a client is added"""

    _name = "ClientAddEvent"
    client_id: int
    """0 if app client"""
    client: Eventable
    """The client that was added"""


@dataclasses.dataclass
class ClientUpdateEvent(BaseEvent):
    """Event for when a client is updated"""

    _name = "ClientUpdateEvent"
    client: Eventable
    old_token: OAuthToken
    new_token: OAuthToken
