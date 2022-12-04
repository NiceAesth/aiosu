"""
This module handles API requests for API v1.

You can read more about it here: https://github.com/ppy/osu-api/wiki
"""
from __future__ import annotations

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
from ..classes import Beatmapset
from ..classes import Gamemode
from ..classes import Mods
from ..classes import Score
from ..classes import User
from ..classes import UserQueryType
from ..classes.legacy import Match
from ..classes.legacy import Replay


def rate_limited(func: Callable) -> Callable:
    """
    A decorator that enforces rate limiting, to be used as:
    @rate_limited
    """

    @functools.wraps(func)
    async def _rate_limited(*args: Any, **kwargs: Any) -> Any:
        self = args[0]
        async with self._limiter:
            return await func(*args, **kwargs)

    return _rate_limited


class Client:
    r"""osu! API v1 Client

    :param token: The API key
    :type token: str
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *base_url* (``str``) --
            Optional, base API URL, defaults to \"https://osu.ppy.sh/api\"
        * *limiter* (``aiolimiter.AsyncLimiter``) --
            Optional, custom AsyncLimiter, defaults to AsyncLimiter(1200, 60)
    """

    def __init__(self, token: str, **kwargs: Any) -> None:
        self.token: str = token
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh/api")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @rate_limited
    async def get_user(self, user_query: Union[str, int], **kwargs: Any) -> list[User]:
        r"""Gets a user by a query.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query
            * *event_days* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, max number of days since last event, Min: 1, Max: 31, defaults to 1

        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: list[aiosu.classes.user.User]
        """
        url = f"{self.base_url}/get_user"
        params = {
            "k": self.token,
            "u": user_query,
            "event_days": kwargs.pop("event_days", 1),
        }
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
            params["type"] = qtype.old_api_name
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(User._from_api_v1, json)

    @rate_limited
    async def __get_type_scores(
        self, user_query: Union[str, int], request_type: str, **kwargs: Any
    ) -> list[Score]:
        r"""INTERNAL: Get a user's scores by type

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param request_type: "recent" or "best"
        :type request_type: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, defaults to 10
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If request_type is invalid
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        if request_type not in ("recent", "best"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        url = f"{self.base_url}/get_user_{request_type}"
        params = {
            "k": self.token,
            "u": user_query,
            "limit": kwargs.pop("limit", 10),
        }
        mode = Gamemode(kwargs.pop("mode", 0))  # type: ignore
        params["m"] = int(mode)
        if "qtype" in kwargs:
            qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
            params["type"] = qtype.old_api_name
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            score_conv = lambda x: Score._from_api_v1(x, mode)
            return helpers.from_list(score_conv, json)

    async def get_user_recents(
        self, user_query: Union[str, int], **kwargs: Any
    ) -> list[Score]:
        r"""Get a user's recent scores.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 50, defaults to 50
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        if not 1 <= kwargs.get("limit", 50) <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        return await self.__get_type_scores(user_query, "recent", **kwargs)

    async def get_user_bests(
        self, user_query: Union[str, int], **kwargs: Any
    ) -> list[Score]:
        r"""Get a user's best scores.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 100, defaults to 100
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        return await self.__get_type_scores(user_query, "best", **kwargs)

    @rate_limited
    async def get_beatmap(self, **kwargs: Any) -> list[Beatmapset]:
        r"""Get beatmap data.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 500, defaults to 500
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *converts* (``bool``) --
                Optional, whether to return converts, defaults to False
            * *mods* (``aiosu.classes.mods.Mods``) --
                Optional, mods to apply to the result
            * *beatmap_id* (``int``) --
                Optional, The ID of the beatmap
            * *beatmapset_id* (``int``) --
                Optional, The ID of the beatmapset
            * *since* (``datetime.datetime``) --
                Optional, Return all beatmaps with a leaderboard since this date
            * *hash* (``str``) --
                Optional, The MD5 hash of the beatmap
            * *user_query* (``Union[str, int]``) --
                Optional, username or ID to search by
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If limit is not between 1 and 500
        :raises ValueError: If none of hash, since, user_query, beatmap_id or beatmapset_id specified.
        :raises APIException: Contains status code and error message
        :return: List of beatmapsets each containing one difficulty of the result
        :rtype: list[aiosu.classes.beatmap.Beatmapset]
        """
        if not 1 <= kwargs.get("limit", 500) <= 500:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 500")
        url = f"{self.base_url}/get_beatmaps"
        params = {
            "k": self.token,
            "limit": kwargs.pop("limit", 500),
            "a": int(kwargs.pop("converts", False)),
        }
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        if "beatmap_id" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
        elif "beatmapset_id" in kwargs:
            params["s"] = kwargs.pop("beatmapset_id")
        elif "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        elif "since" in kwargs:
            params["since"] = kwargs.pop("since")
        elif "hash" in kwargs:
            params["h"] = kwargs.pop("hash")
        else:
            raise ValueError(
                "Either hash, since, user_query, beatmap_id or beatmapset_id must be specified.",
            )
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return helpers.from_list(Beatmapset._from_api_v1, json)

    @rate_limited
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's best scores.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *mods* (``aiosu.classes.mods.Mods``) --
                Optional, mods to search for
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 100, defaults to 100
            * *user_query* (``Union[str, int]``) --
                Optional, username or ID to search by
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.classes.score.Score]
        """
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        url = f"{self.base_url}/get_scores"
        params = {
            "k": self.token,
            "b": beatmap_id,
            "limit": kwargs.pop("limit", 50),
        }
        mode = Gamemode(kwargs.pop("mode", 0))  # type: ignore
        params["m"] = int(mode)
        if "user_query" in kwargs:
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            score_conv = lambda x: Score._from_api_v1(x, mode)
            return helpers.from_list(score_conv, json)

    @rate_limited
    async def get_match(self, match_id: int) -> Match:
        r"""Gets a multiplayer match. (WIP, currently returns raw JSON)

        :param match_id: The ID of the match
        :type match_id: int
        :raises APIException: Contains status code and error message
        :return: The requested multiplayer match
        :rtype: aiosu.classes.legacy.match.Match
        """
        url = f"{self.base_url}/get_match"
        params = {
            "k": self.token,
            "mp": match_id,
        }
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Match.parse_obj(json)

    @rate_limited
    async def get_replay(self, **kwargs: Any) -> Replay:
        r"""Gets data for a replay.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.classes.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *mods* (``aiosu.classes.mods.Mods``) --
                Optional, mods to search for
            * *score_id* (``int``) --
                Optional, the ID of the score
            * *beatmap_id* (``int``) --
                Optional, the ID of the beatmap, specified together with user_query
            * *user_query* (``Union[str, int]``) --
                Optional, username or ID to search by, specified together with beatmap_id
            * *qtype* (``str``) --
                Optional, \"string\" or \"id\". Type of the user_query

        :raises ValueError: If neither score_id nor beatmap_id + user_id specified
        :raises APIException: Contains status code and error message
        :return: The data for the requested replay
        :rtype: aiosu.classes.legacy.replay.Replay
        """
        url = f"{self.base_url}/get_replay"
        params = {"k": self.token}
        params["m"] = int(Gamemode(kwargs.pop("mode", 0)))  # type: ignore
        if "score_id" in kwargs:
            params["s"] = kwargs.pop("score_id")
        elif "beatmap_id" in kwargs and "user_query" in kwargs:
            params["b"] = kwargs.pop("beatmap_id")
            params["u"] = kwargs.pop("user_query")
            if "qtype" in kwargs:
                qtype = UserQueryType(kwargs.pop("qtype"))  # type: ignore
                params["type"] = qtype.old_api_name
        else:
            raise ValueError(
                "Either score_id or beatmap_id + user_id must be specified.",
            )
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            params["mode"] = str(mods)
        async with self._session.get(url, params=params) as resp:
            json = await resp.json()
            if resp.status != 200:
                raise APIException(resp.status, json.get("error", ""))
            return Replay.parse_obj(json)

    async def close(self) -> None:
        """Closes the client session."""
        await self._session.close()
