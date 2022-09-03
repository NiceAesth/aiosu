from __future__ import annotations

import asyncio

from aiosu import v1


async def main():
    token = ""
    async with v1.Client(token) as client:
        user = await client.get_user(7782553)
    print(user)


async def main_simple():
    token = ""
    client = v1.Client(token)
    user = await client.get_user(7782553)
    print(user)


asyncio.run(main())
asyncio.run(main_simple())
