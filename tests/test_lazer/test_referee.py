from __future__ import annotations

import asyncio
import re
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import orjson
import pytest

import aiosu

from ..classes import mock_referee_response


def get_data(name: str) -> bytes:
    with open(f"tests/data/lazer/referee/{name}.json", "rb") as f:
        return f.read()


@pytest.fixture
def signalr(mocker):
    connection = MagicMock()

    async def run():
        await connection.on_open.call_args.args[0]()
        await asyncio.Event().wait()

    connection.run = AsyncMock(side_effect=run)
    connection.send = AsyncMock(
        side_effect=mock_referee_response(get_data("close_room")),
    )
    return mocker.patch(
        "aiosu.lazer.referee.SignalRClient",
        return_value=connection,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    orjson.loads(get_data("commands")),
    ids=lambda case: case["method"],
)
async def test_referee_commands(case, identify_token, signalr):
    kwargs = case["kwargs"].copy()
    if case["request_model"] is not None:
        model = getattr(aiosu.models, case["request_model"])
        kwargs["request"] = model.model_validate(kwargs["request"])
    connection = signalr.return_value
    connection.send.side_effect = mock_referee_response(get_data(case["response"]))
    async with aiosu.lazer.RefereeClient(token=identify_token) as client:
        response = await getattr(client, case["method"])(**kwargs)
    if case["response_model"] is not None:
        assert isinstance(response, getattr(aiosu.models, case["response_model"]))
    else:
        assert response is None
    assert connection.send.await_args.args[:2] == (case["target"], case["arguments"])
    connection.send.assert_awaited_once()


def test_room_model():
    room = aiosu.models.RefereeRoomJoinedResponse.model_validate_json(
        get_data("room_with_players"),
    )
    assert isinstance(room.state, aiosu.models.RefereeMatchState)
    assert isinstance(room.players[0], aiosu.models.RefereePlayer)
    assert isinstance(room.referees[0], aiosu.models.RefereeUser)
    assert isinstance(room.playlist[0], aiosu.models.RefereePlaylistItem)
    assert room.state.slots == [5, None]
    assert room.playlist[0].required_mods[0].settings == {"speed_change": 1.2}
    assert room.playlist[0].allowed_mods[0].settings is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "target, model",
    [
        ("UserJoined", aiosu.models.RefereeUserJoinedEvent),
        ("UserLeft", aiosu.models.RefereeUserLeftEvent),
        ("RefereeAdded", aiosu.models.RefereeAddedEvent),
        ("RefereeRemoved", aiosu.models.RefereeRemovedEvent),
        ("UserKicked", aiosu.models.RefereeUserKickedEvent),
        ("UserBanned", aiosu.models.RefereeUserBannedEvent),
        ("RefereeInvited", aiosu.models.RefereeInvitedEvent),
        ("RoomSettingsChanged", aiosu.models.RefereeRoomSettingsChangedEvent),
        ("MatchStateChanged", aiosu.models.RefereeMatchStateChangedEvent),
        ("PlaylistItemAdded", aiosu.models.RefereePlaylistItemAddedEvent),
        ("PlaylistItemChanged", aiosu.models.RefereePlaylistItemChangedEvent),
        ("PlaylistItemRemoved", aiosu.models.RefereePlaylistItemRemovedEvent),
        ("RollCompleted", aiosu.models.RefereeRollCompletedEvent),
        ("UserStatusChanged", aiosu.models.RefereeUserStatusChangedEvent),
        ("UserModsChanged", aiosu.models.RefereeUserModsChangedEvent),
        ("UserStyleChanged", aiosu.models.RefereeUserStyleChangedEvent),
        ("UserTeamChanged", aiosu.models.RefereeUserTeamChangedEvent),
        ("CountdownStarted", aiosu.models.RefereeCountdownStartedEvent),
        ("CountdownStopped", aiosu.models.RefereeCountdownStoppedEvent),
        ("MatchStarted", aiosu.models.RefereeMatchStartedEvent),
        ("MatchAborted", aiosu.models.RefereeMatchAbortedEvent),
        ("MatchCompleted", aiosu.models.RefereeMatchCompletedEvent),
    ],
)
async def test_referee_events(target, model, identify_token, signalr):
    data = orjson.loads(get_data(model.__name__))
    received = []
    done = asyncio.Event()
    client = aiosu.lazer.RefereeClient(token=identify_token)

    async def listener(event):
        assert isinstance(event, model)
        received.append(event)
        assert isinstance(
            await client.list_rooms(),
            aiosu.models.RefereeListRoomsResponse,
        )
        done.set()

    name = re.sub(r"(?<!^)(?=[A-Z])", "_", target).lower()
    getattr(client, f"on_{name}")(listener)
    connection = signalr.return_value
    connection.send.side_effect = mock_referee_response(get_data("list_rooms"))
    async with client:
        handler = next(
            call.args[1]
            for call in connection.on.call_args_list
            if call.args[0] == target
        )
        await handler([data])
        await asyncio.wait_for(done.wait(), 1)
    assert len(received) == 1
    assert received[0].room_id == data["room_id"]


@pytest.mark.asyncio
async def test_referee_connect(identify_token, signalr):
    client = aiosu.lazer.RefereeClient(token=identify_token)
    async with client:
        await client.connect()
        assert client.connected
    signalr.assert_called_once_with(
        "https://spectator.ppy.sh/referee",
        headers={"Authorization": f"Bearer {identify_token.access_token}"},
        connection_timeout=10,
        retry_count=1,
    )
    assert not client.connected
    assert client._task is None
    await client.aclose()


@pytest.mark.asyncio
async def test_referee_invocation_error(identify_token, signalr):
    connection = signalr.return_value
    connection.send.side_effect = mock_referee_response(
        get_data("command_error"),
        error=True,
    )
    async with aiosu.lazer.RefereeClient(token=identify_token) as client:
        with pytest.raises(aiosu.exceptions.RefereeInvocationError) as exc:
            await client.kick_player(42, 5)
        assert exc.value.code == 5
        assert str(exc.value) == orjson.loads(get_data("command_error"))["error"]
        assert client.connected


@pytest.mark.asyncio
async def test_referee_connect_failure(identify_token, signalr):
    signalr.return_value.run.side_effect = ConnectionError
    client = aiosu.lazer.RefereeClient(token=identify_token)
    with pytest.raises(ConnectionError):
        await client.connect()
    assert client._task is None
    assert client._connection is None
    assert not client.connected


@pytest.mark.asyncio
async def test_referee_connect_timeout(identify_token, signalr):
    signalr.return_value.run.side_effect = asyncio.Event().wait
    client = aiosu.lazer.RefereeClient(token=identify_token, connection_timeout=0.01)
    with pytest.raises(TimeoutError):
        await client.connect()
    assert client._task is None
    assert not client.connected


@pytest.mark.asyncio
async def test_referee_invocation_timeout(identify_token, signalr):
    signalr.return_value.send.side_effect = None
    async with aiosu.lazer.RefereeClient(
        token=identify_token,
        invocation_timeout=0.01,
    ) as client:
        with pytest.raises(TimeoutError):
            await client.roll(42)
        assert not client._pending


@pytest.mark.asyncio
async def test_referee_invocation_cancellation(identify_token, signalr):
    signalr.return_value.send.side_effect = None
    async with aiosu.lazer.RefereeClient(token=identify_token) as client:
        task = asyncio.create_task(client.roll(42))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not client._pending


@pytest.mark.asyncio
async def test_referee_disconnect(identify_token, signalr):
    connection = signalr.return_value
    connection.send.side_effect = None
    async with aiosu.lazer.RefereeClient(token=identify_token) as client:
        pending = asyncio.create_task(client.roll(42))
        await asyncio.sleep(0)
        await connection.on_close.call_args.args[0]()
        with pytest.raises(ConnectionError):
            await pending
        with pytest.raises(ConnectionError):
            await client.wait_closed()
        assert not client.connected


@pytest.mark.asyncio
async def test_referee_reconnect(identify_token, signalr):
    provider = AsyncMock(return_value=identify_token)
    client = aiosu.lazer.RefereeClient(token_provider=provider)
    async with client:
        assert provider.await_count == 1
    async with client:
        assert provider.await_count == 2
    assert signalr.call_count == 2


@pytest.mark.asyncio
async def test_referee_close_pending_call(identify_token, signalr):
    signalr.return_value.send.side_effect = None
    client = aiosu.lazer.RefereeClient(token=identify_token)
    await client.connect()
    task = asyncio.create_task(client.roll(42))
    await asyncio.sleep(0)
    await client.aclose()
    with pytest.raises(ConnectionError):
        await task
    with pytest.raises(ConnectionError):
        await client.list_rooms()


@pytest.mark.asyncio
async def test_referee_wait_closed(identify_token, signalr):
    client = aiosu.lazer.RefereeClient(token=identify_token)
    await client.connect()
    waiting = asyncio.create_task(client.wait_closed())
    await asyncio.sleep(0)
    await client.aclose()
    await asyncio.wait_for(waiting, 1)


@pytest.mark.asyncio
async def test_referee_handler_can_close_client(identify_token, signalr):
    client = aiosu.lazer.RefereeClient(token=identify_token)
    done = asyncio.Event()

    @client.on_roll_completed
    async def listener(event):
        await client.aclose()
        done.set()

    async with client:
        handler = next(
            call.args[1]
            for call in signalr.return_value.on.call_args_list
            if call.args[0] == "RollCompleted"
        )
        await handler([orjson.loads(get_data("RefereeRollCompletedEvent"))])
        await asyncio.wait_for(done.wait(), 1)
    assert client._task is None
