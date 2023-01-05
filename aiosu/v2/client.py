"""
This module handles API requests for API v2 (OAuth).

You can read more about it here: https://osu.ppy.sh/docs/index.html
"""
from __future__ import annotations

import functools
from datetime import datetime
from functools import partial
from io import BytesIO
from typing import Literal
from typing import TYPE_CHECKING

import aiohttp
import orjson
from aiolimiter import AsyncLimiter

from ..events import ClientUpdateEvent
from ..events import Eventable
from ..exceptions import APIException
from ..helpers import add_param
from ..helpers import from_list
from ..models import Beatmap
from ..models import BeatmapDifficultyAttributes
from ..models import Beatmapset
from ..models import BeatmapsetDiscussionPostResponse
from ..models import BeatmapsetDiscussionResponse
from ..models import BeatmapsetDiscussionVoteResponse
from ..models import BeatmapsetEvent
from ..models import BeatmapUserPlaycount
from ..models import Build
from ..models import CommentBundle
from ..models import Event
from ..models import Gamemode
from ..models import KudosuHistory
from ..models import Mods
from ..models import NewsPost
from ..models import OAuthToken
from ..models import Scopes
from ..models import Score
from ..models import SearchResponse
from ..models import SeasonalBackgroundSet
from ..models import Spotlight
from ..models import User
from ..models import UserQueryType
from ..models import WikiPage

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import Type
    from typing import Union

__all__ = ("Client",)


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
        * *client_id* (``int``) --
            Optional, required for client credentials
        * *client_secret* (``str``) --
            Optional, required for client credentials
        * *base_url* (``str``) --
            Optional, base API URL, defaults to "https://osu.ppy.sh"
        * *scopes* (``aiosu.models.Scopes``) --
            Optional, defaults to ``Scopes.PUBLIC | Scopes.IDENTIFY``
        * *token* (``aiosu.models.oauthtoken.OAuthToken``) --
            Optional, defaults to client credentials if not provided
        * *limiter* (``tuple[int, int]``) --
            Optional, rate limit, defaults to (600, 60) (600 requests per minute)
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self._register_event(ClientUpdateEvent)
        self.client_id: int = kwargs.pop("client_id", None)
        self.client_secret: str = kwargs.pop("client_secret", None)
        self.scopes: Scopes = kwargs.pop("scopes", Scopes.PUBLIC | Scopes.IDENTIFY)
        self.token: OAuthToken = kwargs.pop("token", OAuthToken(scopes=self.scopes))
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
        self._limiter: AsyncLimiter = AsyncLimiter(
            *kwargs.pop(
                "limiter",
                (600, 60),
            )
        )
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
            "scope": str(self.scopes),
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
                if content_type == "text/plain":
                    return body.decode()
                raise APIException(415, "Unhandled Content Type")

    async def _refresh(self) -> None:
        r"""INTERNAL: Refreshes the client's token

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
            async with self._limiter:
                async with temp_session.post(url, data=data) as resp:
                    try:
                        body = await resp.read()
                        json = orjson.loads(body)
                        if resp.status != 200:
                            raise APIException(resp.status, json.get("error", ""))
                        if self._session:
                            await self._session.close()
                        self.token = OAuthToken.parse_obj(json)
                        self.token.scopes = self.scopes
                        self._session = aiohttp.ClientSession(
                            headers=self._get_headers(),
                        )
                    except aiohttp.client_exceptions.ContentTypeError:
                        raise APIException(403, "Invalid token specified.")

        await self._process_event(
            ClientUpdateEvent(client=self, old_token=old_token, new_token=self.token),
        )

    async def get_seasonal_backgrounds(self) -> SeasonalBackgroundSet:
        r"""Gets the current seasonal background set.

        :raises APIException: Contains status code and error message
        :return: Seasonal background set object
        :rtype: aiosu.models.backgrounds.SeasonalBackgroundSet
        """
        url = f"{self.base_url}/api/v2/seasonal-backgrounds"
        json = await self._request("GET", url)
        return SeasonalBackgroundSet.parse_obj(json)

    async def get_changelog_build(self, stream: str, build: str) -> Build:
        r"""Gets a specific build from the changelog.

        :param stream: The stream to get the build from
        :param build: The build to get
        :raises APIException: Contains status code and error message
        :return: Build object
        :rtype: aiosu.models.changelog.Build
        """
        url = f"{self.base_url}/api/v2/changelog/{stream}/{build}"
        json = await self._request("GET", url)
        return Build.parse_obj(json)

    async def lookup_changelog_build(
        self, changelog_query: Union[str, int], **kwargs: Any
    ) -> Build:
        r"""Looks up a build from the changelog.

        :param changelog_query: The query to search for
        :type changelog_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *is_id* (``bool``) --
                Optional, whether the query is an ID or not, defaults to ``True`` if the query is an int
            * *message_formats* (``list[Literal["html", "markdown"]]``) --
                Optional, message formats to get, defaults to ``["html", "markdown"]``

        :raises APIException: Contains status code and error message
        :return: Build object
        :rtype: aiosu.models.changelog.Build
        """
        url = f"{self.base_url}/api/v2/changelog/{changelog_query}"
        params: dict[str, Any] = {
            "message_formats": kwargs.pop("message_formats", ["html", "markdown"]),
        }
        if "is_id" in kwargs or isinstance(changelog_query, int):
            params["key"] = "id"
        json = await self._request("GET", url, params=params)
        return Build.parse_obj(json)

    async def get_news_post(
        self, news_query: Union[str, int], **kwargs: Any
    ) -> NewsPost:
        r"""Gets a news post.

        :param news_query: The query to search for
        :type news_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *is_id* (``bool``) --
                Optional, whether the query is an ID or not, defaults to ``True`` if the query is an int

        :raises APIException: Contains status code and error message
        :return: News post object
        :rtype: aiosu.models.news.NewsPost
        """
        url = f"{self.base_url}/api/v2/news/{news_query}"
        params: dict[str, Any] = {
            "message_formats": kwargs.pop("message_formats", ["html", "markdown"]),
        }
        if "is_id" in kwargs or isinstance(news_query, int):
            params["key"] = "id"
        json = await self._request("GET", url, params=params)
        return NewsPost.parse_obj(json)

    async def get_wiki_page(self, locale: str, path: str) -> WikiPage:
        r"""Gets a wiki page.

        :param locale: The locale of the wiki page
        :type locale: str
        :param path: The path of the wiki page
        :type path: str
        :raises APIException: Contains status code and error message
        :return: Wiki page object
        :rtype: aiosu.models.wiki.WikiPage
        """
        url = f"{self.base_url}/api/v2/wiki/{locale}/{path}"
        json = await self._request("GET", url)
        return WikiPage.parse_obj(json)

    async def get_comment(self, comment_id: int) -> CommentBundle:
        r"""Gets a comment.

        :param comment_id: The ID of the comment
        :type comment_id: int
        :raises APIException: Contains status code and error message
        :return: Comment bundle object
        :rtype: aiosu.models.comment.CommentBundle
        """
        url = f"{self.base_url}/api/v2/comments/{comment_id}"
        json = await self._request("GET", url)
        return CommentBundle.parse_obj(json)

    @check_token
    async def search(self, query: str, **kwargs: Any) -> SearchResponse:
        r"""Searches for a user, beatmap, beatmapset, or wiki page.

        :param query: The query to search for
        :type query: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``Literal["all", "user", "wiki_page"]``) --
                Optional, gamemode to search for, defaults to ``all``
            * *page* (``int``) --
                Optional, page to get, ignored if mode is ``all``

        :raises APIException: Contains status code and error message
        :return: Search response object
        :rtype: aiosu.models.search.SearchResponse
        """
        url = f"{self.base_url}/api/v2/search"
        params: dict[str, Any] = {
            "query": query,
            "mode": kwargs.pop("mode", "all"),
        }
        add_param(params, kwargs, key="page")
        json = await self._request("GET", url, params=params)
        return SearchResponse.parse_obj(json)

    @check_token
    @requires_scope(Scopes.IDENTIFY)
    async def get_me(self, **kwargs: Any) -> User:
        r"""Gets the user who owns the current token

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for

        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: aiosu.models.user.User
        """
        url = f"{self.base_url}/api/v2/me"
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            url += f"/{mode}"
        json = await self._request("GET", url)
        return User.parse_obj(json)

    @check_token
    @requires_scope(Scopes.FRIENDS_READ)
    async def get_own_friends(self) -> list[User]:
        r"""Gets the token owner's friend list

        :raises APIException: Contains status code and error message
        :return: List of friends
        :rtype: list[aiosu.models.user.User]
        """
        url = f"{self.base_url}/api/v2/friends"
        json = await self._request("GET", url)
        return from_list(User.parse_obj, json)

    @check_token
    async def get_user(self, user_query: Union[str, int], **kwargs: Any) -> User:
        r"""Gets a user by a query.

        :param user_query: Username or ID to search by
        :type user_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *qtype* (``str``) --
                Optional, "string" or "id". Type of the user_query

        :raises APIException: Contains status code and error message
        :return: Requested user
        :rtype: aiosu.models.user.User
        """
        url = f"{self.base_url}/api/v2/users/{user_query}"
        params: dict[str, Any] = {}
        if "mode" in kwargs:
            mode = Gamemode(kwargs.pop("mode"))  # type: ignore
            url += f"/{mode}"
        add_param(
            params,
            kwargs,
            key="qtype",
            param_name="type",
            converter=lambda x: UserQueryType(x).new_api_name,  # type: ignore
        )
        json = await self._request("GET", url, params=params)
        return User.parse_obj(json)

    @check_token
    async def get_users(self, user_ids: list[int]) -> list[User]:
        r"""Get multiple user data.

        :param user_ids: The IDs of the users
        :type user_ids: list[int]
        :raises APIException: Contains status code and error message
        :return: List of user data objects
        :rtype: list[aiosu.models.user.User]
        """
        url = f"{self.base_url}/api/v2/users"
        params: dict[str, Any] = {
            "ids": user_ids,
        }
        json = await self._request("GET", url, params=params)
        return from_list(User.parse_obj, json.get("users", []))

    @check_token
    async def get_user_kudosu(self, user_id: int, **kwargs: Any) -> list[KudosuHistory]:
        r"""Get a user's kudosu history.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of scores to get
            * *offset* (``int``) --
                Optional, offset of the first score to get

        :raises APIException: Contains status code and error message
        :return: List of kudosu history objects
        :rtype: list[aiosu.models.kudosu.KudosuHistory]
        """
        url = f"{self.base_url}/api/v2/users/{user_id}/kudosu"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="offset")
        json = await self._request("GET", url, params=params)
        return from_list(KudosuHistory.parse_obj, json)

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
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``

        :raises ValueError: If limit is not between 1 and 100
        :raises ValueError: If type is invalid
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        if not 1 <= kwargs.get("limit", 100) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if request_type not in ("recent", "best", "firsts"):
            raise ValueError(
                f'"{request_type}" is not a valid request_type. Valid options are: "recent", "best", "firsts"',
            )
        url = f"{self.base_url}/api/v2/users/{user_id}/scores/{request_type}"
        params: dict[str, Any] = {
            "include_fails": kwargs.pop("include_fails", False),
            "limit": kwargs.pop("limit", 100),
            "offset": kwargs.pop("offset", 0),
        }
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))  # type: ignore
        json = await self._request("GET", url, params=params)
        return from_list(Score.parse_obj, json)

    async def get_user_recents(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's recent scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        return await self.__get_type_scores(user_id, "recent", **kwargs)

    async def get_user_bests(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's top scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        return await self.__get_type_scores(user_id, "best", **kwargs)

    async def get_user_firsts(self, user_id: int, **kwargs: Any) -> list[Score]:
        r"""Get a user's first place scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *include_fails* (``bool``) --
                Optional, whether to include failed scores, defaults to ``False``
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
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
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/scores/users/{user_id}/all"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))  # type: ignore
        json = await self._request("GET", url, params=params)
        return from_list(Score.parse_obj, json.get("scores", []))

    UserBeatmapType = Literal["favourite", "graveyard", "loved", "ranked", "pending"]

    @check_token
    async def get_user_beatmaps(
        self, user_id: int, type: UserBeatmapType, **kwargs: Any
    ) -> list[Beatmapset]:
        r"""Get a user's beatmaps.

        :param user_id: ID of the user
        :type user_id: int
        :param type: Type of beatmaps to get
        :type type: UserBeatmapType
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of beatmaps to get
            * *offset* (``int``) --
                Optional, offset of the first beatmap to get

        :raises APIException: Contains status code and error message
        :return: List of requested beatmaps
        :rtype: list[aiosu.models.beatmap.Beatmap]
        """
        url = f"{self.base_url}/api/v2/users/{user_id}/beatmapsets/{type}"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="offset")
        json = await self._request("GET", url, params=params)
        return from_list(Beatmapset.parse_obj, json)

    @check_token
    async def get_user_most_played(
        self, user_id: int, **kwargs: Any
    ) -> list[BeatmapUserPlaycount]:
        r"""Get a user's most played beatmaps.

        :param user_id: ID of the user
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of beatmaps to get
            * *offset* (``int``) --
                Optional, offset of the first beatmap to get

        :raises APIException: Contains status code and error message
        :return: List of user playcount objects
        :rtype: list[aiosu.models.beatmap.BeatmapUserPlaycount]
        """
        url = f"{self.base_url}/api/v2/users/{user_id}/beatmapsets/most_played"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="offset")
        json = await self._request("GET", url, params=params)
        return from_list(BeatmapUserPlaycount.parse_obj, json)

    @check_token
    async def get_user_recent_activity(
        self, user_id: int, **kwargs: Any
    ) -> list[Event]:
        r"""Get a user's recent activity.

        :param user_id: ID of the user
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of events to get
            * *offset* (``int``) --
                Optional, offset of the first event to get

        :raises APIException: Contains status code and error message
        :return: List of events
        :rtype: list[aiosu.models.event.Event]
        """
        url = f"{self.base_url}/api/v2/users/{user_id}/recent_activity"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="offset")
        json = await self._request("GET", url, params=params)
        return from_list(Event.parse_obj, json)

    @check_token
    async def get_beatmap_scores(self, beatmap_id: int, **kwargs: Any) -> list[Score]:
        r"""Get scores submitted on a specific beatmap.

        :param beatmap_id: Beatmap ID to search by
        :type beatmap_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *mods* (``aiosu.models.mods.Mods``) --
                Optional, mods to search for
            * *type* (``str``) --
                Optional, beatmap score ranking type

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/scores"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))  # type: ignore
        add_param(params, kwargs, key="mods", converter=lambda x: str(Mods(x)))
        add_param(params, kwargs, key="type")
        json = await self._request("GET", url, params=params)
        return from_list(Score.parse_obj, json.get("scores", []))

    @check_token
    async def get_beatmap(self, beatmap_id: int) -> Beatmap:
        r"""Get beatmap data.

        :param beatmap_id: The ID of the beatmap
        :type beatmap_id: int
        :raises APIException: Contains status code and error message
        :return: Beatmap data object
        :rtype: aiosu.models.beatmap.Beatmap
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
        :rtype: list[aiosu.models.beatmap.Beatmap]
        """
        url = f"{self.base_url}/api/v2/beatmaps"
        params: dict[str, Any] = {
            "ids": beatmap_ids,
        }
        json = await self._request("GET", url, params=params)
        return from_list(Beatmap.parse_obj, json.get("beatmaps", []))

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
        :rtype: aiosu.models.beatmap.Beatmap
        """
        url = f"{self.base_url}/api/v2/beatmaps/lookup"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="checksum")
        add_param(params, kwargs, key="filename")
        add_param(params, kwargs, key="id")
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
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *mods* (``aiosu.models.mods.Mods``) --
                Optional, mods to apply to the result

        :raises APIException: Contains status code and error message
        :return: Difficulty attributes for a beatmap
        :rtype: aiosu.models.beatmap.BeatmapDifficultyAttributes
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/attributes"
        data: dict[str, Any] = {}
        add_param(
            data,
            kwargs,
            key="mode",
            param_name="ruleset_id",
            converter=lambda x: int(Gamemode(x)),  # type: ignore
        )
        add_param(data, kwargs, key="mods", converter=lambda x: str(Mods(x)))
        json = await self._request("POST", url, data=data)
        return BeatmapDifficultyAttributes.parse_obj(json.get("attributes"))

    @check_token
    async def get_beatmapset(self, beatmapset_id: int) -> Beatmapset:
        r"""Get beatmapset data.

        :param beatmapset_id: The ID of the beatmapset
        :type beatmapset_id: int
        :raises APIException: Contains status code and error message
        :return: Beatmapset data object
        :rtype: aiosu.models.beatmap.Beatmapset
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
        :rtype: aiosu.models.beatmap.Beatmapset
        """
        url = f"{self.base_url}/api/v2/beatmapsets/lookup"
        params: dict[str, Any] = {
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
        :rtype: list[aiosu.models.beatmap.Beatmapset]
        """
        url = f"{self.base_url}/api/v2/beatmapsets/search/{search_filter}"
        json = await self._request("GET", url)
        return from_list(Beatmapset.parse_obj, json.get("beatmapsets", []))

    @check_token
    async def get_beatmapset_events(self, **kwargs: Any) -> list[BeatmapsetEvent]:
        r"""Get beatmapset events.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of results per page
            * *page* (``int``) --
                Optional, page number
            * *user_id* (``int``) --
                Optional, user ID
            * *min_date* (``datetime.datetime``) --
                Optional, minimum date
            * *max_date* (``datetime.datetime``) --
                Optional, maximum date
            * *types* (``list[aiosu.models.beatmap.BeatmapsetEventType]``) --
                Optional, event types

        :raises APIException: Contains status code and error message
        :return: List of beatmapset events
        :rtype: list[aiosu.models.event.Event]
        """
        url = f"{self.base_url}/api/v2/beatmapsets/events"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="page")
        add_param(params, kwargs, key="user_id", param_name="user")
        add_param(params, kwargs, key="min_date")
        add_param(params, kwargs, key="max_date")
        add_param(params, kwargs, key="types")
        json = await self._request("GET", url, params=params)
        return from_list(BeatmapsetEvent.parse_obj, json.get("events", []))

    @check_token
    async def get_beatmapset_discussions(
        self, **kwargs: Any
    ) -> BeatmapsetDiscussionResponse:
        r"""Get beatmapset discussions.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *beatmap_id* (``int``) --
                Optional, beatmap ID
            * *beatmapset_id* (``int``) --
                Optional, beatmapset ID
            * *beatmapset_status* (``aiosu.models.beatmap.BeatmapsetRequestStatus``) --
                Optional, beatmapset status
            * *limit* (``int``) --
                Optional, number of results per page
            * *page* (``int``) --
                Optional, page number
            * *message_types* (``list[aiosu.models.beatmap.BeatmapsetDisscussionType]``) --
                Optional, message types
            * *only_unresolved* (``bool``) --
                Optional, only unresolved discussions
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, sort order, defaults to ``id_desc``
            * *user_id* (``int``) --
                Optional, user ID
            * with_deleted (``bool``) --
                Optional, include deleted discussions
            * cursor_string (``str``) --
                Optional, cursor string

        :raises APIException: Contains status code and error message
        :return: Beatmapset discussion response
        :rtype: aiosu.models.beatmap.BeatmapsetDiscussionResponse
        """
        url = f"{self.base_url}/api/v2/beatmapsets/discussions"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="beatmap_id")
        add_param(params, kwargs, key="beatmapset_id")
        add_param(params, kwargs, key="beatmapset_status")
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="page")
        add_param(params, kwargs, key="message_types")
        add_param(params, kwargs, key="only_unresolved")
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="user", param_name="user_id")
        add_param(params, kwargs, key="with_deleted")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionResponse.parse_obj(json)
        if resp.cursor_string:
            kwargs.pop("cursor_string", None)
            resp.next = partial(
                self.get_beatmapset_discussions,
                **kwargs,
                cursor_string=resp.cursor_string,
            )
        return resp

    @check_token
    async def get_beatmapset_discussion_posts(
        self, **kwargs: Any
    ) -> BeatmapsetDiscussionPostResponse:
        r"""Get beatmapset discussion posts.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *beatmapset_discussion_id* (``int``) --
                Optional, beatmapset discussion ID
            * *limit* (``int``) --
                Optional, number of results per page
            * *page* (``int``) --
                Optional, page number
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, sort order, defaults to ``id_desc``
            * *types* (``list[str]``) --
                Optional, post types
            * *user_id* (``int``) --
                Optional, user ID
            * with_deleted (``bool``) --
                Optional, include deleted discussions
            * cursor_string (``str``) --
                Optional, cursor string

        :raises APIException: Contains status code and error message
        :return: Beatmapset discussion post response
        :rtype: aiosu.models.beatmap.BeatmapsetDiscussionPostResponse
        """
        url = f"{self.base_url}/api/v2/beatmapsets/discussions/posts"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="beatmapset_discussion_id")
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="page")
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="types")
        add_param(params, kwargs, key="user", param_name="user_id")
        add_param(params, kwargs, key="with_deleted")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionPostResponse.parse_obj(json)
        if resp.cursor_string:
            kwargs.pop("cursor_string", None)
            resp.next = partial(
                self.get_beatmapset_discussion_posts,
                **kwargs,
                cursor_string=resp.cursor_string,
            )
        return resp

    @check_token
    async def get_beatmapset_discussion_votes(
        self, **kwargs: Any
    ) -> BeatmapsetDiscussionVoteResponse:
        r"""Get beatmapset discussion votes.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *beatmapset_discussion_id* (``int``) --
                Optional, beatmapset discussion ID
            * *limit* (``int``) --
                Optional, number of results per page
            * *page* (``int``) --
                Optional, page number
            * *receiver_id* (``int``) --
                Optional, receiver ID
            * *score* (``aiosu.models.beatmap.BeatmapsetDiscussionVoteScore``) --
                Optional, vote score
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, sort order, defaults to ``id_desc``
            * *user_id* (``int``) --
                Optional, user ID
            * with_deleted (``bool``) --
                Optional, include deleted discussions
            * cursor_string (``str``) --
                Optional, cursor string

        :raises APIException: Contains status code and error message
        :return: Beatmapset discussion vote response
        :rtype: aiosu.models.beatmap.BeatmapsetDiscussionVoteResponse
        """
        url = f"{self.base_url}/api/v2/beatmapsets/discussions/votes"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="beatmapset_discussion_id")
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="page")
        add_param(params, kwargs, key="receiver", param_name="receiver_id")
        add_param(params, kwargs, key="score")
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="user", param_name="user_id")
        add_param(params, kwargs, key="with_deleted")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionVoteResponse.parse_obj(json)
        if resp.cursor_string:
            kwargs.pop("cursor_string", None)
            resp.next = partial(
                self.get_beatmapset_discussion_votes,
                **kwargs,
                cursor_string=resp.cursor_string,
            )
        return resp

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
        :type mode: aiosu.models.gamemode.Gamemode

        :raises APIException: Contains status code and error message
        :return: Score data object
        :rtype: aiosu.models.score.Score
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
        :type mode: aiosu.models.gamemode.Gamemode

        :raises APIException: Contains status code and error message
        :return: Replay file
        :rtype: io.BytesIO
        """
        url = f"{self.base_url}/api/v2/scores/{mode}/{score_id}/download"
        return await self._request("GET", url)

    @check_token
    async def get_spotlights(self) -> list[Spotlight]:
        r"""Gets the current spotlights.

        :raises APIException: Contains status code and error message
        :return: List of spotlights
        :rtype: list[aiosu.models.spotlight.Spotlight]
        """
        url = f"{self.base_url}/api/v2/spotlights"
        json = await self._request("GET", url)
        return from_list(Spotlight.parse_obj, json.get("spotlights", []))

    @check_token
    async def revoke_token(self) -> None:
        r"""Revokes the current token and closes the session.

        :raises APIException: Contains status code and error message
        """
        url = f"{self.base_url}/api/v2/oauth/tokens/current"
        await self._request("DELETE", url)
        await self.close()

    async def close(self) -> None:
        """Closes the client session."""
        if self._session:
            await self._session.close()
