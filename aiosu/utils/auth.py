"""
This module contains authorization functions.
"""
from __future__ import annotations

import aiohttp
import orjson

from ..exceptions import APIException
from ..models.token import OAuthToken


async def process_code(
    client_id: int,
    client_secret: str,
    redirect_uri: str,
    code: str,
    base_url: str = "https://osu.ppy.sh",
) -> OAuthToken:
    r"""Creates an OAuth Token from an authorization code.

    :param client_id: The ID of the client
    :type client_id: int
    :param client_secret: The client secret
    :type client_secret: str
    :param redirect_uri: The URL to redirect to
    :type redirect_uri: str
    :param code: Code returned from the API
    :type code: str
    :param base_url: The base URL of the API, defaults to "https://osu.ppy.sh"
    :type base_url: Optional[str]
    :return: The OAuth token
    :rtype: aiosu.models.token.OAuthToken
    """
    url = f"{base_url}/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with aiohttp.ClientSession(headers=headers) as temp_session:
        async with temp_session.post(url, data=data) as resp:
            try:
                body = await resp.read()
                json = orjson.loads(body)
                if resp.status != 200:
                    raise APIException(resp.status, json.get("error", ""))
                return OAuthToken.parse_obj(json)
            except aiohttp.client_exceptions.ContentTypeError:
                raise APIException(403, "Invalid code specified.")
