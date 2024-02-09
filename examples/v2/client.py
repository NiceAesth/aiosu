from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timedelta

import aiosu


async def main():
    token = aiosu.models.OAuthToken(
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
    await client.aclose()

    # client credentials example
    app_client = aiosu.v2.Client(
        client_secret="secret",
        client_id=1000,
    )
    # if you pass a token without a refresh token, it will be treated as a client credentials token

    # ratelimiter example
    limit = (10, 1)  # 10 requests per second
    app_client = aiosu.v2.Client(
        client_secret="secret",
        client_id=1000,
        limiter=limit,
    )


if __name__ == "__main__":
    asyncio.run(main())
