from __future__ import annotations

import asyncio

import aiosu


async def main():
    client = aiosu.v2.Client()

    discussions = await client.get_beatmapset_discussions(beatmapset_id=1786386)

    discussions_next = await discussions.next()

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
