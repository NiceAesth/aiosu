from __future__ import annotations

from datetime import datetime
from datetime import timedelta

import pytest

import aiosu
from ..classes import MockResponse


@pytest.fixture
def token():
    token = aiosu.models.OAuthToken(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiZnJpZW5kcy5yZWFkIiwiaWRlbnRpZnkiLCJwdWJsaWMiXX0.dps4hJ4HwjQ7scacQRBHs1FN0tcGPfYPCUxQjt6ueEo4Q-G-BmkJSGQo6dDhXD1WnXFJdW14prl_fzjvBi7U-9Y7AcLHSMRSbmRa2uS7KciZv7vHpS6Cs64uZO1WqBpOswZJtCfjBeimSrvU9O_zezg3cujrhNTCwbsBOaK1mR9YtxXhw4Y6ORLKqS9ahF1FyXBIZ3pSFBFOxbAtIIDwtZq9CDbffqQrVL7MiNojPBVmhReomf2pSyNM0UIA5u7pCXQOsb4VvmhSPGj7HPoORNyc6CM1iwcmGsrEPDL3d1ZtNtYyiLtarvUZx1WUau9GDAs-AtJ9XaypJTqUjfya7g",
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
        client_2 = await client_storage.get_client(id=client_1.session_id)

        assert client_1 == client_2
        await client_storage.close()
