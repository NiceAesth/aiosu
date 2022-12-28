from __future__ import annotations

import orjson


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
