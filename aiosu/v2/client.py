"""
This module handles API requests for API v2 (OAuth).

You can read more about it here: https://osu.ppy.sh/docs/index.html
"""
from __future__ import annotations

import functools
from datetime import datetime
from functools import partial
from io import BytesIO
from typing import Any
from typing import Callable
from typing import cast
from typing import Literal
from typing import TYPE_CHECKING
from typing import TypeVar
from warnings import warn

import aiohttp
import orjson
from aiolimiter import AsyncLimiter

from ..events import ClientUpdateEvent
from ..events import Eventable
from ..exceptions import APIException
from ..helpers import add_param
from ..helpers import from_list
from ..models import ArtistResponse
from ..models import Beatmap
from ..models import BeatmapDifficultyAttributes
from ..models import Beatmapset
from ..models import BeatmapsetDiscussionPostResponse
from ..models import BeatmapsetDiscussionResponse
from ..models import BeatmapsetDiscussionVoteResponse
from ..models import BeatmapsetEvent
from ..models import BeatmapsetSearchResponse
from ..models import BeatmapUserPlaycount
from ..models import Build
from ..models import ChangelogListing
from ..models import ChatChannel
from ..models import ChatChannelResponse
from ..models import ChatChannelType
from ..models import ChatMessage
from ..models import ChatMessageCreateResponse
from ..models import ChatUpdateResponse
from ..models import ChatUserSilence
from ..models import CommentBundle
from ..models import Event
from ..models import EventResponse
from ..models import ForumCreateTopicResponse
from ..models import ForumPost
from ..models import ForumTopic
from ..models import ForumTopicResponse
from ..models import Gamemode
from ..models import KudosuHistory
from ..models import LazerScore
from ..models import Mods
from ..models import MultiplayerLeaderboardResponse
from ..models import MultiplayerMatchesResponse
from ..models import MultiplayerMatchResponse
from ..models import MultiplayerRoom
from ..models import MultiplayerRoomMode
from ..models import MultiplayerScoresResponse
from ..models import NewsListing
from ..models import NewsPost
from ..models import OAuthToken
from ..models import Rankings
from ..models import RankingType
from ..models import Scopes
from ..models import Score
from ..models import SearchResponse
from ..models import SeasonalBackgroundSet
from ..models import Spotlight
from ..models import User
from ..models import UserBeatmapType
from ..models import UserQueryType
from ..models import WikiPage
from .repository import BaseTokenRepository
from .repository import SimpleTokenRepository

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional
    from typing import Union

__all__ = ("Client",)

F = TypeVar("F", bound=Callable[..., Any])
ClientRequestType = Literal["GET", "POST", "DELETE", "PUT", "PATCH"]


def to_lower_str(value: Any) -> str:
    """Converts a value to a lowercase string."""
    return str(value).lower()


def get_content_type(content_type: str) -> str:
    """Returns the content type."""
    return content_type.split(";")[0]


def prepare_token(func: F) -> F:
    """A decorator that prepares the token for use, to be used as:
    @prepare_token
    """

    @functools.wraps(func)
    async def _prepare_token(self: Client, *args: Any, **kwargs: Any) -> Any:
        await self._prepare_token()

        return await func(self, *args, **kwargs)

    return cast(F, _prepare_token)


def check_token(func: F) -> F:
    """
    A decorator that checks the current token, to be used as:
    @check_token
    """

    @functools.wraps(func)
    async def _check_token(self: Client, *args: Any, **kwargs: Any) -> Any:
        token = await self.get_current_token()
        if datetime.utcnow().timestamp() > token.expires_on.timestamp():
            await self._refresh()
        return await func(self, *args, **kwargs)

    return cast(F, _check_token)


def requires_scope(
    required_scopes: Scopes,
    any_scope: bool = False,
) -> Callable[[F], F]:
    """
    A decorator that enforces a scope, to be used as:
    @requires_scope(Scopes.PUBLIC)
    """

    def _requires_scope(
        func: F,
    ) -> F:
        @functools.wraps(func)
        async def _wrap(self: Client, *args: Any, **kwargs: Any) -> Any:
            token = await self.get_current_token()
            if any_scope:
                if not (required_scopes & token.scopes):
                    raise APIException(403, "Missing required scopes.")
            elif required_scopes & token.scopes != required_scopes:
                raise APIException(403, "Missing required scopes.")

            return await func(self, *args, **kwargs)

        return cast(F, _wrap)

    return _requires_scope


class Client(Eventable):
    r"""osu! API v2 Client

    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *token_repository* (``aiosu.v2.repository.BaseTokenRepository``) --
            Optional, defaults to ``aiosu.v2.repository.SimpleTokenRepository()``
        * *session_id* (``int``) --
            Optional, ID of the session to search in the repository, defaults to 0
        * *client_id* (``int``) --
            Optional, required to refresh tokens
        * *client_secret* (``str``) --
            Optional, required to refresh tokens
        * *base_url* (``str``) --
            Optional, base API URL, defaults to "https://osu.ppy.sh"
        * *token* (``aiosu.models.oauthtoken.OAuthToken``) --
            Optional, defaults to client credentials if not provided
        * *limiter* (``tuple[int, int]``) --
            Optional, rate limit, defaults to (600, 60) (600 requests per minute)
    """

    __slots__ = (
        "_token_repository",
        "_initial_token",
        "_session",
        "_limiter",
        "session_id",
        "client_id",
        "client_secret",
        "base_url",
    )

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._register_event(ClientUpdateEvent)
        self._token_repository: BaseTokenRepository = kwargs.pop(
            "token_repository",
            SimpleTokenRepository(),
        )
        max_rate, time_period = kwargs.pop("limiter", (600, 60))
        if (
            not isinstance(self._token_repository, SimpleTokenRepository)
            and "session_id" not in kwargs
        ):
            warn(
                "You are using a custom token repository, but did not provide a session ID. This may cause unexpected behavior.",
            )
        if (max_rate / time_period) > (1000 / 60):
            warn(
                "You are running at an insanely high rate limit. Doing so may result in your account being banned.",
            )
        self.session_id: int = kwargs.pop("session_id", 0)
        self.client_id: int = kwargs.pop("client_id", None)
        self.client_secret: str = kwargs.pop("client_secret", None)
        self._initial_token: Optional[OAuthToken] = kwargs.pop("token", None)
        self.base_url: str = kwargs.pop("base_url", "https://osu.ppy.sh")
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
        await self.close()

    def on_client_update(
        self,
        func: F,
    ) -> F:
        """
        A decorator that is called whenever a client is updated, to be used as:

            @client.on_client_update

            async def func(event: ClientUpdateEvent)
        """
        self._register_listener(func, ClientUpdateEvent)

        @functools.wraps(func)
        async def _on_client_update(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return cast(F, _on_client_update)

    async def get_current_token(self) -> OAuthToken:
        """Get the current token"""
        return await self._token_repository.get(self.session_id)

    async def _prepare_token(self) -> None:
        """Prepare the token for use."""
        if not await self._token_exists():
            token_to_add = self._initial_token
            if token_to_add is None:
                token_to_add = OAuthToken()
            await self._add_token(token_to_add)
        elif self._initial_token is not None:
            await self._update_token(self._initial_token)
        self._initial_token = None

    async def _add_token(self, token: OAuthToken) -> None:
        """Add a token to the current session"""
        await self._token_repository.add(self.session_id, token)

    async def _update_token(self, token: OAuthToken) -> None:
        """Update the current token"""
        await self._token_repository.update(self.session_id, token)

    async def _token_exists(self) -> bool:
        """Check if a token exists for the current session"""
        return await self._token_repository.exists(self.session_id)

    async def _delete_token(self) -> None:
        """Delete the current token"""
        await self._token_repository.delete(self.session_id)

    async def _get_headers(self) -> dict[str, str]:
        token = await self.get_current_token()
        return {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _refresh_auth_data(self) -> dict[str, Union[str, int]]:
        token = await self.get_current_token()
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }

    def _refresh_guest_data(self) -> dict[str, Union[str, int]]:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "public",
        }

    async def _request(
        self,
        request_type: ClientRequestType,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        await self._prepare_token()

        if self._session is None:
            self._session = aiohttp.ClientSession(headers=await self._get_headers())

        async with self._limiter:
            async with self._session.request(request_type, *args, **kwargs) as resp:
                if resp.status == 204:
                    return

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
                if content_type.startswith("application/x-osu"):
                    return BytesIO(body)
                if content_type == "text/plain":
                    return body.decode()
                raise APIException(415, f"Unhandled Content Type '{content_type}'")

    async def _refresh(self) -> None:
        r"""INTERNAL: Refreshes the client's token

        :raises APIException: Contains status code and error message
        """
        old_token = await self.get_current_token()
        url = f"{self.base_url}/oauth/token"

        data = {}
        if old_token.can_refresh:
            data = await self._refresh_auth_data()
        else:
            data = self._refresh_guest_data()

        async with aiohttp.ClientSession() as temp_session:
            async with self._limiter:
                async with temp_session.post(url, json=data) as resp:
                    try:
                        body = await resp.read()
                        content_type = get_content_type(
                            resp.headers.get("content-type", ""),
                        )
                        if content_type != "application/json":
                            raise APIException(
                                415,
                                f"Unhandled Content Type '{content_type}'",
                            )
                        json = orjson.loads(body)
                        if resp.status != 200:
                            raise APIException(resp.status, json.get("error", ""))
                        if self._session:
                            await self._session.close()
                        new_token = OAuthToken.model_validate(json)
                        await self._update_token(new_token)
                        self._session = aiohttp.ClientSession(
                            headers=await self._get_headers(),
                        )
                    except aiohttp.client_exceptions.ContentTypeError:
                        raise APIException(403, "Invalid token specified.")

        await self._process_event(
            ClientUpdateEvent(client=self, old_token=old_token, new_token=new_token),
        )

    @prepare_token
    async def get_featured_artists(self, **kwargs: Any) -> ArtistResponse:
        r"""Gets the current featured artists.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the number of featured artists to return.
            * *album* (``str``) --
                Optional, the album to filter by.
            * *artist* (``str``) --
                Optional, the artist to filter by.
            * *genre* (``int``) --
                Optional, the genre ID to filter by.
            * *length* (``list[int]``) --
                Optional, the length range to filter by.
            * *bpm* (``list[int]``) --
                Optional, The BPM range to filter by.
            * *query* (``str``) --
                Optional, the search query to filter by.
            * *is_default_sort* (``bool``) --
                Optional, whether to sort by the default sort.
            * *sort* (``str``) --
                Optional, the sort to use.

        :raises APIException: Contains status code and error message
        :return: Featured artist response object
        :rtype: aiosu.models.artist.ArtistResponse
        """
        url = f"{self.base_url}/beatmaps/artists/tracks"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="limit")
        add_param(params, kwargs, key="album")
        add_param(params, kwargs, key="artist")
        add_param(params, kwargs, key="genre")
        add_param(params, kwargs, key="length")
        add_param(params, kwargs, key="bpm")
        add_param(params, kwargs, key="query")
        add_param(params, kwargs, key="is_default_sort", converter=to_lower_str)
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url)
        resp = ArtistResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_featured_artists, **kwargs)
        return resp

    @prepare_token
    async def get_seasonal_backgrounds(self) -> SeasonalBackgroundSet:
        r"""Gets the current seasonal background set.

        :raises APIException: Contains status code and error message
        :return: Seasonal background set object
        :rtype: aiosu.models.backgrounds.SeasonalBackgroundSet
        """
        url = f"{self.base_url}/api/v2/seasonal-backgrounds"
        json = await self._request("GET", url)
        return SeasonalBackgroundSet.model_validate(json)

    @prepare_token
    async def get_changelog_listing(self, **kwargs: Any) -> ChangelogListing:
        r"""Gets the changelog listing.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *message_formats* (``list[str]``) --
                Optional, the message formats to return.
            * *from* (``str``) --
                Optional, the start date to return.
            * *to* (``str``) --
                Optional, the end date to return.
            * *max_id* (``int``) --
                Optional, the maximum ID to return.
            * *stream* (``str``) --
                Optional, the stream to return.
            * *cursor_string* (``str``) --
                Optional, the cursor string to use.

        :raises APIException: Contains status code and error message
        :return: Changelog listing object
        :rtype: aiosu.models.changelog.ChangelogListing
        """
        url = f"{self.base_url}/api/v2/changelog"
        params: dict[str, Any] = {
            "message_formats": kwargs.pop("message_formats", ["html", "markdown"]),
        }
        add_param(params, kwargs, key="from")
        add_param(params, kwargs, key="to")
        add_param(params, kwargs, key="max_id")
        add_param(params, kwargs, key="stream")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = ChangelogListing.model_validate(json)
        if resp.cursor_string:  # Unused: API does not return cursor_string
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_changelog_listing, **kwargs)
        return resp

    @prepare_token
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
        return Build.model_validate(json)

    @prepare_token
    async def lookup_changelog_build(
        self,
        changelog_query: Union[str, int],
        **kwargs: Any,
    ) -> Build:
        r"""Looks up a build from the changelog.

        :param changelog_query: The query to search for
        :type changelog_query: Union[str, int]
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *is_id* (``bool``) --
                Optional, whether the query is an ID or not, defaults to ``True`` if the query is an int
            * *message_formats* (``list[aiosu.models.news.ChangelogMessageFormats]``) --
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
        return Build.model_validate(json)

    @prepare_token
    async def get_news_listing(self, **kwargs: Any) -> NewsListing:
        r"""Gets the news listing.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the number of news posts to return. Min: 1, Max: 21, defaults to 12
            * *year* (``int``) --
                Optional, the year to filter by.
            * *cursor_string* (``str``) --
                Optional, the cursor string to use for pagination.

        :raises APIException: Contains status code and error message
        :return: News listing object
        :rtype: aiosu.models.news.NewsListing
        """
        url = f"{self.base_url}/api/v2/news"
        if not 1 <= (limit := kwargs.pop("limit", 12)) <= 21:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 21")
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="year")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = NewsListing.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_news_listing, **kwargs)
        return resp

    @prepare_token
    async def get_news_post(
        self,
        news_query: Union[str, int],
        **kwargs: Any,
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
        return NewsPost.model_validate(json)

    @prepare_token
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
        return WikiPage.model_validate(json)

    @prepare_token
    async def get_comment(self, comment_id: int, **kwargs: Any) -> CommentBundle:
        r"""Gets a comment.

        :param comment_id: The ID of the comment
        :type comment_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *cursor_string* (``str``) --
                Optional, cursor string to get the next page of comments

        :raises APIException: Contains status code and error message
        :return: Comment bundle object
        :rtype: aiosu.models.comment.CommentBundle
        """
        url = f"{self.base_url}/api/v2/comments/{comment_id}"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = CommentBundle.model_validate(json)
        if resp.cursor_string:  # Unused: API does not return cursor_string
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_comment, comment_id=comment_id, **kwargs)
        return resp

    @prepare_token
    async def get_comments(self, **kwargs: Any) -> CommentBundle:
        r"""Gets comments.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *commentable_type* (``aiosu.models.comment.CommentableType``) --
                Optional, commentable type to get comments from
            * *commentable_id* (``int``) --
                Optional, commentable ID to get comments from
            * *parent_id* (``int``) --
                Optional, parent ID to get comments from
            * *sort* (aiosu.models.comment.CommentSortType) --
                Optional, sort order of comments, defaults to ``"new"``
            * *cursor_string* (``str``) --
                Optional, cursor string to get the next page of comments

        :raises APIException: Contains status code and error message
        :return: Comment bundle object
        :rtype: aiosu.models.comment.CommentBundle
        """
        url = f"{self.base_url}/api/v2/comments"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="commentable_type")
        add_param(params, kwargs, key="commentable_id")
        add_param(params, kwargs, key="parent_id")
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = CommentBundle.model_validate(json)
        if resp.cursor_string:  # Unused: API does not return cursor_string
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_comments, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def search(self, query: str, **kwargs: Any) -> SearchResponse:
        r"""Searches for a user, beatmap, beatmapset, or wiki page.

        :param query: The query to search for
        :type query: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.search.SearchMode``) --
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
        return SearchResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
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
            mode = Gamemode(kwargs.pop("mode"))
            url += f"/{mode}"
        json = await self._request("GET", url)
        return User.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.FRIENDS_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_own_friends(self) -> list[User]:
        r"""Gets the token owner's friend list

        :raises APIException: Contains status code and error message
        :return: List of friends
        :rtype: list[aiosu.models.user.User]
        """
        url = f"{self.base_url}/api/v2/friends"
        json = await self._request("GET", url)
        return from_list(User.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
            mode = Gamemode(kwargs.pop("mode"))
            url += f"/{mode}"
        add_param(
            params,
            kwargs,
            key="qtype",
            param_name="type",
            converter=lambda x: UserQueryType(x).new_api_name,
        )
        json = await self._request("GET", url, params=params)
        return User.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return from_list(User.model_validate, json.get("users", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return from_list(KudosuHistory.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def __get_type_scores(
        self,
        user_id: int,
        request_type: str,
        **kwargs: Any,
    ) -> list[Union[Score, LazerScore]]:
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
            * *new_format* (``bool``) --
                Optional, whether to use the new format, defaults to ``False``

        :raises ValueError: If limit is not between 1 and 100
        :raises ValueError: If type is invalid
        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score] or list[aiosu.models.score.LazerScore]
        """
        if not 1 <= (limit := kwargs.pop("limit", 100)) <= 100:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 100")
        if request_type not in ("recent", "best", "firsts", "pinned"):
            raise ValueError(
                f'"{request_type}" is not a valid request_type. Valid options are: "recent", "best", "firsts"',
            )
        url = f"{self.base_url}/api/v2/users/{user_id}/scores/{request_type}"
        params: dict[str, Any] = {
            "include_fails": int(kwargs.pop("include_fails", False)),
            "limit": limit,
            "offset": kwargs.pop("offset", 0),
        }
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))
        headers = {}
        new_format = kwargs.pop("new_format", False)
        if new_format:
            headers = {"x-api-version": "20220705"}
        json = await self._request("GET", url, params=params, headers=headers)
        if new_format:
            return from_list(LazerScore.model_validate, json)
        return from_list(Score.model_validate, json)

    async def get_user_recents(
        self,
        user_id: int,
        **kwargs: Any,
    ) -> list[Union[Score, LazerScore]]:
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
            * *new_format* (``bool``) --
                Optional, whether to use the new format, defaults to ``False``

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score] or list[aiosu.models.score.LazerScore]
        """
        return await self.__get_type_scores(user_id, "recent", **kwargs)

    async def get_user_bests(
        self,
        user_id: int,
        **kwargs: Any,
    ) -> list[Union[Score, LazerScore]]:
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
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0
            * *new_format* (``bool``) --
                Optional, whether to use the new format, defaults to ``False``

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score] or list[aiosu.models.score.LazerScore]
        """
        return await self.__get_type_scores(user_id, "best", **kwargs)

    async def get_user_firsts(
        self,
        user_id: int,
        **kwargs: Any,
    ) -> list[Union[Score, LazerScore]]:
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
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0
            * *new_format* (``bool``) --
                Optional, whether to use the new format, defaults to ``False``

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score] or list[aiosu.models.score.LazerScore]
        """
        return await self.__get_type_scores(user_id, "firsts", **kwargs)

    async def get_user_pinned(
        self,
        user_id: int,
        **kwargs: Any,
    ) -> list[Union[Score, LazerScore]]:
        r"""Get a user's pinned scores.

        :param user_id: User ID to search by
        :type user_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.gamemode.Gamemode``) --
                Optional, gamemode to search for
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *offset* (``int``) --
                Optional, page offset to start from, defaults to 0
            * *new_format* (``bool``) --
                Optional, whether to use the new format, defaults to ``False``

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score] or list[aiosu.models.score.LazerScore]
        """
        return await self.__get_type_scores(user_id, "pinned", **kwargs)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_user_beatmap_scores(
        self,
        user_id: int,
        beatmap_id: int,
        **kwargs: Any,
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
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))
        json = await self._request("GET", url, params=params)
        return from_list(Score.model_validate, json.get("scores", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_user_beatmaps(
        self,
        user_id: int,
        type: UserBeatmapType,
        **kwargs: Any,
    ) -> list[Beatmapset]:
        r"""Get a user's beatmaps.

        :param user_id: ID of the user
        :type user_id: int
        :param type: Type of beatmaps to get
        :type type: aiosu.models.beatmap.UserBeatmapType
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
        return from_list(Beatmapset.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_user_most_played(
        self,
        user_id: int,
        **kwargs: Any,
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
        return from_list(BeatmapUserPlaycount.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_user_recent_activity(
        self,
        user_id: int,
        **kwargs: Any,
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
        return from_list(Event.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_events(self) -> EventResponse:
        r"""Get global events.

        :raises APIException: Contains status code and error message
        :return: Event response object
        :rtype: aiosu.models.event.EventResponse
        """
        url = f"{self.base_url}/api/v2/events"
        json = await self._request("GET", url)
        return EventResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
            * *type* (``aiosu.models.common.BeatmapScoreboardType``) --
                Optional, beatmap score ranking type

        :raises APIException: Contains status code and error message
        :return: List of requested scores
        :rtype: list[aiosu.models.score.Score]
        """
        url = f"{self.base_url}/api/v2/beatmaps/{beatmap_id}/scores"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="mode", converter=lambda x: str(Gamemode(x)))
        add_param(
            params,
            kwargs,
            key="mods",
            converter=lambda x: [str(y) for y in Mods(x)],
        )
        add_param(params, kwargs, key="type")
        json = await self._request("GET", url, params=params)
        return from_list(Score.model_validate, json.get("scores", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return Beatmap.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return from_list(Beatmap.model_validate, json.get("beatmaps", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return Beatmap.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_beatmap_attributes(
        self,
        beatmap_id: int,
        **kwargs: Any,
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
            converter=lambda x: int(Gamemode(x)),
        )
        add_param(data, kwargs, key="mods", converter=lambda x: int(Mods(x)))
        json = await self._request("POST", url, json=data)
        return BeatmapDifficultyAttributes.model_validate(json.get("attributes"))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return Beatmapset.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return Beatmapset.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def search_beatmapsets(
        self,
        search_filter: Optional[str] = "",
        **kwargs: Any,
    ) -> BeatmapsetSearchResponse:
        r"""Search beatmapset by filter.

        :param search_filter: The search filter.
        :type search_filter: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *cursor_string* (``str``) --
                Optional, cursor string to get the next page of results

        :raises APIException: Contains status code and error message
        :return: Beatmapset search response
        :rtype: list[aiosu.models.beatmap.BeatmapsetSearchResponse]
        """
        url = f"{self.base_url}/api/v2/beatmapsets/search/{search_filter}"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url)
        resp = BeatmapsetSearchResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.search_beatmapsets, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
            * *beatmapset_id* (``int``) --
                Optional, beatmapset ID
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
        add_param(params, kwargs, key="beatmapset_id")
        add_param(params, kwargs, key="user_id", param_name="user")
        add_param(params, kwargs, key="min_date")
        add_param(params, kwargs, key="max_date")
        add_param(params, kwargs, key="types")
        json = await self._request("GET", url, params=params)
        return from_list(BeatmapsetEvent.model_validate, json.get("events", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_beatmapset_discussions(
        self,
        **kwargs: Any,
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
        add_param(params, kwargs, key="only_unresolved", converter=to_lower_str)
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="user", param_name="user_id")
        add_param(params, kwargs, key="with_deleted", converter=to_lower_str)
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_beatmapset_discussions, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_beatmapset_discussion_posts(
        self,
        **kwargs: Any,
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
        add_param(params, kwargs, key="with_deleted", converter=to_lower_str)
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionPostResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_beatmapset_discussion_posts, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_beatmapset_discussion_votes(
        self,
        **kwargs: Any,
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
        add_param(params, kwargs, key="with_deleted", converter=to_lower_str)
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = BeatmapsetDiscussionVoteResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_beatmapset_discussion_votes, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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
        return Score.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
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

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_rankings(
        self,
        mode: Gamemode,
        type: RankingType,
        **kwargs: Any,
    ) -> Rankings:
        r"""Get rankings.

        :param mode: The gamemode to search for
        :type mode: aiosu.models.gamemode.Gamemode
        :param type: The ranking type to search for
        :type type: aiosu.models.rankings.RankingType
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *country* (``str``) --
                Optional, country code
            * *filter* (``aiosu.models.rankings.RankingFilter``) --
                Optional, ranking filter
            * *spotlight* (``int``) --
                Optional, spotlight ID
            * *variant* (``aiosu.models.rankings.RankingVariant``) --
                Optional, ranking variant
            * *cursor_string* (``str``) --
                Optional, cursor string

        :raises APIException: Contains status code and error message
        :return: Rankings
        :rtype: aiosu.models.rankings.Rankings
        """
        url = f"{self.base_url}/api/v2/rankings/{mode}/{type}"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="country")
        add_param(params, kwargs, key="filter")
        add_param(params, kwargs, key="spotlight")
        add_param(params, kwargs, key="variant")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = Rankings.model_validate(json)
        if resp.cursor_string:  # Unused: API does not return cursor_string
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_rankings, mode=mode, type=type, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_rankings_kudosu(self, **kwargs: Any) -> Rankings:
        r"""Get kudosu rankings.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *page_id* (``int``) --
                Optional, page ID

        :raises APIException: Contains status code and error message
        :return: Rankings
        :rtype: aiosu.models.rankings.Rankings
        """
        url = f"{self.base_url}/api/v2/rankings/kudosu"
        params: dict[str, Any] = {}
        add_param(params, kwargs, key="page_id", param_name="page")
        json = await self._request("GET", url, params=params)
        resp = Rankings.model_validate(json)
        kwargs["page_id"] = min(params.get("page_id", 1) + 1, 20)
        resp.next = partial(self.get_rankings_kudosu, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_spotlights(self) -> list[Spotlight]:
        r"""Gets the current spotlights.

        :raises APIException: Contains status code and error message
        :return: List of spotlights
        :rtype: list[aiosu.models.spotlight.Spotlight]
        """
        url = f"{self.base_url}/api/v2/spotlights"
        json = await self._request("GET", url)
        return from_list(Spotlight.model_validate, json.get("spotlights", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_forum_topic(self, topic_id: int, **kwargs: Any) -> ForumTopicResponse:
        r"""Gets a forum topic.

        :param topic_id: The ID of the topic
        :type topic_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the number of posts to return. Min: 1, Max: 50, defaults to 20
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, the sort type to use. Defaults to ``id_asc``
            * *start* (``int``) --
                Optional, the start post ID to use for pagination.
            * *end* (``int``) --
                Optional, the end post ID to use for pagination.
            * *cursor_string* (``str``) --
                Optional, the cursor string to use for pagination.

        :raises APIException: Contains status code and error message
        :return: Forum topic response object
        :rtype: aiosu.models.forum.ForumTopicResponse
        """
        if not 1 <= (limit := kwargs.pop("limit", 20)) <= 50:
            raise ValueError("Invalid limit specified. Limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/forums/topics/{topic_id}"
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="start")
        add_param(params, kwargs, key="end")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = ForumTopicResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_forum_topic, topic_id, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.FORUM_WRITE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def create_forum_topic(
        self,
        forum_id: int,
        title: str,
        content: str,
        **kwargs: Any,
    ) -> ForumCreateTopicResponse:
        r"""Creates a forum topic.

        :param forum_id: The ID of the forum to create the topic in
        :type forum_id: int
        :param title: The title of the topic
        :type title: str
        :param content: The content of the topic
        :type content: str
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *with_poll* (``bool``) --
                Optional, whether to create a poll with the topic. Defaults to ``False``
            * *poll_title* (``str``) --
                Optional, the title of the poll
            * *poll_options* (``list[str]``) --
                Optional, the options for the poll
            * *poll_length_days* (``int``) --
                Optional, the length of the poll in days. Defaults to 0
            * *poll_vote_change* (``bool``) --
                Optional, whether to allow users to change their vote. Defaults to ``False``
            * *poll_hide_results* (``bool``) --
                Optional, whether to hide the results of the poll. Defaults to ``False``
            * *poll_max_votes* (``int``) --
                Optional, the maximum number of votes a user can make. Defaults to 1

        :raises APIException: Contains status code and error message
        :return: Forum create topic response object
        :rtype: aiosu.models.forum.ForumCreateTopicResponse
        """
        url = f"{self.base_url}/api/v2/forums/topics"
        data: dict[str, Any] = {
            "forum_id": forum_id,
            "title": title,
            "body": content,
        }
        add_param(data, kwargs, key="with_poll")
        if data.get("with_poll"):
            forum_topic_poll: dict[str, Any] = {
                "title": kwargs["poll_title"],
                "length_days": kwargs.pop("poll_length_days", 0),
                "vote_change": kwargs.pop("poll_vote_change", False),
                "hide_results": kwargs.pop("poll_hide_results", False),
                "max_votes": kwargs.pop("poll_max_votes", 1),
            }
            add_param(
                forum_topic_poll,
                kwargs,
                key="options",
                param_name="poll_options",
            )
            data["forum_topic_poll"] = forum_topic_poll
        json = await self._request("POST", url, json=data)
        return ForumCreateTopicResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.FORUM_WRITE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def reply_forum_topic(self, topic_id: int, content: str) -> ForumPost:
        r"""Replies to a forum topic.

        :param topic_id: The ID of the topic
        :type topic_id: int
        :param content: The content of the post
        :type content: str
        :raises APIException: Contains status code and error message
        :return: Forum post object
        :rtype: aiosu.models.forum.ForumPost
        """
        url = f"{self.base_url}/api/v2/forums/topics/{topic_id}/reply"
        data: dict[str, str] = {
            "body": content,
        }
        json = await self._request("POST", url, json=data)
        return ForumPost.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.FORUM_WRITE)
    async def edit_forum_topic_title(self, topid_id: int, new_title: str) -> ForumTopic:
        r"""Edits a forum topic's title.

        :param topid_id: The ID of the topic
        :type topid_id: int
        :param new_title: The new title of the topic
        :type new_title: str
        :raises APIException: Contains status code and error message
        :return: Forum topic object
        :rtype: aiosu.models.forum.ForumTopic
        """
        url = f"{self.base_url}/api/v2/forums/topics/{topid_id}/title"
        data: dict[str, dict[str, str]] = {
            "forum_topic": {
                "topic_title": new_title,
            },
        }
        json = await self._request("PUT", url, json=data)
        return ForumTopic.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.FORUM_WRITE)
    async def edit_forum_post(self, post_id: int, new_content: str) -> ForumPost:
        r"""Edits a forum post.

        :param post_id: The ID of the post
        :type post_id: int
        :param new_content: The new content of the post
        :type new_content: str
        :raises APIException: Contains status code and error message
        :return: Forum post object
        :rtype: aiosu.models.forum.ForumPost
        """
        url = f"{self.base_url}/api/v2/forums/posts/{post_id}"
        data: dict[str, str] = {
            "body": new_content,
        }
        json = await self._request("PUT", url, json=data)
        return ForumPost.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_chat_ack(self, **kwargs: Any) -> list[ChatUserSilence]:
        r"""Gets chat acknowledgement.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *since* (``int``) --
                Optional, the last message ID received
            * *silence_id_since* (``int``) --
                Optional, the last silence ID received

        :raises APIException: Contains status code and error message
        :return: List of chat user silence objects
        :rtype: list[aiosu.models.chat.ChatUserSilence]
        """
        url = f"{self.base_url}/api/v2/chat/ack"
        data: dict[str, Any] = {}
        add_param(data, kwargs, key="since")
        add_param(data, kwargs, key="silence_id_since", param_name="history_since")
        json = await self._request("POST", url, json=data)
        return from_list(ChatUserSilence.model_validate, json.get("silences", []))

    @prepare_token
    @check_token
    @requires_scope(Scopes.LAZER)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_chat_updates(self, since: int, **kwargs: Any) -> ChatUpdateResponse:
        r"""Gets chat updates.

        :param since: The last message ID received
        :type since: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the maximum number of messages to return. Min: 1, Max: 50. Defaults to 50
            * *channel_id* (``int``) --
                Optional, the channel ID to get messages from
            * *silence_id_since* (``int``) --
                Optional, the last silence ID received
            * *includes* (``list[aiosu.models.chat.ChatIncludeTypes]``) --
                Optional, the additional information to include. Defaults to all.

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: Chat update response object
        :rtype: aiosu.models.chat.ChatUpdateResponse
        """
        if not 1 <= (limit := kwargs.get("limit", 50)) <= 50:
            raise ValueError("limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/chat/updates"
        params: dict[str, Any] = {
            "since": since,
            "limit:": limit,
        }
        add_param(params, kwargs, key="channel_id")
        add_param(params, kwargs, key="includes")
        add_param(params, kwargs, key="silence_id_since", param_name="history_since")
        json = await self._request("GET", url, params=params)
        return ChatUpdateResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_channel(self, channel_id: int) -> ChatChannelResponse:
        r"""Gets channel.

        :param channel_id: The channel ID to get
        :type channel_id: int
        :raises APIException: Contains status code and error message
        :return: Chat channel object
        :rtype: aiosu.models.chat.ChatChannelResponse
        """
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}"
        json = await self._request("GET", url)
        return ChatChannelResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_channels(self) -> list[ChatChannel]:
        r"""Gets a list of joinable public channels.

        :raises APIException: Contains status code and error message
        :return: List of chat channel objects
        :rtype: list[aiosu.models.chat.ChatChannel]
        """
        url = f"{self.base_url}/api/v2/chat/channels"
        json = await self._request("GET", url)
        return from_list(ChatChannel.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_channel_messages(
        self,
        channel_id: int,
        **kwargs: Any,
    ) -> list[ChatMessage]:
        r"""Gets channel messages.

        :param channel_id: The channel ID to get messages from
        :type channel_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the maximum number of messages to return. Min: 1, Max: 50. Defaults to 50
            * *since* (``int``) --
                Optional, the ID of the oldest message to return
            * *until* (``int``) --
                Optional, the ID of the newest message to return

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: List of chat message objects
        :rtype: list[aiosu.models.chat.ChatMessage]
        """
        if not 1 <= (limit := kwargs.get("limit", 50)) <= 50:
            raise ValueError("limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}/messages"
        params: dict[str, Any] = {
            "limit:": limit,
        }
        add_param(params, kwargs, key="since")
        add_param(params, kwargs, key="until")
        json = await self._request("GET", url, params=params)
        return from_list(ChatMessage.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_WRITE_MANAGE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def create_chat_channel(
        self,
        type: ChatChannelType,
        **kwargs: Any,
    ) -> ChatChannel:
        r"""Creates a chat channel.

        :param type: The type of the channel.
        :type type: aiosu.models.chat.ChatChannelType
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *message* (``str``) --
                Required if type is ``ANNOUNCE``, the message to send in the PM
            * *target_id* (``int``) --
                Only used if if type is ``PM``, the ID of the user to send a PM to
            * *target_ids* (``List[int]``) --
                Only used if type is ``ANNOUNCE``, the IDs of the users to send a PM to
            * *channel_name* (``str``) --
                Only used if type is ``ANNOUNCE``, the name of the channel
            * *channel_description* (``str``) --
                Only used if type is ``ANNOUNCE``, the description of the channel

        :raises ValueError: If missing required parameters
        :raises APIException: Contains status code and error message
        :return: Chat channel object
        :rtype: aiosu.models.chat.ChatChannel
        """
        url = f"{self.base_url}/api/v2/chat/channels"
        data: dict[str, Any] = {
            "type": type,
        }
        add_param(data, kwargs, key="message")
        if type == "PM":
            if not add_param(data, kwargs, key="target_id"):
                raise ValueError("Missing target ID")
        elif type == "ANNOUNCE":
            if not add_param(data, kwargs, key="target_ids"):
                raise ValueError("Missing target IDs")
            if not data.get("message"):
                raise ValueError("Missing message")
            channel = {
                "name": kwargs["channel_name"],
                "description": kwargs["channel_description"],
            }
            data["channel"] = channel
        json = await self._request("POST", url, json=data)
        return ChatChannel.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_WRITE_MANAGE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def join_channel(self, channel_id: int, user_id: int) -> ChatChannel:
        r"""Joins a channel.

        :param channel_id: The channel ID to join
        :type channel_id: int
        :param user_id: The user ID to join as
        :type user_id: int
        :raises APIException: Contains status code and error message
        :return: Chat channel object
        :rtype: aiosu.models.chat.ChatChannel
        """
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}/users/{user_id}"
        json = await self._request("PUT", url)
        return ChatChannel.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_WRITE_MANAGE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def leave_channel(self, channel_id: int, user_id: int) -> None:
        r"""Leaves a channel.

        :param channel_id: The channel ID to leave
        :type channel_id: int
        :param user_id: The user ID to leave as
        :type user_id: int
        :raises APIException: Contains status code and error message
        """
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}/users/{user_id}"
        await self._request("DELETE", url)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_READ)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def mark_read(self, channel_id: int, message_id: int) -> None:
        r"""Marks a channel as read.

        :param channel_id: The channel ID to mark as read
        :type channel_id: int
        :param message_id: The message ID to mark as read up to
        :type message_id: int
        :raises APIException: Contains status code and error message
        """
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}/mark-as-read/{message_id}"
        await self._request("PUT", url)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_WRITE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def send_message(
        self,
        channel_id: int,
        message: str,
        is_action: bool,
    ) -> ChatMessage:
        r"""Sends a message to a channel.

        :param channel_id: The ID of the channel
        :type channel_id: int
        :param message: The message to send
        :type message: str
        :param is_action: Whether the message is an action
        :type is_action: bool
        :raises APIException: Contains status code and error message
        :return: Chat message object
        :rtype: aiosu.models.chat.ChatMessage
        """
        url = f"{self.base_url}/api/v2/chat/channels/{channel_id}/messages"
        data: dict[str, Any] = {
            "message": message,
            "is_action": is_action,
        }
        json = await self._request("POST", url, json=data)
        return ChatMessage.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.CHAT_WRITE)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def send_private_message(
        self,
        user_id: int,
        message: str,
        is_action: bool,
        **kwargs: Any,
    ) -> ChatMessageCreateResponse:
        r"""Sends a message to a user.

        :param user_id: The ID of the user
        :type user_id: int
        :param message: The message to send
        :type message: str
        :param is_action: Whether the message is an action
        :type is_action: bool
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *uuid* (``str``) --
                Optional, client-side message identifier to be sent back in response and websocket json

        :raises APIException: Contains status code and error message
        :return: Chat message create response object
        :rtype: aiosu.models.chat.ChatMessageCreateResponse
        """
        url = f"{self.base_url}/api/v2/chat/new"
        data: dict[str, Any] = {
            "target_id": user_id,
            "message": message,
            "is_action": is_action,
        }
        add_param(data, kwargs, key="uuid")
        json = await self._request("POST", url, json=data)
        return ChatMessageCreateResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_multiplayer_matches(
        self,
        **kwargs: Any,
    ) -> MultiplayerMatchesResponse:
        r"""Gets the multiplayer matches.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, the sort type
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 50, defaults to 50
            * *cursor_string* (``str``) --
                Optional, the cursor string to get the next page of results

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: Multiplayer matches response object
        :rtype: aiosu.models.multiplayer.MultiplayerMatchesResponse
        """
        if not 1 <= (limit := kwargs.pop("limit", 1)) <= 50:
            raise ValueError("Limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/matches"
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="sort")
        json = await self._request("GET", url, params=params)
        resp = MultiplayerMatchesResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(self.get_multiplayer_matches, **kwargs)
        return resp

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_multiplayer_match(
        self,
        match_id: int,
        **kwargs: Any,
    ) -> MultiplayerMatchResponse:
        r"""Gets a multiplayer match.

        :param match_id: The ID of the match
        :type match_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 100, defaults to 100
            * *before* (``int``) --
                Optional, the ID of the score to get the scores before
            * *after* (``int``) --
                Optional, the ID of the score to get the scores after

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: Multiplayer match response object
        :rtype: aiosu.models.multiplayer.MultiplayerMatchResponse
        """
        if not 1 <= (limit := kwargs.pop("limit", 1)) <= 100:
            raise ValueError("Limit must be between 1 and 100")
        url = f"{self.base_url}/api/v2/matches/{match_id}"
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="before")
        add_param(params, kwargs, key="after")
        json = await self._request("GET", url)
        return MultiplayerMatchResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_multiplayer_rooms(self, **kwargs: Any) -> list[MultiplayerRoom]:
        r"""Gets the multiplayer rooms.

        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *mode* (``aiosu.models.multiplayer.MultiplayerRoomMode``) --
                Optional, the multiplayer room mode
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 50, defaults to 50
            * *sort* (``aiosu.models.common.SortTypes``) --
                Optional, the sort type
            * *category* (``aiosu.models.multiplayer.MultiplayerRoomCategories``) --
                Optional, the multiplayer room category
            * *type* (``aiosu.models.multiplayer.MultiplayerRoomTypeGroups``) --
                Optional, the multiplayer room type group

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: List of multiplayer rooms
        :rtype: list[aiosu.models.multiplayer.MultiplayerRoom]
        """
        if not 1 <= (limit := kwargs.pop("limit", 50)) <= 50:
            raise ValueError("Limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/rooms"
        if "mode" in kwargs:
            mode: MultiplayerRoomMode = kwargs.pop("mode")
            url += f"/{mode}"
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="category")
        add_param(params, kwargs, key="type", param_name="type_group")
        json = await self._request("GET", url, params=params)
        return from_list(MultiplayerRoom.model_validate, json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_multiplayer_room(self, room_id: int) -> MultiplayerRoom:
        r"""Gets a multiplayer room.

        :param room_id: The ID of the room
        :type room_id: int

        :raises APIException: Contains status code and error message
        :return: Multiplayer room object
        :rtype: aiosu.models.multiplayer.MultiplayerRoom
        """
        url = f"{self.base_url}/api/v2/rooms/{room_id}"
        json = await self._request("GET", url)
        return MultiplayerRoom.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    @requires_scope(Scopes.IDENTIFY | Scopes.DELEGATE, any_scope=True)
    async def get_multiplayer_leaderboard(
        self,
        room_id: int,
        **kwargs: Any,
    ) -> MultiplayerLeaderboardResponse:
        r"""Gets the multiplayer leaderboard for a room.

        :param room_id: The ID of the room
        :type room_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, number of scores to get. Min: 1, Max: 50, defaults to 50

        :raises ValueError: If limit is not between 1 and 50
        :raises APIException: Contains status code and error message
        :return: Multiplayer leaderboard response object
        :rtype: aiosu.models.multiplayer.MultiplayerLeaderboardResponse
        """
        if not 1 <= (limit := kwargs.pop("limit", 50)) <= 50:
            raise ValueError("Limit must be between 1 and 50")
        url = f"{self.base_url}/api/v2/rooms/{room_id}/leaderboard"
        params: dict[str, Any] = {
            "limit": limit,
        }
        json = await self._request("GET", url, params=params)
        return MultiplayerLeaderboardResponse.model_validate(json)

    @prepare_token
    @check_token
    @requires_scope(Scopes.PUBLIC)
    async def get_multiplayer_scores(
        self,
        room_id: int,
        playlist_id: int,
        **kwargs: Any,
    ) -> MultiplayerScoresResponse:
        r"""Gets the multiplayer scores for a room.

        :param room_id: The ID of the room
        :type room_id: int
        :param playlist_id: The ID of the playlist
        :type playlist_id: int
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *limit* (``int``) --
                Optional, the number of scores to return
            * *sort* (``aiosu.models.multiplayer.MultiplayerScoreSortType``) --
                Optional, the sort order of the scores
            * *cursor_string* (``str``) --
                Optional, the cursor string to use for pagination

        :raises ValueError: If limit is not between 1 and 100
        :raises APIException: Contains status code and error message
        :return: Multiplayer scores response object
        :rtype: aiosu.models.multiplayer.MultiplayerScoresResponse
        """
        if not 1 <= (limit := kwargs.pop("limit", 1)) <= 100:
            raise ValueError("Limit must be between 1 and 100")
        url = f"{self.base_url}/api/v2/rooms/{room_id}/playlist/{playlist_id}/scores"
        params: dict[str, Any] = {
            "limit": limit,
        }
        add_param(params, kwargs, key="sort")
        add_param(params, kwargs, key="cursor_string")
        json = await self._request("GET", url, params=params)
        resp = MultiplayerScoresResponse.model_validate(json)
        if resp.cursor_string:
            kwargs["cursor_string"] = resp.cursor_string
            resp.next = partial(
                self.get_multiplayer_scores,
                room_id,
                playlist_id,
                **kwargs,
            )
        return resp

    @prepare_token
    @check_token
    async def revoke_token(self) -> None:
        r"""Revokes the current token and closes the session.

        :raises APIException: Contains status code and error message
        """
        url = f"{self.base_url}/api/v2/oauth/tokens/current"
        await self._request("DELETE", url)
        await self._delete_token()
        await self.close()

    async def close(self) -> None:
        """Closes the client session."""
        if self._session:
            await self._session.close()
            self._session = None
