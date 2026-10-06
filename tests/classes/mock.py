from __future__ import annotations

from io import BytesIO

import orjson
import pytest
from pysignalr.messages import CompletionMessage

from aiosu.exceptions import APIException
from aiosu.models import OAuthToken


@pytest.fixture
def api_token():
    token = OAuthToken(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiY2hhdC5yZWFkIiwiY2hhdC53cml0ZSIsImNoYXQud3JpdGVfbWFuYWdlIiwiZm9ydW0ud3JpdGUiLCJmcmllbmRzLnJlYWQiLCJpZGVudGlmeSIsInB1YmxpYyJdfQ.S_JhNdYLm0PdDpPj42xumaNyKARZUxDOesLwNPTLBrQ",
        refresh_token="hi",
        expires_in=86400,
    )
    return token


@pytest.fixture
def friends_token():
    token = OAuthToken(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiZnJpZW5kcy5yZWFkIiwiaWRlbnRpZnkiLCJwdWJsaWMiXX0.dps4hJ4HwjQ7scacQRBHs1FN0tcGPfYPCUxQjt6ueEo4Q-G-BmkJSGQo6dDhXD1WnXFJdW14prl_fzjvBi7U-9Y7AcLHSMRSbmRa2uS7KciZv7vHpS6Cs64uZO1WqBpOswZJtCfjBeimSrvU9O_zezg3cujrhNTCwbsBOaK1mR9YtxXhw4Y6ORLKqS9ahF1FyXBIZ3pSFBFOxbAtIIDwtZq9CDbffqQrVL7MiNojPBVmhReomf2pSyNM0UIA5u7pCXQOsb4VvmhSPGj7HPoORNyc6CM1iwcmGsrEPDL3d1ZtNtYyiLtarvUZx1WUau9GDAs-AtJ9XaypJTqUjfya7g",
        refresh_token="hi",
        expires_in=86400,
    )
    return token


@pytest.fixture
def user_data():
    with open("tests/data/v2/get_me_200.json", "rb") as f:
        data = f.read()
    return data


@pytest.fixture
def auth_token_data():
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiaWRlbnRpZnkiLCJwdWJsaWMiXX0.eHwSds48D1qqWkFI18PcL2YNO9-Agr6OUGg-zAdDq3uj6p6mkgUOmJqHQkMNK5JjzF3qF0XBou_0NgOfTz5tVg68T0P90CBi4SmMw5Ljp8ir5-Jbsq9abo4RCfQG_0kQNGtvTftoxYudaQQXD-BmpxfwSDXXxJJIdoYpPBBmiKFAF8C2wf6451F9i9hR77oF67I7_NjEP2xXiLVkYHuiwtvgZDHjPFKA8LvXXJCVLui-dZvW45SCz9u5Kr1NIR_lFFbp0GsQPDQZNz1PU20oswJlo7aKnH8OpAepP13G9cdy8wXbqn8nhsI4hunRcuTeqMDJsCThWx23D5rwfGIqag",
        "expires_in": 86400,
        "refresh_token": "anotherlongstring",
        "token_type": "Bearer",
    }


@pytest.fixture
def credentials_token_data():
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkIiwiaWF0IjoxNjc3MTA0NjU3LjU2NjUyNCwibmJmIjoxNjc3MTA0NjU3LjU2NjUyNSwiZXhwIjoxNjc3MTkxMDU3LjU1OTc1Nywic3ViIjoiIiwic2NvcGVzIjpbInB1YmxpYyJdfQ.ApjKrJg_k8PmMVYt1Fkj3_w0G2Mds7oXQMitRpEmTGER5I4hX16mwHwhiAryWXzDH0MnPTRzZDB8AE_mjN25AjK4I-B7dB0eWe6-7pOI3eYmxlFVIKtXseNkpAtEKA1vo2xsr06ngwUBxxrro2tE3W8CJNz7sQD_mt6fabh1V2OlTb-X8Dm6o732dknMm5S4yCTAsT_YeO1_4ovyTWkGkCxfJGD2MtPnFiX1ieFOBtPAaQafkrz2ncadzcGJpsKiwVBQAJGu4nkVffYxXa6jZ7ud1whBZfvpCmuzQjNEagqUUHFmjJYRdD92DcFjVe-e-3uwK2bDAJ2rKOYasvZyZg",
        "expires_in": 86400,
        "token_type": "Bearer",
    }


@pytest.fixture
def replay_file(mode="osu"):
    def _replay_file(mode=mode):
        with open(f"tests/data/replay_{mode}.osr", "rb") as f:
            data = f.read()
        return data

    return _replay_file


@pytest.fixture
def accuracy_scores():
    def _scores(mode="osu"):
        with open(f"tests/data/v2/score_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _scores


@pytest.fixture
def difficulty_attributes():
    def _difficulty_attributes(mode="osu"):
        with open(f"tests/data/v2/difficulty_attributes_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _difficulty_attributes


@pytest.fixture
def performance_scores():
    def _scores(mode="osu"):
        with open(f"tests/data/v2/score_performance_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        if isinstance(data, dict):
            with open("tests/data/v2/beatmap_performance_315.json", "rb") as f:
                beatmap = orjson.loads(f.read())
            score_list = data["scores"]
            for score in score_list:
                assert score["beatmap_id"] == beatmap["id"] == 315
                score["beatmap"] = beatmap
            return score_list
        return data

    return _scores


@pytest.fixture
def lazer_beatmap_state():
    with open("tests/data/lazer/beatmap_state.json", "rb") as f:
        return f.read()


@pytest.fixture
def lazer_user_activity():
    with open("tests/data/lazer/user_activity.json", "rb") as f:
        return f.read()


@pytest.fixture
def identify_token(auth_token_data):
    return OAuthToken.model_validate(auth_token_data)


@pytest.fixture
def expired_identify_token(auth_token_data):
    data = auth_token_data.copy()
    data["expires_in"] = -86400
    return OAuthToken.model_validate(data)


def mock_referee_response(data: bytes, error: bool = False):
    async def mocked_send(method, arguments, on_invocation):
        payload = orjson.loads(data)
        message = CompletionMessage(invocation_id=None, result=payload)
        if error:
            message = CompletionMessage(invocation_id=None, error=payload["error"])
        await on_invocation(message)

    return mocked_send


class MockResponse:
    def __init__(self, text, status, content_type="application/json"):
        self._text = text
        self.status = status
        self.headers = {"content-type": content_type}

    async def text(self):
        return self._text.decode("utf-8")

    async def json(self):
        return orjson.loads(self._text)

    async def read(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        return self

    async def __aenter__(self):
        return self


def mock_request(status_code: int, content_type: str, data: bytes):
    def mocked_request(*args, **kwargs):
        if status_code == 204:
            return

        if status_code != 200:
            json = {}
            if content_type == "application/json":
                json = orjson.loads(data)
            raise APIException(status_code, json.get("error", ""))
        if content_type == "application/json":
            return orjson.loads(data)
        if content_type == "application/octet-stream":
            return BytesIO(data)
        if content_type == "application/x-osu":
            return BytesIO(data)
        if content_type == "text/plain":
            return data.decode()

    return mocked_request
