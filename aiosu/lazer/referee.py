"""This module contains the client for interfacing with the osu!lazer referee API."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Coroutine
from types import TracebackType
from typing import Any
from typing import Self

from pysignalr.client import SignalRClient
from pysignalr.exceptions import ServerError
from pysignalr.messages import CompletionMessage
from pysignalr.messages import Message

from .. import models
from ..exceptions import RefereeInvocationError
from ..models import OAuthToken
from ..models.base import BaseModel

__all__ = ("RefereeClient",)

type EventCallback[T] = Callable[[T], Coroutine[Any, Any, None]]
type TokenProvider = Callable[[], Awaitable[OAuthToken | str]]

_EVENTS: dict[str, type[BaseModel]] = {
    "UserJoined": models.RefereeUserJoinedEvent,
    "UserLeft": models.RefereeUserLeftEvent,
    "UserKicked": models.RefereeUserKickedEvent,
    "UserBanned": models.RefereeUserBannedEvent,
    "RefereeAdded": models.RefereeAddedEvent,
    "RefereeRemoved": models.RefereeRemovedEvent,
    "RefereeInvited": models.RefereeInvitedEvent,
    "RoomSettingsChanged": models.RefereeRoomSettingsChangedEvent,
    "MatchStateChanged": models.RefereeMatchStateChangedEvent,
    "PlaylistItemAdded": models.RefereePlaylistItemAddedEvent,
    "PlaylistItemChanged": models.RefereePlaylistItemChangedEvent,
    "PlaylistItemRemoved": models.RefereePlaylistItemRemovedEvent,
    "RollCompleted": models.RefereeRollCompletedEvent,
    "UserStatusChanged": models.RefereeUserStatusChangedEvent,
    "UserModsChanged": models.RefereeUserModsChangedEvent,
    "UserStyleChanged": models.RefereeUserStyleChangedEvent,
    "UserTeamChanged": models.RefereeUserTeamChangedEvent,
    "CountdownStopped": models.RefereeCountdownStoppedEvent,
    "CountdownStarted": models.RefereeCountdownStartedEvent,
    "MatchAborted": models.RefereeMatchAbortedEvent,
    "MatchCompleted": models.RefereeMatchCompletedEvent,
    "MatchStarted": models.RefereeMatchStartedEvent,
}


class RefereeClient:
    def __init__(
        self,
        token: OAuthToken | str | None = None,
        *,
        base_url: str = "https://spectator.ppy.sh",
        token_provider: TokenProvider | None = None,
        connection_timeout: int = 10,
        invocation_timeout: float = 30,
    ) -> None:
        r"""osu!lazer referee client.
        :param token: OAuth token, defaults to None
        :type token: aiosu.models.OAuthToken | str | None, optional
        :param base_url: Base server URL, defaults to "https://spectator.ppy.sh"
        :type base_url: str, optional
        :param token_provider: The callable to get the token, defaults to None
        :type token_provider: Callable[[], Awaitable[OAuthToken | str]] | None, optional
        :param connection_timeout: The connection timeout in seconds, defaults to 10
        :type connection_timeout: int, optional
        :param invocation_timeout: The request timeout in seconds, defaults to 30
        :type invocation_timeout: float, optional

        :raises ValueError: If token and token_provider are both provided or both missing
        :raises ValueError: If the timeouts are not positive
        """
        if (token is None) == (token_provider is None):
            raise ValueError("Provide either token or token_provider.")
        if connection_timeout <= 0 or invocation_timeout <= 0:
            raise ValueError("Timeouts must be positive.")
        self._token = token
        self._token_provider = token_provider
        self._url = f"{base_url.rstrip('/')}/referee"
        self._connection_timeout = connection_timeout
        self._invocation_timeout = invocation_timeout
        self._connection: SignalRClient | None = None
        self._task: asyncio.Task[None] | None = None
        self._events: set[asyncio.Task[None]] = set()
        self._listeners: dict[str, EventCallback[Any]] = {}
        self._pending: set[asyncio.Future[Any]] = set()
        self._ready = asyncio.Event()
        self._connected = False
        self._error: Exception | None = None

    @property
    def connected(self) -> bool:
        r"""Returns whether the client is connected.

        :return: Whether the client is connected
        :rtype: bool
        """
        return self._connected

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def connect(self) -> None:
        r"""Connects to the referee server.

        :raises ValueError: If the access token is empty
        :raises ConnectionError: If the connection is closed
        :raises TimeoutError: If the connection times out
        :return: None
        """
        if self.connected:
            return
        if self._task is None or self._task.done():
            self._error = None
            self._ready.clear()
            self._task = asyncio.create_task(self._run())
        try:
            await asyncio.wait_for(self._ready.wait(), self._connection_timeout)
            if self._error is not None:
                raise self._error
        except BaseException:
            await self.aclose()
            raise

    async def _run(self) -> None:
        try:
            token = self._token
            if self._token_provider is not None:
                token = await self._token_provider()
            access_token = (
                token.access_token if isinstance(token, OAuthToken) else token
            )
            if not access_token:
                raise ValueError("Access token must not be empty.")
            connection = SignalRClient(
                self._url,
                headers={"Authorization": f"Bearer {access_token}"},
                connection_timeout=self._connection_timeout,
                retry_count=1,
            )
            self._connection = connection
            connection.on_open(self._on_open)
            connection.on_close(self._on_close)
            connection.on_error(self._on_error)
            for target in _EVENTS:
                connection.on(target, functools.partial(self._on_event, target))
            await connection.run()
        except ServerError as exc:
            self._error = ConnectionError(str(exc))
        except Exception as exc:
            self._error = exc
        finally:
            self._connected = False
            self._ready.set()
            for future in self._pending:
                if not future.done():
                    future.set_exception(
                        self._error or ConnectionError("Referee connection closed."),
                    )

    async def _on_open(self) -> None:
        self._connected = True
        self._ready.set()

    async def _on_close(self) -> None:
        self._error = ConnectionError("Referee connection closed.")
        if self._task is not None:
            self._task.cancel()

    async def _on_error(self, message: CompletionMessage) -> None:
        pass

    async def wait_closed(self) -> None:
        r"""Waits for the connection to close.

        :raises ConnectionError: If the connection is closed
        :return: None
        """
        task = self._task
        if task is not None:
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.cancelled():
                    raise
        if self._error is not None:
            raise self._error

    async def aclose(self) -> None:
        r"""Closes the client.

        :return: None
        """
        self._connected = False
        current = asyncio.current_task()
        tasks = [
            task
            for task in (self._task, *self._events)
            if task is not None and task is not current
        ]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._task = None
        self._connection = None

    async def _invoke(self, target: str, *arguments: Any) -> Any:
        if not self.connected or self._connection is None:
            raise ConnectionError(
                "Connect the referee client before invoking commands.",
            )
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending.add(future)

        async def completed(message: Message) -> None:
            if future.done():
                return
            assert isinstance(message, CompletionMessage)
            if message.error:
                future.set_exception(RefereeInvocationError(message.error))
            else:
                future.set_result(message.result)

        payload = [
            (
                argument.model_dump(mode="json", by_alias=True)
                if isinstance(argument, BaseModel)
                else argument
            )
            for argument in arguments
        ]
        try:
            async with asyncio.timeout(self._invocation_timeout):
                await self._connection.send(target, payload, completed)
                return await future
        finally:
            self._pending.discard(future)
            if future.done() and not future.cancelled():
                future.exception()
            else:
                future.cancel()

    def _on[T: BaseModel](
        self,
        target: str,
        func: EventCallback[T],
    ) -> EventCallback[T]:
        self._listeners[target] = func
        return func

    async def _on_event(self, target: str, arguments: list[Any]) -> None:
        listener = self._listeners.get(target)
        if listener is None:
            return
        event = _EVENTS[target].model_validate(arguments[0])
        task = asyncio.create_task(listener(event))
        self._events.add(task)
        task.add_done_callback(self._event_done)

    def _event_done(self, task: asyncio.Task[None]) -> None:
        self._events.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            asyncio.get_running_loop().call_exception_handler(
                {
                    "message": "Referee event handler failed.",
                    "exception": error,
                },
            )

    async def make_room(
        self,
        request: models.RefereeMakeRoomRequest,
    ) -> models.RefereeRoomJoinedResponse:
        r"""Creates a multiplayer room.

        :param request: The request to create the room
        :type request: aiosu.models.referee.RefereeMakeRoomRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: Room joined response object
        :rtype: aiosu.models.referee.RefereeRoomJoinedResponse
        """
        return models.RefereeRoomJoinedResponse.model_validate(
            await self._invoke("MakeRoom", request),
        )

    async def join_room(self, room_id: int) -> models.RefereeRoomJoinedResponse:
        r"""Joins a multiplayer room.

        :param room_id: The room ID to join
        :type room_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: Room joined response object
        :rtype: aiosu.models.referee.RefereeRoomJoinedResponse
        """
        return models.RefereeRoomJoinedResponse.model_validate(
            await self._invoke("JoinRoom", room_id),
        )

    async def list_rooms(self) -> models.RefereeListRoomsResponse:
        r"""Gets a list of rooms.

        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: List rooms response object
        :rtype: aiosu.models.referee.RefereeListRoomsResponse
        """
        return models.RefereeListRoomsResponse.model_validate(
            await self._invoke("ListRooms"),
        )

    async def roll(
        self,
        room_id: int,
        request: models.RefereeRollRequest | None = None,
    ) -> None:
        r"""Rolls a random number in a multiplayer room.

        :param room_id: The room ID to roll in
        :type room_id: int
        :param request: The request to roll, defaults to None
        :type request: aiosu.models.referee.RefereeRollRequest | None
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("Roll", room_id, request)

    async def close_room(self, room_id: int) -> None:
        r"""Closes a multiplayer room.

        :param room_id: The room ID to close
        :type room_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("CloseRoom", room_id)

    async def invite_player(self, room_id: int, user_id: int) -> None:
        r"""Invites a player to a multiplayer room.

        :param room_id: The room ID to invite the player to
        :type room_id: int
        :param user_id: The user ID to invite
        :type user_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("InvitePlayer", room_id, user_id)

    async def kick_player(self, room_id: int, user_id: int) -> None:
        r"""Kicks a player from a multiplayer room.

        :param room_id: The room ID to kick the player from
        :type room_id: int
        :param user_id: The user ID to kick
        :type user_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("KickPlayer", room_id, user_id)

    async def ban_user(self, room_id: int, user_id: int) -> None:
        r"""Bans a user from a multiplayer room.

        :param room_id: The room ID to ban the user from
        :type room_id: int
        :param user_id: The user ID to ban
        :type user_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("BanUser", room_id, user_id)

    async def add_referee(self, room_id: int, user_id: int) -> None:
        r"""Adds a referee to a multiplayer room.

        :param room_id: The room ID to add the referee to
        :type room_id: int
        :param user_id: The user ID to add
        :type user_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("AddReferee", room_id, user_id)

    async def remove_referee(self, room_id: int, user_id: int) -> None:
        r"""Removes a referee from a multiplayer room.

        :param room_id: The room ID to remove the referee from
        :type room_id: int
        :param user_id: The user ID to remove
        :type user_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("RemoveReferee", room_id, user_id)

    async def stop_match_countdown(self, room_id: int) -> None:
        r"""Stops the match countdown in a multiplayer room.

        :param room_id: The room ID to stop the countdown in
        :type room_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("StopMatchCountdown", room_id)

    async def abort_match(self, room_id: int) -> None:
        r"""Aborts a match in a multiplayer room.

        :param room_id: The room ID to abort the match in
        :type room_id: int
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("AbortMatch", room_id)

    async def change_room_settings(
        self,
        room_id: int,
        request: models.RefereeChangeRoomSettingsRequest,
    ) -> None:
        r"""Changes multiplayer room settings.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to change the room settings
        :type request: aiosu.models.referee.RefereeChangeRoomSettingsRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("ChangeRoomSettings", room_id, request)

    async def edit_current_playlist_item(
        self,
        room_id: int,
        request: models.RefereeEditCurrentPlaylistItemRequest,
    ) -> None:
        r"""Edits the current playlist item.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to edit the current playlist item
        :type request: aiosu.models.referee.RefereeEditCurrentPlaylistItemRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("EditCurrentPlaylistItem", room_id, request)

    async def add_playlist_item(
        self,
        room_id: int,
        request: models.RefereeAddPlaylistItemRequest,
    ) -> None:
        r"""Adds a playlist item.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to add the playlist item
        :type request: aiosu.models.referee.RefereeAddPlaylistItemRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("AddPlaylistItem", room_id, request)

    async def edit_playlist_item(
        self,
        room_id: int,
        request: models.RefereeEditPlaylistItemRequest,
    ) -> None:
        r"""Edits a playlist item.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to edit the playlist item
        :type request: aiosu.models.referee.RefereeEditPlaylistItemRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("EditPlaylistItem", room_id, request)

    async def remove_playlist_item(
        self,
        room_id: int,
        request: models.RefereeRemovePlaylistItemRequest,
    ) -> None:
        r"""Removes a playlist item.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to remove the playlist item
        :type request: aiosu.models.referee.RefereeRemovePlaylistItemRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("RemovePlaylistItem", room_id, request)

    async def move_user(
        self,
        room_id: int,
        request: models.RefereeMoveUserRequest,
    ) -> None:
        r"""Moves a user in a multiplayer room.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to move the user
        :type request: aiosu.models.referee.RefereeMoveUserRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("MoveUser", room_id, request)

    async def set_lock_state(
        self,
        room_id: int,
        request: models.RefereeSetLockStateRequest,
    ) -> None:
        r"""Sets the lock state of a multiplayer room.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to set the lock state
        :type request: aiosu.models.referee.RefereeSetLockStateRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("SetLockState", room_id, request)

    async def start_match(
        self,
        room_id: int,
        request: models.RefereeStartGameplayRequest,
    ) -> None:
        r"""Starts a match in a multiplayer room.

        :param room_id: The room ID
        :type room_id: int
        :param request: The request to start the match
        :type request: aiosu.models.referee.RefereeStartGameplayRequest
        :raises RefereeInvocationError: Contains error code and error message
        :raises ConnectionError: If the client is not connected
        :raises TimeoutError: If the request times out
        :return: None
        """
        await self._invoke("StartMatch", room_id, request)

    def on_user_joined(
        self,
        func: EventCallback[models.RefereeUserJoinedEvent],
    ) -> EventCallback[models.RefereeUserJoinedEvent]:
        r"""Returns a callable that is called when a user joins a room, to be used as:
        @client.on_user_joined
        async def user_joined(event: RefereeUserJoinedEvent):
        """
        return self._on("UserJoined", func)

    def on_user_left(
        self,
        func: EventCallback[models.RefereeUserLeftEvent],
    ) -> EventCallback[models.RefereeUserLeftEvent]:
        r"""Returns a callable that is called when a user leaves a room, to be used as:
        @client.on_user_left
        async def user_left(event: RefereeUserLeftEvent):
        """
        return self._on("UserLeft", func)

    def on_user_kicked(
        self,
        func: EventCallback[models.RefereeUserKickedEvent],
    ) -> EventCallback[models.RefereeUserKickedEvent]:
        r"""Returns a callable that is called when a user is kicked from a room, to be used as:
        @client.on_user_kicked
        async def user_kicked(event: RefereeUserKickedEvent):
        """
        return self._on("UserKicked", func)

    def on_user_banned(
        self,
        func: EventCallback[models.RefereeUserBannedEvent],
    ) -> EventCallback[models.RefereeUserBannedEvent]:
        r"""Returns a callable that is called when a user is banned from a room, to be used as:
        @client.on_user_banned
        async def user_banned(event: RefereeUserBannedEvent):
        """
        return self._on("UserBanned", func)

    def on_referee_added(
        self,
        func: EventCallback[models.RefereeAddedEvent],
    ) -> EventCallback[models.RefereeAddedEvent]:
        r"""Returns a callable that is called when a referee is added to a room, to be used as:
        @client.on_referee_added
        async def referee_added(event: RefereeAddedEvent):
        """
        return self._on("RefereeAdded", func)

    def on_referee_removed(
        self,
        func: EventCallback[models.RefereeRemovedEvent],
    ) -> EventCallback[models.RefereeRemovedEvent]:
        r"""Returns a callable that is called when a referee is removed from a room, to be used as:
        @client.on_referee_removed
        async def referee_removed(event: RefereeRemovedEvent):
        """
        return self._on("RefereeRemoved", func)

    def on_referee_invited(
        self,
        func: EventCallback[models.RefereeInvitedEvent],
    ) -> EventCallback[models.RefereeInvitedEvent]:
        r"""Returns a callable that is called when a referee is invited to a room, to be used as:
        @client.on_referee_invited
        async def referee_invited(event: RefereeInvitedEvent):
        """
        return self._on("RefereeInvited", func)

    def on_room_settings_changed(
        self,
        func: EventCallback[models.RefereeRoomSettingsChangedEvent],
    ) -> EventCallback[models.RefereeRoomSettingsChangedEvent]:
        r"""Returns a callable that is called when the room settings are updated, to be used as:
        @client.on_room_settings_changed
        async def room_settings_changed(event: RefereeRoomSettingsChangedEvent):
        """
        return self._on("RoomSettingsChanged", func)

    def on_match_state_changed(
        self,
        func: EventCallback[models.RefereeMatchStateChangedEvent],
    ) -> EventCallback[models.RefereeMatchStateChangedEvent]:
        r"""Returns a callable that is called when the match state is updated, to be used as:
        @client.on_match_state_changed
        async def match_state_changed(event: RefereeMatchStateChangedEvent):
        """
        return self._on("MatchStateChanged", func)

    def on_playlist_item_added(
        self,
        func: EventCallback[models.RefereePlaylistItemAddedEvent],
    ) -> EventCallback[models.RefereePlaylistItemAddedEvent]:
        r"""Returns a callable that is called when a playlist item is added, to be used as:
        @client.on_playlist_item_added
        async def playlist_item_added(event: RefereePlaylistItemAddedEvent):
        """
        return self._on("PlaylistItemAdded", func)

    def on_playlist_item_changed(
        self,
        func: EventCallback[models.RefereePlaylistItemChangedEvent],
    ) -> EventCallback[models.RefereePlaylistItemChangedEvent]:
        r"""Returns a callable that is called when a playlist item is updated, to be used as:
        @client.on_playlist_item_changed
        async def playlist_item_changed(event: RefereePlaylistItemChangedEvent):
        """
        return self._on("PlaylistItemChanged", func)

    def on_playlist_item_removed(
        self,
        func: EventCallback[models.RefereePlaylistItemRemovedEvent],
    ) -> EventCallback[models.RefereePlaylistItemRemovedEvent]:
        r"""Returns a callable that is called when a playlist item is removed, to be used as:
        @client.on_playlist_item_removed
        async def playlist_item_removed(event: RefereePlaylistItemRemovedEvent):
        """
        return self._on("PlaylistItemRemoved", func)

    def on_roll_completed(
        self,
        func: EventCallback[models.RefereeRollCompletedEvent],
    ) -> EventCallback[models.RefereeRollCompletedEvent]:
        r"""Returns a callable that is called when a roll is completed, to be used as:
        @client.on_roll_completed
        async def roll_completed(event: RefereeRollCompletedEvent):
        """
        return self._on("RollCompleted", func)

    def on_user_status_changed(
        self,
        func: EventCallback[models.RefereeUserStatusChangedEvent],
    ) -> EventCallback[models.RefereeUserStatusChangedEvent]:
        r"""Returns a callable that is called when the user status is updated, to be used as:
        @client.on_user_status_changed
        async def user_status_changed(event: RefereeUserStatusChangedEvent):
        """
        return self._on("UserStatusChanged", func)

    def on_user_mods_changed(
        self,
        func: EventCallback[models.RefereeUserModsChangedEvent],
    ) -> EventCallback[models.RefereeUserModsChangedEvent]:
        r"""Returns a callable that is called when the user mods are updated, to be used as:
        @client.on_user_mods_changed
        async def user_mods_changed(event: RefereeUserModsChangedEvent):
        """
        return self._on("UserModsChanged", func)

    def on_user_style_changed(
        self,
        func: EventCallback[models.RefereeUserStyleChangedEvent],
    ) -> EventCallback[models.RefereeUserStyleChangedEvent]:
        r"""Returns a callable that is called when the user style is updated, to be used as:
        @client.on_user_style_changed
        async def user_style_changed(event: RefereeUserStyleChangedEvent):
        """
        return self._on("UserStyleChanged", func)

    def on_user_team_changed(
        self,
        func: EventCallback[models.RefereeUserTeamChangedEvent],
    ) -> EventCallback[models.RefereeUserTeamChangedEvent]:
        r"""Returns a callable that is called when the user team is updated, to be used as:
        @client.on_user_team_changed
        async def user_team_changed(event: RefereeUserTeamChangedEvent):
        """
        return self._on("UserTeamChanged", func)

    def on_countdown_started(
        self,
        func: EventCallback[models.RefereeCountdownStartedEvent],
    ) -> EventCallback[models.RefereeCountdownStartedEvent]:
        r"""Returns a callable that is called when a countdown is started, to be used as:
        @client.on_countdown_started
        async def countdown_started(event: RefereeCountdownStartedEvent):
        """
        return self._on("CountdownStarted", func)

    def on_countdown_stopped(
        self,
        func: EventCallback[models.RefereeCountdownStoppedEvent],
    ) -> EventCallback[models.RefereeCountdownStoppedEvent]:
        r"""Returns a callable that is called when a countdown is stopped, to be used as:
        @client.on_countdown_stopped
        async def countdown_stopped(event: RefereeCountdownStoppedEvent):
        """
        return self._on("CountdownStopped", func)

    def on_match_started(
        self,
        func: EventCallback[models.RefereeMatchStartedEvent],
    ) -> EventCallback[models.RefereeMatchStartedEvent]:
        r"""Returns a callable that is called when a match is started, to be used as:
        @client.on_match_started
        async def match_started(event: RefereeMatchStartedEvent):
        """
        return self._on("MatchStarted", func)

    def on_match_aborted(
        self,
        func: EventCallback[models.RefereeMatchAbortedEvent],
    ) -> EventCallback[models.RefereeMatchAbortedEvent]:
        r"""Returns a callable that is called when a match is aborted, to be used as:
        @client.on_match_aborted
        async def match_aborted(event: RefereeMatchAbortedEvent):
        """
        return self._on("MatchAborted", func)

    def on_match_completed(
        self,
        func: EventCallback[models.RefereeMatchCompletedEvent],
    ) -> EventCallback[models.RefereeMatchCompletedEvent]:
        r"""Returns a callable that is called when a match is completed, to be used as:
        @client.on_match_completed
        async def match_completed(event: RefereeMatchCompletedEvent):
        """
        return self._on("MatchCompleted", func)
