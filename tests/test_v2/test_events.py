from __future__ import annotations

from datetime import datetime
from datetime import timedelta

import orjson
import pytest

import aiosu
from ..classes import MockResponse


def to_bytes(obj):
    return orjson.dumps(obj)


@pytest.fixture
def token():
    token = aiosu.models.OAuthToken(
        refresh_token="hi",
        expires_on=datetime.utcnow() + timedelta(days=1),
    )
    return token


@pytest.fixture
def token_expired():
    token = aiosu.models.OAuthToken(
        refresh_token="hi",
        expires_on=datetime.utcnow() - timedelta(days=1),
    )
    return token


@pytest.fixture
def user():
    def _user(mode="osu"):
        with open(f"tests/data/v2/single_user_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _user


class TestEvents:
    @pytest.mark.asyncio
    async def test_cs_add_client(self, mocker, token, user):
        client_storage = aiosu.v2.ClientStorage()

        @client_storage.on_client_add
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user(), 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)

        await client_storage.add_client(token=token)

        assert decorated.times_called == 1
        await client_storage.close()

    @pytest.mark.asyncio
    async def test_cs_update_client(self, mocker, token, token_expired, user):
        client_storage = aiosu.v2.ClientStorage()

        @client_storage.on_client_update
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user(), 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        resp_token = MockResponse(to_bytes(token.dict()), 200)
        mocker.patch("aiohttp.ClientSession.post", return_value=resp_token)

        client = await client_storage.add_client(token=token_expired)
        user = await client.get_me()

        assert decorated.times_called == 1
        await client_storage.close()

    @pytest.mark.asyncio
    async def test_update_client(self, mocker, token, token_expired, user):
        client = aiosu.v2.Client(token=token_expired)

        @client.on_client_update
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user(), 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        resp_token = MockResponse(to_bytes(token.dict()), 200)
        mocker.patch("aiohttp.ClientSession.post", return_value=resp_token)

        user = await client.get_me()
        user = await client.get_me()

        assert decorated.times_called == 1
        await client.close()
