from __future__ import annotations

from io import StringIO

import pytest

import aiosu
from ..classes import MockResponse

modes = ["osu", "mania", "fruits", "taiko"]


@pytest.fixture
def empty():
    return b"[]"


@pytest.fixture
def user():
    def _user(mode="osu"):
        with open(f"tests/data/v1/single_user_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _user


@pytest.fixture
def scores():
    def _scores(mode="osu", score_type="recents"):
        with open(f"tests/data/v1/multiple_score_{mode}_{score_type}.json", "rb") as f:
            data = f.read()
        return data

    return _scores


@pytest.fixture
def beatmap():
    def _beatmap(mode="osu"):
        with open(f"tests/data/v1/multiple_beatmap_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _beatmap


@pytest.fixture
def match():
    with open("tests/data/v1/match.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def replay():
    with open("tests/data/v1/replay.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def beatmap_osu():
    with open("tests/data/beatmap.osu", "rb") as f:
        data = f.read()
    return data


class TestClient:
    @pytest.mark.asyncio
    async def test_get_user(self, mocker, user):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user(7782553, mode=mode)
            assert isinstance(data, aiosu.models.User)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "recents"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_recents(1473890, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents_missing(self, mocker, empty):
        client = aiosu.v1.Client("")
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_recents(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_bests(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "bests"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_bests(7782553, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_bests_missing(self, mocker, empty):
        client = aiosu.v1.Client("")
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_bests(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap(self, mocker, beatmap):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap(user_query=7118575, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Beatmapset) for x in data
            )
        await client.close()

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
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores_missing(self, mocker, empty):
        client = aiosu.v1.Client("")
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393, user_query=7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_scores(self, mocker, scores):
        client = aiosu.v1.Client("")
        for mode in modes:
            resp = MockResponse(scores(mode, "beatmap"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap_scores(2354779, mode=mode)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_scores_missing(self, mocker, empty):
        client = aiosu.v1.Client("")
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_match(self, mocker, match):
        client = aiosu.v1.Client("")
        resp = MockResponse(match, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_match(105019274)
        assert isinstance(data, aiosu.models.legacy.Match)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_replay(self, mocker, replay):
        client = aiosu.v1.Client("")
        resp = MockResponse(replay, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_replay(beatmap_id=2271666, user_query=9703390)
        assert isinstance(data, aiosu.models.legacy.ReplayCompact)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_osu(self, mocker, beatmap_osu):
        client = aiosu.v1.Client("")
        resp = MockResponse(beatmap_osu, 200, "text/plain")
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_osu(413428)
        assert isinstance(data, StringIO)
        await client.close()
