from __future__ import annotations

import asyncio
import datetime

import aiosu


async def main():
    token = aiosu.classes.OAuthToken(
        access_token="access token",
        refresh_token="refresh token",
        expires_on=datetime.datetime.utcnow()
        + datetime.timedelta(days=1),  # can also be string
    )

    # async with syntax
    async with aiosu.v2.ClientStorage(client_secret="secret", client_id=1000) as cs:
        client_1 = await cs.add_client(token=token)
        user = await client.get_me()

        client_2 = await cs.get_client(id=user.id)

    # regular syntax
    cs = aiosu.v2.ClientStorage(client_secret="secret", client_id=1000)
    client = await cs.add_client(token=token)
    user = await client.get_me()
    cs.close()


if __name__ == "__main__":
    asyncio.run(main())
