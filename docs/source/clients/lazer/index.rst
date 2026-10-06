Lazer client
============

`aiosu` provides a client that can be used to receive websocket events from osu!lazer.

API Example
-----------

.. code:: py

    import aiosu
    import asyncio


    async def main():
        client = aiosu.lazer.Client()

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

        @client.on_raw_message
        async def on_raw_message(data: str) -> None:
            print(data)

        async with client:
            await asyncio.Event().wait()


    if __name__ == "__main__":
        asyncio.run(main())

Connecting
----------

To connect without using ``async with``, do the following:

.. code:: py

    import aiosu
    import asyncio


    async def main():
        client = aiosu.lazer.Client(base_url="ws://localhost:49727/")

        @client.on_raw_message
        async def on_raw_message(data: str) -> None:
            print(data)

        try:
            await client.connect()
            await asyncio.Event().wait()
        finally:
            await client.aclose()


    if __name__ == "__main__":
        asyncio.run(main())

More examples can be found in the `repository <https://github.com/NiceAesth/aiosu/tree/master/examples/lazer>`__

Client
------

.. automodule:: aiosu.lazer.client
    :members:
    :undoc-members:

Referee API
-----------

`aiosu` provides a client that can be used to manage multiplayer rooms in osu!lazer.

The access token must have the ``multiplayer.write_manage`` scope. Tokens obtained
using the client credentials grant must also have the ``delegate`` scope.
See the `referee API documentation <https://ppy.sh/osu-server-spectator/>`__.

.. code:: py

    import aiosu
    import asyncio


    async def main(token: aiosu.models.OAuthToken):
        client = aiosu.lazer.RefereeClient(token=token)

        @client.on_user_joined
        async def on_user_joined(event: aiosu.models.RefereeUserJoinedEvent) -> None:
            print(event.room_id, event.user_id)

        async with client:
            room = await client.make_room(
                aiosu.models.RefereeMakeRoomRequest(
                    name="Tournament",
                    beatmap_id=974423,
                    ruleset_id=0,
                    max_participants=2,
                ),
            )
            print(room.room_id, room.chat_channel_id)
            await client.wait_closed()

Referee Client
--------------

.. automodule:: aiosu.lazer.referee
    :members:
    :undoc-members:
