from __future__ import annotations

import asyncio

import aiosu


async def main():
    # async with syntax
    async with aiosu.v1.Client("osu api token") as client:
        user = await client.get_user(7782553)

    # regular syntax
    client = aiosu.v1.Client("osu api token")
    user = await client.get_user(7782553)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
