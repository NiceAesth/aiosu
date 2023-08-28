from __future__ import annotations

import orjson
import pytest

import aiosu
from ..classes import MockResponse


def to_bytes(obj):
    return orjson.dumps(obj)


@pytest.fixture
def token():
    token = aiosu.models.OAuthToken(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiaWRlbnRpZnkiLCJwdWJsaWMiXX0.eHwSds48D1qqWkFI18PcL2YNO9-Agr6OUGg-zAdDq3uj6p6mkgUOmJqHQkMNK5JjzF3qF0XBou_0NgOfTz5tVg68T0P90CBi4SmMw5Ljp8ir5-Jbsq9abo4RCfQG_0kQNGtvTftoxYudaQQXD-BmpxfwSDXXxJJIdoYpPBBmiKFAF8C2wf6451F9i9hR77oF67I7_NjEP2xXiLVkYHuiwtvgZDHjPFKA8LvXXJCVLui-dZvW45SCz9u5Kr1NIR_lFFbp0GsQPDQZNz1PU20oswJlo7aKnH8OpAepP13G9cdy8wXbqn8nhsI4hunRcuTeqMDJsCThWx23D5rwfGIqag",
        refresh_token="hi",
        expires_in=86400,
    )
    return token


@pytest.fixture
def token_expired():
    token = aiosu.models.OAuthToken(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiaWRlbnRpZnkiLCJwdWJsaWMiXX0.eHwSds48D1qqWkFI18PcL2YNO9-Agr6OUGg-zAdDq3uj6p6mkgUOmJqHQkMNK5JjzF3qF0XBou_0NgOfTz5tVg68T0P90CBi4SmMw5Ljp8ir5-Jbsq9abo4RCfQG_0kQNGtvTftoxYudaQQXD-BmpxfwSDXXxJJIdoYpPBBmiKFAF8C2wf6451F9i9hR77oF67I7_NjEP2xXiLVkYHuiwtvgZDHjPFKA8LvXXJCVLui-dZvW45SCz9u5Kr1NIR_lFFbp0GsQPDQZNz1PU20oswJlo7aKnH8OpAepP13G9cdy8wXbqn8nhsI4hunRcuTeqMDJsCThWx23D5rwfGIqag",
        refresh_token="hi",
        expires_in=-86400,
    )
    return token


@pytest.fixture
def user():
    with open(f"tests/data/v2/get_me_200.json", "rb") as f:
        data = f.read()
    return data


class TestEvents:
    @pytest.mark.asyncio
    async def test_cs_add_client(self, mocker, token, user):
        client_storage = aiosu.v2.ClientStorage()

        @client_storage.on_client_add
        async def decorated(event):
            decorated.times_called += 1
            assert isinstance(event.client, aiosu.v2.Client)

        decorated.times_called = 0

        resp = MockResponse(user, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)

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

        resp = MockResponse(user, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)
        resp_token = MockResponse(to_bytes(token.model_dump()), 200)
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

        resp = MockResponse(user, 200)
        mocker.patch("aiohttp.ClientSession.request", return_value=resp)
        resp_token = MockResponse(to_bytes(token.model_dump()), 200)
        mocker.patch("aiohttp.ClientSession.post", return_value=resp_token)

        user = await client.get_me()
        user = await client.get_me()

        assert decorated.times_called == 1
        await client.close()
