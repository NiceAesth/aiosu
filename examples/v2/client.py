from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import aiosu


async def main():
    token = aiosu.classes.OAuthToken(
        access_token="access token",
        refresh_token="refresh token",
        expires_on=datetime.utcnow() + timedelta(days=1),  # can also be string
    )

    # async with syntax
    async with aiosu.v2.Client(
        client_secret="secret",
        client_id=1000,
        token=token,
    ) as client:
        user = await client.get_me()

    # regular syntax
    client = aiosu.v2.Client(client_secret="secret", client_id=1000, token=token)
    user = await client.get_me()
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
