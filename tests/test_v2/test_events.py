from __future__ import annotations

import orjson
import pytest

import aiosu

from ..classes import MockResponse


def to_bytes(obj):
    return orjson.dumps(obj)


class TestEvents:
    @pytest.mark.asyncio
    async def test_cs_add_client(self, mocker, identify_token, user_data):
        client_storage = aiosu.v2.ClientStorage()

        @client_storage.on_client_add
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user_data, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)

        await client_storage.add_client(token=identify_token)

        assert decorated.times_called == 1
        await client_storage.aclose()

    @pytest.mark.asyncio
    async def test_cs_update_client(
        self,
        mocker,
        identify_token,
        expired_identify_token,
        user_data,
    ):
        client_storage = aiosu.v2.ClientStorage()

        @client_storage.on_client_update
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user_data, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)
        resp_token = MockResponse(to_bytes(identify_token.model_dump()), 200)
        mocker.patch("aiohttp.ClientSession.post", return_value=resp_token)

        client = await client_storage.add_client(token=expired_identify_token)
        user = await client.get_me()

        assert decorated.times_called == 1
        await client_storage.aclose()

    @pytest.mark.asyncio
    async def test_update_client(
        self,
        mocker,
        identify_token,
        expired_identify_token,
        user_data,
    ):
        client = aiosu.v2.Client(token=expired_identify_token)

        @client.on_client_update
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user_data, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)
        resp_token = MockResponse(to_bytes(identify_token.model_dump()), 200)
        mocker.patch("aiohttp.ClientSession.post", return_value=resp_token)

        user = await client.get_me()
        user = await client.get_me()

        assert decorated.times_called == 1
        await client.aclose()
