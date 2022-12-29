from __future__ import annotations

from datetime import datetime
from datetime import timedelta

import orjson
import pytest

import aiosu
from ..classes import MockResponse


@pytest.fixture
def token():
    token = aiosu.classes.OAuthToken(
        refresh_token="hi",
        expires_on=datetime.utcnow() + timedelta(days=1),
    )
    return token


@pytest.fixture
def user():
    def _user(mode="osu"):
        with open(f"tests/data/v2/single_user_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _user


class TestClientStorage:
    @pytest.mark.asyncio
    async def test_get_client(self, mocker, token, user):
        client_storage = aiosu.v2.ClientStorage()
        resp = MockResponse(user(), 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)

        client_1 = await client_storage.get_client(token=token)
        client_1_user = await client_1.get_me()
        client_2 = await client_storage.get_client(id=client_1_user.id)

        assert client_1 == client_2
        await client_storage.close()
