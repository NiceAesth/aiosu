Client lazer
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
