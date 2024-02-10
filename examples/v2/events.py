from __future__ import annotations

import aiosu

client = aiosu.v2.Client()


@client.on_client_update
async def on_client_update(event: aiosu.events.ClientUpdateEvent):
    """Called when client token is refreshed"""
    print(f"Updated {event.client} {event.old_token} {event.new_token}")


client_storage = aiosu.v2.ClientStorage()


@client_storage.on_client_add
async def on_client_add(event: aiosu.events.ClientAddEvent):
    """Called when client is added via client_storage.add_client() or client_storage.get_client()"""
    print(f"{event.session_id} {event.client}")


@client_storage.on_client_update
async def on_client_update(event: aiosu.events.ClientUpdateEvent):
    """Called when any client token is refreshed"""
    print(f"Updated {event.client} {event.old_token} {event.new_token}")
