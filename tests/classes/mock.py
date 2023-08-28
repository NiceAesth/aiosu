from __future__ import annotations

from io import BytesIO

import orjson

from aiosu.exceptions import APIException


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
