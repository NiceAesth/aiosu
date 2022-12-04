"""
This module handles API requests for API v2 (OAuth).

You can read more about it here: https://osu.ppy.sh/docs/index.html
"""
from __future__ import annotations

import datetime
import functools
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import Union

import aiohttp
from aiolimiter import AsyncLimiter

from .. import helpers
from ..classes import APIException
from ..classes import Beatmap
from ..classes import BeatmapDifficultyAttributes
from ..classes import Gamemode
from ..classes import Mods
from ..classes import OAuthToken
from ..classes import Score
from ..classes import User
from ..classes import UserQueryType
from ..classes.events import BaseEvent
from ..classes.events import ClientUpdateEvent
from ..classes.events import Eventable


def check_token(func: Callable) -> Callable:
    """
    A decorator that checks the current token, to be used as:
    @check_token
    """

    @functools.wraps(func)
    async def _check_token(self: Client, *args: Any, **kwargs: Any) -> Any:
        if datetime.datetime.now() > self.token.expires_on:
            await self._refresh()
        return await func(self, *args, **kwargs)

    return _check_token


def rate_limited(func: Callable) -> Callable:
    """
    A decorator that enforces rate limiting, to be used as:
    @rate_limited
    """

    @functools.wraps(func)
    async def _rate_limited(self: Client, *args: Any, **kwargs: Any) -> Any:
        async with self._limiter:
            return await func(self, *args, **kwargs)

    return _rate_limited


class Client(Eventable):
    r"""osu! API v2 Client

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *client_id* (``int``)
        * *client_secret* (``str``)
        * *base_url* (``str``) --
            Optional, base API URL, defaults to \"https://osu.ppy.sh\"
        * *token* (``aiosu.classes.token.OAuthToken``)
        * *limiter* (``aiolimiter.AsyncLimiter``) --
            Optional, custom AsyncLimiter, defaults to AsyncLimiter(1200, 60)
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.client_id: int = kwargs.pop("client_id", None)
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.token: OAuthToken = kwargs.pop("token", OAuthToken())
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self._session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=self.__get_headers(),
        )

    def __get_headers(self):
        return {
            "Authorization": f"Bearer {self.token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    def on_client_update(self, func: Callable) -> Callable:
        """
        A decorator that is called whenever a client is updated, to be used as:

            @client.on_client_update

            async def func(event: ClientUpdateEvent)
        """
        self._listeners.append(func)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_update

    async def _process_event(self, event: BaseEvent) -> None:
        if isinstance(event, ClientUpdateEvent):
            for func in event.client._listeners:
                await func(event)
            return
        raise NotImplementedError(f"{event!r}")

    @rate_limited
    async def _refresh(self) -> None:
        """INTERNAL: Refreshes the client's token

        :raises APIException: Contains status code and error message
        """
        old_token = self.token
        url = f"{self.base_url}/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": old_token.refresh_token,
        }

        async with aiohttp.ClientSession(headers=headers) as temp_session:
            async with temp_session.post(url, data=data) as resp:
                try:
                    json = await resp.json()
                    if resp.status != 200:
                        raise APIException(resp.status, json.get("error", ""))
                    self.token = OAuthToken.parse_obj(json)
                    await self._session.close()
                    self._session = aiohttp.ClientSession(headers=self.__get_headers())
                except aiohttp.client_exceptions.ContentTypeError:
                    raise APIException(403, "Invalid token specified.")

        await self._process_event(
            ClientUpdateEvent(client=self, old_token=old_token, new_token=self.token),
        )

    @rate_limited
    @check_token
    async def get_me(self, **kwargs: Any) -> User:
        r"""Gets the user who owns the current token

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for

        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: aiosu.classes.user.User
        """
        url = f"{self.base_url}/api/v2/me"
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            url += f"/{mode}"
        async with self._session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    @rate_limited
    @check_token
    async def get_user(self, user_query: Union[str, int], **kwargs: Any) -> User:
        r"""Gets a user by a query.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: aiosu.classes.user.User
        """
        url = f"{self.base_url}/api/v2/users/{user_query}"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            url += f"/{mode}"
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
            params["type"] = qtype.new_api_name
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return User.parse_obj(json)

    @rate_limited
    @check_token
    async def __get_type_scores(
        self, user_id: int, request_type: str, **kwargs: Any
    ) -> list[Score]:
        r"""INTERNAL: Get a user's scores by type

        :param user_id: User ID to search by
        :type user_id: int
        :param request_type: "recent", "best" or "firsts"
        :type request_type: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises ValueError: If limit is not between 1 and 100
        :raises ValueError: If type is invalid
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if request_type not in ("recent", "best", "firsts"):
            raise ValueError(
                f'"{request_type}" is not a valid request_type. Valid options are: "recent", "best", "firsts"',
            )
        url = f"{self.base_url}/api/v2/users/{user_id}/scores/{request_type}"
        params = {
            "include_fails": kwargs.pop("include_fails", False),
            "offset": kwargs.pop("offset", 0),
            "limit": kwargs.pop("limit", 100),
        }
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            params["mode"] = str(mode)
        if "limit" in kwargs:
            params["limit"] = kwargs.pop("limit")
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json)

    async def get_user_recents(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's recent scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        return await self.__get_type_scores(user_id, "recent", **kwargs)

    async def get_user_bests(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's top scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        return await self.__get_type_scores(user_id, "best", **kwargs)

    async def get_user_firsts(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's first place scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        return await self.__get_type_scores(user_id, "firsts", **kwargs)

    @rate_limited
    @check_token
    async def get_user_beatmap_scores(
        self, user_id: int, beatmap_id: int, **kwargs: Any
    ) -> list[Score]:
        r"""Get a user's scores on a specific beatmap.

        :param user_id: User ID to search by
        :type user_id: int
        :param beatmap_id: Beatmap ID to search by
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/scores/users/{user_id}/all"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            params["mode"] = str(mode)
        async with self._session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json.get("scores", []))

    @rate_limited
    @check_token
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs: Any) -> list[Score]:
        r"""Get scores submitted on a specific beatmap.

        :param beatmap_id: Beatmap ID to search by
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *mods* (``aiosu.classes.mods.Mods``) --
                Optional, mods to search for
            * *type* (``str``) --
                Optional, beatmap score ranking type

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/scores"
        params = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            params["mode"] = str(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        if "type" in kwargs:
            params["type"] = kwargs.pop("type")
        async with self._session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Score.parse_obj, json.get("scores", []))

    @rate_limited
    @check_token
    async def get_beatmap(self, beatmap_id: int) -> Beatmap:
        r"""Get beatmap data.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int
        :raises APIException: Contains status code and error message
        :return: Beatmap data object
        :rtype: aiosu.classes.beatmap.Beatmap
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}"
        async with self._session.get(url) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Beatmap.parse_obj(json)

    @rate_limited
    @check_token
    async def get_beatmap_attributes(
        self, beatmap_id: int, **kwargs: Any
    ) -> BeatmapDifficultyAttributes:
        r"""Gets difficulty attributes for a beatmap.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *mods* (``aiosu.classes.mods.Mods``) --
                Optional, mods to apply to the result

        :raises APIException: Contains status code and error message
        :return: Difficulty attributes for a beatmap
        :rtype: aiosu.classes.beatmap.BeatmapDifficultyAttributes
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/attributes"
        params: dict[str, Any] = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            params["ruleset_id"] = int(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mods"] = str(mods)
        async with self._session.post(url, data=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return BeatmapDifficultyAttributes.parse_obj(json.get("attributes"))

    async def close(self) -> None:
        """Closes the client session."""
        await self._session.close()
