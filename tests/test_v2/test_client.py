from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from io import BytesIO

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
    token = aiosu.models.OAuthToken(
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


@pytest.fixture
def users():
    with open("tests/data/v2/multiple_user.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def score():
    def _score(mode="osu"):
        with open(f"tests/data/v2/single_score_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _score


@pytest.fixture
def scores():
    def _scores(mode="osu", type="recents"):
        with open(f"tests/data/v2/multiple_score_{mode}_{type}.json", "rb") as f:
            data = f.read()
        return data

    return _scores


@pytest.fixture
def beatmap():
    def _beatmap(mode="osu"):
        with open(f"tests/data/v2/single_beatmap_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _beatmap


@pytest.fixture
def beatmaps():
    with open("tests/data/v2/multiple_beatmap.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def beatmapset():
    def _beatmapset(mode="osu"):
        with open(f"tests/data/v2/single_beatmapset_{mode}.json", "rb") as f:
            data = f.read()
        return data

    return _beatmapset


@pytest.fixture
def beatmapsets():
    with open("tests/data/v2/multiple_beatmapset.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def replay():
    def _replay(mode="osu"):
        with open(f"tests/data/replay_{mode}.osr", "rb") as f:
            data = f.read()
        return data

    return _replay


@pytest.fixture
def seasonal_bgs():
    with open("tests/data/v2/seasonal_backgrounds.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def changelog():
    with open("tests/data/v2/single_changelog.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def spotlights():
    with open("tests/data/v2/multiple_spotlight.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def news_post():
    with open("tests/data/v2/single_news_post.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def difficulty_attributes():
    def _difficulty_attributes(mode="osu"):
        with open(f"tests/data/v2/difficulty_attributes_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _difficulty_attributes


class TestClient:
    @pytest.mark.asyncio
    async def test_get_seasonal_backgrounds(self, mocker, token, seasonal_bgs):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(seasonal_bgs, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_seasonal_backgrounds()
        assert isinstance(data, aiosu.models.SeasonalBackgroundSet)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_changelog_build(self, mocker, token, changelog):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(changelog, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_changelog_build("lazer", "2022.1228.0")
        assert isinstance(data, aiosu.models.Build)
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_changelog_build(self, mocker, token, changelog):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(changelog, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.lookup_changelog_build("lazer")
        assert isinstance(data, aiosu.models.Build)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_news_post(self, mocker, token, news_post):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(news_post, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_news_post(1)
        assert isinstance(data, aiosu.models.NewsPost)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_me(self, mocker, token, user):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_me()
            assert isinstance(data, aiosu.models.User)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user(self, mocker, token, user):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(user(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user(7782553)
            assert isinstance(data, aiosu.models.User)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_users(self, mocker, token, users):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(users, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_users([7782553, 15118934])
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.User) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents(self, mocker, token, scores):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(scores(mode, "recents"), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_user_recents(7782553)
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_recents_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_recents(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
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
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_bests_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_bests(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
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
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_firsts_missing(self, mocker, token, empty):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_firsts(7782553)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
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
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_beatmap_scores_missing(self, mocker, token, empty_score):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty_score, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_user_beatmap_scores(7782553, 2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
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
                isinstance(x, aiosu.models.Score) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap_scores_missing(self, mocker, token, empty_score):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(empty_score, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_beatmap_scores(2095393)
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Score) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmap(self, mocker, token, beatmap):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmap(2354779)
            assert isinstance(data, aiosu.models.Beatmap)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmaps(self, mocker, token, beatmaps):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmaps, 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmaps([2095393, 2354779])
            assert isinstance(data, list) and all(
                isinstance(x, aiosu.models.Beatmap) for x in data
            )
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_beatmap(self, mocker, token, beatmap):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmap(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.lookup_beatmap(id=2354779)
            assert isinstance(data, aiosu.models.Beatmap)
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
            assert isinstance(data, aiosu.models.BeatmapDifficultyAttributes)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_beatmapset(self, mocker, token, beatmapset):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmapset(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_beatmapset(2354779)
            assert isinstance(data, aiosu.models.Beatmapset)
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_beatmapset(self, mocker, token, beatmapset):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(beatmapset(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.lookup_beatmapset(2354779)
            assert isinstance(data, aiosu.models.Beatmapset)
        await client.close()

    @pytest.mark.asyncio
    async def test_search_beatmaps(self, mocker, token, beatmapsets):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(beatmapsets, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.search_beatmapsets()
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Beatmapset) for x in data
        )
        await client.close()

    @pytest.mark.asyncio
    async def test_get_score(
        self,
        mocker,
        token,
        score,
    ):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(score(mode), 200)
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_score(4220635589, mode)
            assert isinstance(data, aiosu.models.Score)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_score_replay(
        self,
        mocker,
        token,
        replay,
    ):
        client = aiosu.v2.Client(token=token)
        for mode in modes:
            resp = MockResponse(replay(mode), 200, "application/octet-stream")
            mocker.patch("aiohttp.ClientSession.get", return_value=resp)
            data = await client.get_score_replay(4220635589, mode)
            assert isinstance(data, BytesIO)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_spotlights(self, mocker, token, spotlights):
        client = aiosu.v2.Client(token=token)
        resp = MockResponse(spotlights, 200)
        mocker.patch("aiohttp.ClientSession.get", return_value=resp)
        data = await client.get_spotlights()
        assert isinstance(data, list) and all(
            isinstance(x, aiosu.models.Spotlight) for x in data
        )
        await client.close()
