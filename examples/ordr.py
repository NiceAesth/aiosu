from __future__ import annotations

import asyncio

import aiosu


async def main():
    client = aiosu.utils.ordr.ordrClient(verification_key="verylongstring")

    await client.create_render(
        "username",
        "- YUGEN -",
        replay_url="https://url.to.replay",
    )

    @client.on_render_added
    async def on_render_added(data: dict) -> None:
        print(data)

    @client.on_render_progress
    async def on_render_progress(data: dict) -> None:
        print(data)

    @client.on_render_fail
    async def on_render_fail(data: dict) -> None:
        print(data)

    @client.on_render_finish
    async def on_render_finish(data: dict) -> None:
        print(data)


if __name__ == "__main__":
    asyncio.run(main())
