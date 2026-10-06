from __future__ import annotations

import pytest

import aiosu

from ..classes import MockResponse


class TestClientStorage:
    @pytest.mark.asyncio
    async def test_get_client(self, mocker, friends_token, user_data):
        client_storage = aiosu.v2.ClientStorage()
        resp = MockResponse(user_data, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)

        client_1 = await client_storage.get_client(token=friends_token)
        client_2 = await client_storage.get_client(id=client_1.session_id)

        assert client_1 == client_2
        await client_storage.aclose()

    @pytest.mark.asyncio
    async def test_add_client(self, mocker, friends_token, user_data):
        client_storage = aiosu.v2.ClientStorage()
        resp = MockResponse(user_data, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)

        client_1 = await client_storage.add_client(token=friends_token)
        client_2 = await client_storage.get_client(id=client_1.session_id)

        assert client_1 == client_2
        await client_storage.aclose()

    @pytest.mark.asyncio
    async def test_revoke_client(self, mocker, friends_token, user_data):
        client_storage = aiosu.v2.ClientStorage()
        resp = MockResponse(user_data, 200)
        resp_del = MockResponse("", 204)

        def mock_request(*args, **kwargs):
            if args[0] == "DELETE":
                return resp_del
            return resp

        mocker.patch("aiohttp.ClientSession.request", side_effect=mock_request)

        client = await client_storage.add_client(token=friends_token)

        await client_storage.revoke_client(client.session_id)
        with pytest.raises(aiosu.exceptions.InvalidClientRequestedError):
            await client_storage.get_client(id=client.session_id)

        await client_storage.aclose()
