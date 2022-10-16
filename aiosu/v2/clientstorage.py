from __future__ import annotations

from . import Client
from ..classes import OAuthToken


class ClientStorage:
    def __init__(self, **kwargs):
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.client_id: int = kwargs.pop("client_id", None)
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api/v2")
        self.clients = {}

    def _get_client_args(self) -> Dict:
        return {
            "client_secret": self.client_secret,
            "client_id": self.client_id,
            "base_url": self.base_url,
        }

    def client_exists(self, client_uid: int) -> bool:
        return client_uid in self.clients

    async def add_client(self, token: OAuthToken) -> Client:
        client = Client(token=token, **self._get_client_args())
        client_user = await client.get_me()
        self.clients[client_user.id] = client
        return client

    async def get_client(self, **kwargs) -> Client:
        client_uid: int = kwargs.pop("id", None)
        token: OAuthToken = kwargs.pop("token", None)
        if self.client_exists(client_uid):
            return self.clients[client_uid]
        if token is not None:
            return await self.add_client(token)
        raise ValueError("Either id or token must be specified.")
