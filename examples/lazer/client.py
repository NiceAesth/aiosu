from __future__ import annotations

import asyncio

import aiosu


async def main() -> None:
    client = aiosu.lazer.Client()

    @client.on_raw_message
    async def on_raw_message(data: str) -> None:
        print(data)

    @client.on_beatmap_state
    async def on_beatmap_state(
        event: aiosu.models.BeatmapStateWebSocketMessage,
    ) -> None:
        print(event.beatmap.metadata.title, event.mods)

    @client.on_user_activity
    async def on_user_activity(
        event: aiosu.models.UserActivityWebSocketMessage,
    ) -> None:
        print(event.status, event.data)

    async with client:
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
