"""
This module handles API requests for API v1.

You can read more about it here: https://github.com/ppy/osu-api/wiki
"""
from __future__ import annotations

from io import BytesIO
from io import StringIO
from typing import Literal
from typing import TYPE_CHECKING
from warnings import warn

import aiohttp
import orjson
from aiolimiter import AsyncLimiter

from ..exceptions import APIException
from ..helpers import add_param
from ..helpers import from_list
from ..models import Beatmapset
from ..models import Gamemode
from ..models import Mods
from ..models import Score
from ..models import User
from ..models import UserQueryType
from ..models.legacy import Match
from ..models.legacy import ReplayCompact

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from collections.abc import MutableMapping
    from typing import Optional
    from typing import Union


__all__ = ("Client",)

ClientRequestType = Literal["GET", "POST", "DELETE", "PUT", "PATCH"]


def get_content_type(content_type: str) -> str:
    """Returns the content type."""
    return content_type.split(";")[0]


def _beatmap_score_conv(
    data: MutableMapping[str, object],
    mode: Gamemode,
    beatmap_id: int,
) -> Score:
    data["beatmap_id"] = beatmap_id
    return Score._from_api_v1(data, mode)


class Client:
    r"""osu! API v1 Client

    :param token: The API key
    :type token: str
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *base_url* (``str``) --
            Optional, base API URL, defaults to "https://osu.ppy.sh"
        * *limiter* (``tuple[int, int]``) --
            Optional, rate limit, defaults to (600, 60) (600 requests per minute)
    """

    __slots__ = (
        "token",
        "base_url",
        "_limiter",
        "_session",
    )

    def __init__(self, token: str, **kwargs: Any) -> None:
        self.token: str = token
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
        max_rate, time_period = kwargs.pop("limiter", (600, 60))
        if (max_rate / time_period) > (1000 / 60):
            warn(
                "You are running at an insanely high rate limit. Doing so may result in your account being banned.",
            )
        self._limiter: AsyncLimiter = AsyncLimiter(
            max_rate=max_rate,
            time_period=time_period,
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.aclose()

    async def _request(
        self,
        request_type: ClientRequestType,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self._session is None:
            self._session = aiohttp.ClientSession()

        async with self._limiter:
            async with self._session.request(request_type, *args, **kwargs) as resp:
                body = await resp.read()
                content_type = get_content_type(resp.headers.get("content-type", ""))
                if resp.status != 200:
                    json = {}
                    if content_type == "application/json":
                        json = orjson.loads(body)
                    raise APIException(resp.status, json.get("error", ""))
                if content_type == "application/json":
                    return orjson.loads(body)
                if content_type == "application/octet-stream":
                    return BytesIO(body)
                if content_type == "text/plain":
                    return body.decode()
                raise APIException(415, "Unhandled Content Type")

    async def get_user(self, user_query: Union[str, int], **kwargs: Any) -> User:
        r"""Gets a user by a query.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query
            * *event_days* (``int``) --
                Optional, max number of days since last event, Min: 1, Max: 31, defaults to 1

        :raises ValueError: If event_days is not between 1 and 31
        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: list[aiosu.models.user.User]
        """
        url = f"{self.base_url}/api/get_user"
        if not 1 <= (event_days := kwargs.pop("limit", 1)) <= 31:
            raise ValueError(
                "Invalid event_days specified. Limit must be between 1 and 31",
            )
        params = {
            "k": self.token,
            "u": user_query,
            "event_days": event_days,
            "m": int(Gamemode(kwargs.pop("mode", 0))),
        }
        add_param(
            params,
            kwargs,
            key="qtype",
            param_name="type",
            converter=lambda x: UserQueryType(x).old_api_name,
        )
        json = await self._request("GET", url, params=params)
        if not json:
            raise APIException(404, "User not found")
        return User._from_api_v1(json[0])

    async def __get_type_scores(
        self,
        user_query: Union[str, int],
        request_type: str,
        **kwargs: Any,
    ) -> list[Score]:
        r"""INTERNAL: Get a user's scores by type

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param request_type: "recent" or "best"
        :type request_type: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, defaults to 10
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If request_type is invalid
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        if request_type not in ("recent", "best"):
            raise ValueError(
                'Invalid request_type specified. Valid options are: "best", "recent"',
            )
        url = f"{self.base_url}/api/get_user_{request_type}"
        params = {
            "k": self.token,
            "u": user_query,
            "limit": kwargs.pop("limit", 10),
        }
        mode = Gamemode(kwargs.pop("mode", 0))
        params["m"] = int(mode)
        add_param(
            params,
            kwargs,
            key="qtype",
            param_name="type",
            converter=lambda x: UserQueryType(x).old_api_name,
        )
        json = await self._request("GET", url, params=params)
        score_conv = lambda x: Score._from_api_v1(x, mode)
        return from_list(score_conv, json)

    async def get_user_recents(
        self,
        user_query: Union[str, int],
        **kwargs: Any,
    ) -> list[Score]:
        r"""Get a user's recent scores.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 50, defaults to 50
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        if not 1 <= (limit := kwargs.pop("limit", 50)) <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        return await self.__get_type_scores(user_query, "recent", limit=limit, **kwargs)

    async def get_user_bests(
        self,
        user_query: Union[str, int],
        **kwargs: Any,
    ) -> list[Score]:
        r"""Get a user's best scores.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 100, defaults to 100
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        if not 1 <= (limit := kwargs.pop("limit", 100)) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        return await self.__get_type_scores(user_query, "best", limit=limit, **kwargs)

    async def get_beatmap(self, **kwargs: Any) -> list[Beatmapset]:
        r"""Get beatmap data.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 500, defaults to 500
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *converts* (``bool``) --
                Optional, whether to return converts, defaults to False
            * *mods* (``aiosu.models.mods.Mods``) --
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
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If limit is not between 1 and 500
        :raises ValueError: If none of hash, since, user_query, beatmap_id or beatmapset_id specified.
        :raises APIException: Contains status code and error message
        :return: List of beatmapsets each containing one difficulty of the result
        :rtype: list[aiosu.models.beatmap.Beatmapset]
        """
        if not 1 <= (limit := kwargs.get("limit", 500)) <= 500:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 500")
        url = f"{self.base_url}/api/get_beatmaps"
        params = {
            "k": self.token,
            "limit": limit,
            "a": int(kwargs.pop("converts", False)),
            "m": int(Gamemode(kwargs.pop("mode", 0))),
        }
        added = add_param(params, kwargs, key="mods", converter=lambda x: str(Mods(x)))
        added |= add_param(params, kwargs, key="beatmap_id", param_name="b")
        added |= add_param(params, kwargs, key="beatmapset_id", param_name="s")
        if add_param(params, kwargs, key="user_query", param_name="u"):
            added = True
            add_param(
                params,
                kwargs,
                key="qtype",
                param_name="type",
                converter=lambda x: UserQueryType(x).old_api_name,
            )
        added |= add_param(params, kwargs, key="since", param_name="since")
        added |= add_param(params, kwargs, key="hash", param_name="h")
        if not added:
            raise ValueError(
                "Either hash, since, user_query, beatmap_id or beatmapset_id must be specified.",
            )
        json = await self._request("GET", url, params=params)
        return from_list(Beatmapset._from_api_v1, json)

    async def get_beatmap_scores(self, beatmap_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's best scores.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *mods* (``aiosu.models.mods.Mods``) --
                Optional, mods to search for
            * *limit* (``int``) --
                Optional, number of scores to get, Min: 1, Max: 100, defaults to 100
            * *user_query* (``Union[str, int]``) --
                Optional, username or ID to search by
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        url = f"{self.base_url}/api/get_scores"
        params = {
            "k": self.token,
            "b": beatmap_id,
            "limit": kwargs.pop("limit", 50),
        }
        mode = Gamemode(kwargs.pop("mode", 0))
        params["m"] = int(mode)
        if add_param(params, kwargs, key="user_query", param_name="u"):
            add_param(
                params,
                kwargs,
                key="qtype",
                param_name="type",
                converter=lambda x: UserQueryType(x).old_api_name,
            )
        add_param(params, kwargs, key="mods", converter=lambda x: str(Mods(x)))
        json = await self._request("GET", url, params=params)
        score_conv = lambda x: _beatmap_score_conv(x, mode, beatmap_id)
        return from_list(score_conv, json)

    async def get_match(self, match_id: int) -> Match:
        r"""Gets a multiplayer match. (WIP, currently returns raw JSON)

        :param match_id: The ID of the match
        :type match_id: int
        :raises APIException: Contains status code and error message
        :return: The requested multiplayer match
        :rtype: aiosu.models.legacy.match.Match
        """
        url = f"{self.base_url}/api/get_match"
        params = {
            "k": self.token,
            "mp": match_id,
        }
        json = await self._request("GET", url, params=params)
        return Match.model_validate(json)

    async def get_replay(self, **kwargs: Any) -> ReplayCompact:
        r"""Gets data for a replay.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for, defaults to standard
            * *mods* (``aiosu.models.mods.Mods``) --
                Optional, mods to search for
            * *score_id* (``int``) --
                Optional, the ID of the score
            * *beatmap_id* (``int``) --
                Optional, the ID of the beatmap, specified together with user_query
            * *user_query* (``Union[str, int]``) --
                Optional, username or ID to search by, specified together with beatmap_id
            * *qtype* (``aiosu.models.user.UserQueryType``) --
                Optional, "string" or "id". Type of the user_query

        :raises ValueError: If neither score_id nor beatmap_id + user_id specified
        :raises APIException: Contains status code and error message
        :return: The data for the requested replay
        :rtype: aiosu.models.legacy.replay.Replay
        """
        url = f"{self.base_url}/api/get_replay"
        params = {
            "k": self.token,
            "m": int(Gamemode(kwargs.pop("mode", 0))),
        }
        added = add_param(params, kwargs, key="score_id", param_name="s")
        if add_param(params, kwargs, key="beatmap_id", param_name="b") and add_param(
            params,
            kwargs,
            key="user_query",
            param_name="u",
        ):
            added = True
            add_param(
                params,
                kwargs,
                key="qtype",
                param_name="type",
                converter=lambda x: UserQueryType(x).old_api_name,
            )
        if not added:
            raise ValueError(
                "Either score_id or beatmap_id + user_id must be specified.",
            )
        add_param(params, kwargs, key="mods", converter=lambda x: str(Mods(x)))
        json = await self._request("GET", url, params=params)
        return ReplayCompact.model_validate(json)

    async def get_beatmap_osu(self, beatmap_id: int) -> StringIO:
        r"""Returns the Buffer of the beatmap file requested.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int

        :return: File-like object of .osu data downloaded from the server.
        :rtype: io.StringIO
        """
        url = f"{self.base_url}/osu/{beatmap_id}"
        data = await self._request("GET", url)
        return StringIO(data)

    async def aclose(self) -> None:
        """Closes the client session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def close(self) -> None:
        """Closes the client session. (Deprecated)"""
        warn(
            "close is deprecated, use aclose instead. Will be removed on 2024-03-01",
            DeprecationWarning,
        )
        await self.aclose()
