from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import aiohttp
import orjson
import pytest

import aiosu


def test_beatmap_state(lazer_beatmap_state):
    message = aiosu.models.BeatmapStateWebSocketMessage.model_validate_json(
        lazer_beatmap_state,
    )
    assert message.beatmap.beatmap_id == 974423
    assert message.beatmap.status == aiosu.models.BeatmapRankStatus.RANKED
    assert isinstance(message.mods, aiosu.models.Mods)
    assert message.mods[0].settings == {"speed_change": 1.76}


@pytest.mark.parametrize("status", ["None", "LocallyModified"])
def test_local_status(lazer_beatmap_state, status):
    payload = orjson.loads(lazer_beatmap_state)
    payload["beatmap"]["status"] = status
    message = aiosu.models.BeatmapStateWebSocketMessage.model_validate(payload)
    assert message.beatmap.status == status


@pytest.mark.parametrize("status", ["WatchingReplay", "SpectatingUser"])
def test_replay_activity(status):
    message = aiosu.models.UserActivityWebSocketMessage.model_validate(
        {
            "status": status,
            "data": {"score_id": 123, "user_id": 456, "beatmap_id": 789},
        },
    )
    assert isinstance(
        message.data,
        aiosu.models.WebSocketWatchingReplayUserActivityData,
    )
    assert message.data.user_id == 456


def test_activity_without_data():
    message = aiosu.models.UserActivityWebSocketMessage(status="InSoloGame")
    assert message.data is None


def test_unknown_activity(lazer_user_activity):
    payload = orjson.loads(lazer_user_activity)
    payload["status"] = "FutureActivity"
    message = aiosu.models.UserActivityWebSocketMessage.model_validate(payload)
    assert message.data == payload["data"]


@pytest.mark.asyncio
async def test_client_events(mocker, lazer_beatmap_state, lazer_user_activity):
    socket = MagicMock()
    socket.close = AsyncMock()
    socket.__aiter__.return_value = [
        aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, lazer_beatmap_state.decode(), ""),
        aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, lazer_user_activity.decode(), ""),
        aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, '{"type":"FutureMessage"}', ""),
    ]
    connect = mocker.patch(
        "aiohttp.ClientSession.ws_connect",
        new_callable=AsyncMock,
        return_value=socket,
    )
    client = aiosu.lazer.Client()
    received = []
    raw_messages = []

    @client.on_raw_message
    async def on_raw_message(data):
        assert isinstance(data, str)
        raw_messages.append(data)

    @client.on_beatmap_state
    async def on_beatmap_state(event):
        assert isinstance(event, aiosu.models.BeatmapStateWebSocketMessage)
        assert event.beatmap.beatmap_id == 974423
        received.append(event)

    @client.on_user_activity
    async def on_user_activity(event):
        assert isinstance(event, aiosu.models.UserActivityWebSocketMessage)
        assert isinstance(event.data, aiosu.models.WebSocketInLobbyUserActivityData)
        assert event.data.room_id == 123
        received.append(event)

    async with client:
        session = client._session
        await client._task

    assert len(received) == 2
    assert raw_messages == [
        lazer_beatmap_state.decode(),
        lazer_user_activity.decode(),
        '{"type":"FutureMessage"}',
    ]
    connect.assert_awaited_once_with("ws://localhost:49727/")
    socket.close.assert_awaited()
    assert session.closed


@pytest.mark.asyncio
async def test_connect_failure(mocker):
    mocker.patch(
        "aiohttp.ClientSession.ws_connect",
        new_callable=AsyncMock,
        side_effect=ConnectionError,
    )
    close = mocker.patch("aiohttp.ClientSession.close")
    client = aiosu.lazer.Client()
    with pytest.raises(ConnectionError):
        await client.connect()
    close.assert_awaited_once()
    assert client._session is None
