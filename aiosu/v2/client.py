"""
This module handles API requests for API v2 (OAuth).

You can read more about it here: https://osu.ppy.sh/docs/index.html
"""
from __future__ import annotations

from datetime import datetime
import functools
from io import BytesIO
from typing import TYPE_CHECKING

import aiohttp
import orjson
from aiolimiter import AsyncLimiter

from .. import helpers
from ..classes import APIException
from ..classes import Beatmap
from ..classes import BeatmapDifficultyAttributes
from ..classes import Beatmapset
from ..classes import Gamemode
from ..classes import Mods
from ..classes import OAuthToken
from ..classes import Scopes
from ..classes import Score
from ..classes import SeasonalBackgroundSet
from ..classes import User
from ..classes import UserQueryType
from ..classes.events import ClientUpdateEvent
from ..classes.events import Eventable

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import Type
    from typing import Union
    from typing import Literal


def check_token(func: Callable) -> Callable:
    """
    A decorator that checks the current token, to be used as:
    @check_token
    """

    @functools.wraps(func)
    async def _check_token(self: Client, *args: Any, **kwargs: Any) -> Any:
        if datetime.utcnow() > self.token.expires_on:
            await self._refresh()
        return await func(self, *args, **kwargs)

    return _check_token


def requires_scope(required_scopes: Scopes, any_scope: bool = False) -> Callable:
    """
    A decorator that enforces a scope, to be used as:
    @requires_scope(Scopes.PUBLIC)
    """

    def _requires_scope(func: Callable) -> Callable:
        @functools.wraps(func)
        async def _wrap(self: Client, *args: Any, **kwargs: Any) -> Any:
            if any_scope:
                if not (required_scopes & self.token.scopes):
                    raise APIException(403, "Missing required scopes.")
            elif required_scopes & self.token.scopes != required_scopes:
                raise APIException(403, "Missing required scopes.")

            return await func(self, *args, **kwargs)

        return _wrap

    return _requires_scope


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
        self._register_event(ClientUpdateEvent)
        self.client_id: int = kwargs.pop("client_id", None)
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.token: OAuthToken = kwargs.pop("token", OAuthToken())
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
        self._limiter: AsyncLimiter = kwargs.pop("limiter", AsyncLimiter(1200, 60))
        self._session: aiohttp.ClientSession = None  # type: ignore

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
        self._register_listener(func, ClientUpdateEvent)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return _on_client_update

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _refresh_guest_data(self) -> dict[str, Union[str, int]]:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "public",
        }

    def _refresh_auth_data(self) -> dict[str, Union[str, int]]:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.token.refresh_token,
        }

    async def _request(
        self, request_type: Literal["GET", "POST", "DELETE"], *args: Any, **kwargs: Any
    ) -> Any:
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers=self._get_headers(),
            )

        req: dict[str, Callable] = {
            "GET": self._session.get,
            "POST": self._session.post,
            "DELETE": self._session.delete,
        }

        async with self._limiter:
            async with req[request_type](*args, **kwargs) as resp:
                body = await resp.read()
                content_type = resp.headers.get("content-type", "")
                if resp.status != 200:
                    json = orjson.loads(body)
                    raise APIException(resp.status, json.get("error", ""))
                if content_type == "application/json":
                    return orjson.loads(body)
                if content_type == "application/octet-stream":
                    return BytesIO(body)

    async def _refresh(self) -> None:
        """INTERNAL: Refreshes the client's token

        :raises APIException: Contains status code and error message
        """
        old_token = self.token
        url = f"{self.base_url}/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {}
        if self.token.can_refresh:
            data = self._refresh_auth_data()
        else:
            data = self._refresh_guest_data()

        async with aiohttp.ClientSession(headers=headers) as temp_session:
            async with temp_session.post(url, data=data) as resp:
                try:
                    body = await resp.read()
                    json = orjson.loads(body)
                    if resp.status != 200:
                        raise APIException(resp.status, json.get("error", ""))
                    if self._session:
                        await self._session.close()
                    self.token = OAuthToken.parse_obj(json)
                    self._session = aiohttp.ClientSession(headers=self._get_headers())
                except aiohttp.client_exceptions.ContentTypeError:
                    raise APIException(403, "Invalid token specified.")

        await self._process_event(
            ClientUpdateEvent(client=self, old_token=old_token, new_token=self.token),
        )

    async def get_seasonal_backgrounds(self) -> SeasonalBackgroundSet:
        r"""Gets the current seasonal background set.

        :raises APIException: Contains status code and error message
        :return: Seasonal background set object
        :rtype: aiosu.classes.backgrounds.SeasonalBackgroundSet
        """
        url = f"{self.base_url}/api/v2/seasonal-backgrounds"
        json = await self._request("GET", url)
        return SeasonalBackgroundSet.parse_obj(json)

    @check_token
    @requires_scope(Scopes.IDENTIFY)
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
        json = await self._request("GET", url)
        return User.parse_obj(json)

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
        json = await self._request("GET", url, params=params)
        return User.parse_obj(json)

    @check_token
    async def get_users(self, user_ids: list[int]) -> list[User]:
        r"""Get multiple user data.

        :param user_ids: The IDs of the users
        :type user_ids: list[int]
        :raises APIException: Contains status code and error message
        :return: List of user data objects
        :rtype: list[aiosu.classes.user.User]
        """
        url = f"{self.base_url}/api/v2/users"
        params = {
            "ids": user_ids,
        }
        json = await self._request("GET", url, params=params)
        return helpers.from_list(User.parse_obj, json.get("users", []))

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
        json = await self._request("GET", url, params=params)
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
        json = await self._request("GET", url, params=params)
        return helpers.from_list(Score.parse_obj, json.get("scores", []))

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
        json = await self._request("GET", url, params=params)
        return helpers.from_list(Score.parse_obj, json.get("scores", []))

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
        json = await self._request("GET", url)
        return Beatmap.parse_obj(json)

    @check_token
    async def get_beatmaps(self, beatmap_ids: list[int]) -> list[Beatmap]:
        r"""Get multiple beatmap data.

        :param beatmap_ids: The IDs of the beatmaps
        :type beatmap_ids: list[int]
        :raises APIException: Contains status code and error message
        :return: List of beatmap data objects
        :rtype: list[aiosu.classes.beatmap.Beatmap]
        """
        url = f"{self.base_url}/api/v2/beatmaps"
        params = {
            "ids": beatmap_ids,
        }
        json = await self._request("GET", url, params=params)
        return helpers.from_list(Beatmap.parse_obj, json.get("beatmaps", []))

    @check_token
    async def lookup_beatmap(self, **kwargs: Any) -> Beatmap:
        r"""Lookup beatmap data.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *checksum* (``str``) --
                Optional, the MD5 checksum of the beatmap
            * *filename* (``str``) --
                Optional, the filename of the beatmap
            * *id* (``int``) --
                Optional, the ID of the beatmap

        :raises ValueError: If no arguments are specified
        :raises APIException: Contains status code and error message
        :return: Beatmap data object
        :rtype: aiosu.classes.beatmap.Beatmap
        """
        url = f"{self.base_url}/api/v2/beatmaps/lookup"
        params = {}
        if "checksum" in kwargs:
            params["checksum"] = kwargs.pop("checksum")
        if "filename" in kwargs:
            params["filename"] = kwargs.pop("filename")
        if "id" in kwargs:
            params["id"] = kwargs.pop("id")
        if not params:
            raise ValueError("One of checksum, filename or id must be provided.")
        json = await self._request("GET", url, params=params)
        return Beatmap.parse_obj(json)

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
        data: dict[str, Any] = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            data["ruleset_id"] = int(mode)
        if "mods" in kwargs:
            mods = Mods(kwargs.pop("mods"))
            data["mods"] = str(mods)
        json = await self._request("POST", url, data=data)
        return BeatmapDifficultyAttributes.parse_obj(json.get("attributes"))

    @check_token
    async def get_beatmapset(self, beatmapset_id: int) -> Beatmapset:
        r"""Get beatmapset data.

        :param beatmapset_id: The ID of the beatmapset
        :type beatmapset_id: int
        :raises APIException: Contains status code and error message
        :return: Beatmapset data object
        :rtype: aiosu.classes.beatmap.Beatmapset
        """
        url = f"{self.base_url}/api/v2/beatmapsets/{beatmapset_id}"
        json = await self._request("GET", url)
        return Beatmapset.parse_obj(json)

    @check_token
    async def lookup_beatmapset(self, beatmap_id: int) -> Beatmapset:
        r"""Lookup beatmap data.

        :param beatmap_id: The ID of a beatmap in the set
        :type beatmap_id: int

        :raises APIException: Contains status code and error message
        :return: Beatmapset data object
        :rtype: aiosu.classes.beatmap.Beatmapset
        """
        url = f"{self.base_url}/api/v2/beatmapsets/lookup"
        params = {
            "beatmap_id": beatmap_id,
        }
        json = await self._request("GET", url, params=params)
        return Beatmapset.parse_obj(json)

    @check_token
    async def search_beatmapsets(
        self,
        search_filter: Optional[str] = "",
    ) -> list[Beatmapset]:
        r"""Search beatmapset by filter.

        :param search_filter: The search filter.
        :type search_filter: str

        :raises APIException: Contains status code and error message
        :return: List of beatmapset data objects
        :rtype: list[aiosu.classes.beatmap.Beatmapset]
        """
        url = f"{self.base_url}/api/v2/beatmapsets/search/{search_filter}"
        json = await self._request("GET", url)
        return helpers.from_list(Beatmapset.parse_obj, json.get("beatmapsets", []))

    @check_token
    async def get_score(
        self,
        score_id: int,
        mode: Gamemode,
    ) -> Score:
        r"""Gets data about a score.

        :param score_id: The ID of the score
        :type score_id: int
        :param mode: The gamemode to search for
        :type mode: aiosu.classes.gamemode.Gamemode

        :raises APIException: Contains status code and error message
        :return: Score data object
        :rtype: aiosu.classes.score.Score
        """
        url = f"{self.base_url}/api/v2/scores/{mode}/{score_id}"
        json = await self._request("GET", url)
        return Score.parse_obj(json)

    @check_token
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_score_replay(
        self,
        score_id: int,
        mode: Gamemode,
    ) -> BytesIO:
        r"""Gets the replay file for a score.

        :param score_id: The ID of the score
        :type score_id: int
        :param mode: The gamemode to search for
        :type mode: aiosu.classes.gamemode.Gamemode

        :raises APIException: Contains status code and error message
        :return: Replay file
        :rtype: io.BytesIO
        """
        url = f"{self.base_url}/api/v2/scores/{mode}/{score_id}/download"
        return await self._request("GET", url)

    @check_token
    async def revoke_token(self) -> None:
        """Revokes the current token and closes the session.

        :raises APIException: Contains status code and error message
        """
        url = f"{self.base_url}/api/v2/oauth/tokens/current"
        await self._request("DELETE", url)
        await self.close()

    async def close(self) -> None:
        """Closes the client session."""
        if self._session:
            await self._session.close()
