from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timedelta

import orjson

import aiosu
from aiosu.v2.repository import BaseTokenRepository


# This is an example of a custom repository. It uses a file to store tokens. You can check BaseTokenRepository to see what methods you need to implement.
class ExampleFileRepository(BaseTokenRepository):
    def __init__(self):
        self._file_path = "tokens.json"

    async def _read_file(self):
        try:
            with open(self._file_path, "rb") as f:
                return orjson.loads(f.read())
        except FileNotFoundError:
            return {}

    async def _write_file(self, data):
        with open(self._file_path, "wb") as f:
            f.write(orjson.dumps(data))

    async def exists(self, session_id: int) -> bool:
        """Check if a token exists."""
        tokens = await self._read_file()
        return session_id in tokens

    async def add(
        self,
        session_id: int,
        token: aiosu.models.OAuthToken,
    ) -> aiosu.models.OAuthToken:
        """Add a token."""
        tokens = await self._read_file()
        tokens[session_id] = token.dict()
        await self._write_file(tokens)
        return token

    async def get(self, session_id: int) -> aiosu.models.OAuthToken:
        """Get a token."""
        tokens = await self._read_file()
        return aiosu.models.OAuthToken.from_dict(tokens[session_id])


async def main():
    token = aiosu.models.OAuthToken(
        access_token="access token",
        refresh_token="refresh token",
        expires_on=datetime.utcnow() + timedelta(days=1),  # can also be string
    )

    file_repo = ExampleFileRepository()
    # async with syntax
    async with aiosu.v2.ClientStorage(
        repository=file_repo,
        client_secret="secret",
        client_id=1000,
    ) as cs:
        client_1 = await cs.add_client(token=token)
        user = await client.get_me()

        client_2 = await cs.get_client(id=user.id)

    # regular syntax
    cs = aiosu.v2.ClientStorage(
        repository=file_repo,
        client_secret="secret",
        client_id=1000,
    )
    client = await cs.add_client(token=token)
    user = await client.get_me()
    await cs.close()


if __name__ == "__main__":
    asyncio.run(main())
