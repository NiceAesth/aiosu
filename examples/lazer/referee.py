from __future__ import annotations

import asyncio

import aiosu


async def main() -> None:
    token = aiosu.models.OAuthToken(
        access_token="access token",
    )
    client = aiosu.lazer.RefereeClient(token=token)

    @client.on_user_joined
    async def on_user_joined(event: aiosu.models.RefereeUserJoinedEvent) -> None:
        print(event.room_id, event.user_id)

    @client.on_match_completed
    async def on_match_completed(
        event: aiosu.models.RefereeMatchCompletedEvent,
    ) -> None:
        print(event.room_id, event.playlist_item_id)

    async with client:
        rooms = await client.list_rooms()
        for room_id in rooms.room_ids:
            room = await client.join_room(room_id)
            print(room.name, room.chat_channel_id)
        await client.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
