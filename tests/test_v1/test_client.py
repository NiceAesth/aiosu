from __future__ import annotations

import orjson
import pytest

import aiosu
from ..classes import MockResponse

modes = ["osu", "mania", "fruits", "taiko"]


@pytest.fixture
def user():
    def _user(mode="osu"):
        with open(f"tests/data/v1/single_user_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        f.close()
        return data

    return _user


@pytest.fixture
def scores():
    def _scores(mode="osu", type="recents"):
        with open(f"tests/data/v1/multiple_score_{mode}_{type}.json", "rb") as f:
            data = orjson.loads(f.read())
        f.close()
        return data

    return _scores


@pytest.fixture
def beatmap():
    def _beatmap(mode="osu"):
        with open(f"tests/data/v1/multiple_beatmap_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        f.close()
        return data

    return _beatmap


@pytest.fixture
def match():
    with open(f"tests/data/v1/match.json", "rb") as f:
        data = orjson.loads(f.read())
    f.close()
    return data


@pytest.fixture
def replay():
    with open(f"tests/data/v1/replay.json", "rb") as f:
        data = orjson.loads(f.read())
    f.close()
    return data


class TestClient:
    @pytest.mark.asyncio
    async def test_get_user(self, mocker, user):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user(7782553, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.User) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_user_recents(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "recents"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_recents(1473890, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_user_recents_missing(self, mocker):
        client = aiosu.v1.Client("")
        resp = MockResponse([], 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_recents(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )

    @pytest.mark.asyncio
    async def test_get_user_bests(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "bests"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_bests(7782553, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_user_bests_missing(self, mocker):
        client = aiosu.v1.Client("")
        resp = MockResponse([], 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_bests(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )

    @pytest.mark.asyncio
    async def test_get_beatmap(self, mocker, beatmap):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap(user_query=7118575, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Beatmapset) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "beatmap"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap_scores(
                2354779,
                user_query=7782553,
                mode=mode,
            )
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores_missing(self, mocker):
        client = aiosu.v1.Client("")
        resp = MockResponse([], 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393, user_query=7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )

    @pytest.mark.asyncio
    async def test_get_beatmap_scores(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "beatmap"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap_scores(2354779, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.classes.Score) for x in data
            )

    @pytest.mark.asyncio
    async def test_get_beatmap_scores_missing(self, mocker):
        client = aiosu.v1.Client("")
        resp = MockResponse([], 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.classes.Score) for x in data
        )

    @pytest.mark.asyncio
    async def test_get_match(self, mocker, match):
        client = aiosu.v1.Client("")
        resp = MockResponse(match, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_match(105019274)
        assert isinstance(data, aiosu.classes.legacy.Match)

    @pytest.mark.asyncio
    async def test_get_replay(self, mocker, replay):
        client = aiosu.v1.Client("")
        resp = MockResponse(replay, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_replay(beatmap_id=2271666, user_query=9703390)
        assert isinstance(data, aiosu.classes.legacy.Replay)
