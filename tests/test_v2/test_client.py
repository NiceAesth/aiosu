from __future__ import annotations

import datetime

import orjson
import pytest

import aiosu
from ..classes import MockResponse

modes = ["osu", "mania", "fruits", "taiko"]


def to_bytes(obj):
    return orjson.dumps(obj)


@pytest.fixture
def empty():
    return b"[]"


@pytest.fixture
def empty_score():
    return b'{"scores": []}'


@pytest.fixture
def token():
    token = aiosu.classes.OAuthToken(
        refresh_token="hi",
        expires_on=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    return token


@pytest.fixture
def user():
    def _user(mode="osu"):
        with open(f"tests/data/v2/single_user_{mode}.json", "rb") as f:
            data = f.read()
        f.close()
        return data

    return _user


@pytest.fixture
def scores():
    def _scores(mode="osu", type="recents"):
        with open(f"tests/data/v2/multiple_score_{mode}_{type}.json", "rb") as f:
            data = f.read()
        f.close()
        return data

    return _scores


@pytest.fixture
def beatmap():
    def _beatmap(mode="osu"):
        with open(f"tests/data/v2/single_beatmap_{mode}.json", "rb") as f:
            data = f.read()
        f.close()
        return data

    return _beatmap


@pytest.fixture
def difficulty_attributes():
    def _difficulty_attributes(mode="osu"):
        with open(f"tests/data/v2/difficulty_attributes_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        f.close()
        return data

    return _difficulty_attributes


class TestClient:
    @pytest.mark.asyncio
    async def test_get_me(self, mocker, token, user):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_me()
            assert isinstance(data, aiosu.classes.User)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user(self, mocker, token, user):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user(7782553)
            assert isinstance(data, aiosu.classes.User)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "recents"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_recents(7782553)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_recents(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_bests(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "bests"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_bests(7782553)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_bests_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_bests(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_firsts(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "firsts"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_firsts(7782553)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_firsts_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_firsts(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "beatmap"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_beatmap_scores(7782553, 2354779)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores_missing(self, mocker, token, empty_score):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty_score, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_beatmap_scores(7782553, 2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_scores(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "beatmap"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap_scores(2354779)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_scores_missing(self, mocker, token, empty_score):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty_score, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap(self, mocker, token, beatmap):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap(2354779)
            assert isinstance(data, aiosu.classes.Beatmap)
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_beatmap(self, mocker, token, beatmap):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.lookup_beatmap(id=2354779)
            assert isinstance(data, aiosu.classes.Beatmap)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_attributes(
        self,
        mocker,
        token,
        beatmap,
        difficulty_attributes,
    ):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            diffatrib = difficulty_attributes(mode)["2354779"]
            resp = MockResponse(to_bytes(diffatrib), 200)
            mocker.patch("aiohttp.ClientSession.post", return_value=resp)
            data = await client.get_beatmap_attributes("2354779")
            assert isinstance(data, aiosu.classes.BeatmapDifficultyAttributes)
        await client.close()
