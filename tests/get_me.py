from __future__ import annotations

import asyncio

from aiosu import v2


async def main():
    async with v2.Client() as client:
        user = await client.get_me()


asyncio.run(main())
