"""
This module is used to generate test data for aiosu tests from the osu! API.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import urllib.parse
import webbrowser
from abc import ABC
from abc import abstractmethod
from functools import partial

import aiohttp
import orjson
from aiohttp import web
from dotenv import load_dotenv

import aiosu

API_MODES = ["osu", "taiko", "fruits", "mania"]
BASE_URL = "https://osu.ppy.sh"
BASE_URL_LAZER = "https://lazer.ppy.sh"
BASE_URL_DEV = "https://dev.ppy.sh"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DEFAULT_REDIRECT_URI = "http://localhost:7270/callback"
OAUTH_TIMEOUT = 300
MAX_ATTEMPTS = 3
RETRY_DELAY = 5
FULL_SCOPES = (
    aiosu.models.Scopes.PUBLIC
    | aiosu.models.Scopes.IDENTIFY
    | aiosu.models.Scopes.FRIENDS_READ
    | aiosu.models.Scopes.FORUM_WRITE
    | aiosu.models.Scopes.CHAT_READ
    | aiosu.models.Scopes.CHAT_WRITE
    | aiosu.models.Scopes.CHAT_WRITE_MANAGE
)

logger = logging.getLogger("aiosu")


async def interactive_oauth_token(
    client_id: int,
    client_secret: str,
    redirect_uri: str,
    base_url: str = BASE_URL,
    scopes: aiosu.models.Scopes = FULL_SCOPES,
) -> aiosu.models.OAuthToken:
    """
    Obtain an OAuth token by opening the authorization page in the browser
    and catching the redirect on a local callback server.
    """

    parsed = urllib.parse.urlparse(redirect_uri)
    code_future: asyncio.Future[str] = asyncio.get_running_loop().create_future()

    async def callback(request: web.Request) -> web.Response:
        if not code_future.done():
            code = request.query.get("code")
            if code is not None:
                code_future.set_result(code)
            else:
                error = request.query.get("error", "no code returned")
                code_future.set_exception(
                    RuntimeError(f"OAuth authorization failed: {error}"),
                )
        return web.Response(
            text="<html><body><h3>aiosu test generator</h3>"
            "<p>Authorization received. You may close this tab.</p></body></html>",
            content_type="text/html",
        )

    app = web.Application()
    app.router.add_get(parsed.path or "/", callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, parsed.hostname or "localhost", parsed.port or 80)
    await site.start()

    auth_url = aiosu.utils.auth.generate_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        base_url=base_url,
        scopes=scopes,
    )
    logger.info(f"Requesting authorization: {auth_url}")
    if not webbrowser.open(auth_url):
        logger.info("Could not open a browser. Please visit the URL manually.")
    try:
        code = await asyncio.wait_for(code_future, timeout=OAUTH_TIMEOUT)
    finally:
        await runner.cleanup()

    return await aiosu.utils.auth.process_code(
        client_id,
        client_secret,
        redirect_uri,
        code,
        base_url=base_url,
    )


async def get_token(env_prefix: str, base_url: str) -> aiosu.models.OAuthToken:
    """
    Build a token from ``{env_prefix}ACCESS_TOKEN`` if set, otherwise run the
    interactive browser flow using ``{env_prefix}CLIENT_ID``/``{env_prefix}CLIENT_SECRET``.
    """

    access_token = os.environ.get(f"{env_prefix}ACCESS_TOKEN")
    if access_token:
        return aiosu.models.OAuthToken(
            access_token=access_token,
            refresh_token="",
            expires_in=86400,
        )
    client_id = os.environ.get(f"{env_prefix}CLIENT_ID")
    client_secret = os.environ.get(f"{env_prefix}CLIENT_SECRET")
    if not (client_id and client_secret):
        raise ValueError(
            f"Either {env_prefix}ACCESS_TOKEN or {env_prefix}CLIENT_ID and "
            f"{env_prefix}CLIENT_SECRET must be set",
        )
    redirect_uri = os.environ.get(
        f"{env_prefix}REDIRECT_URI",
        DEFAULT_REDIRECT_URI,
    )
    return await interactive_oauth_token(
        int(client_id),
        client_secret,
        redirect_uri,
        base_url=base_url,
    )


class TestGeneratorBase(ABC):
    __slots__ = ("client", "routes")

    def __init__(self) -> None:
        self.client = None
        self.routes = []

    def _register_route(
        self,
        method: str,
        url: str,
        filename: str,
        expect_status: int = 200,
        headers: dict | None = None,
        params: dict | None = None,
        data: dict | None = None,
    ) -> None:
        self.routes.append(
            partial(
                self._save_data,
                method,
                url,
                filename,
                expect_status,
                headers,
                params,
                data,
            ),
        )

    @abstractmethod
    def _register_routes(self) -> None: ...

    def _ensure_dir(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path)

    async def _save_data(
        self,
        method: str,
        url: str,
        filename: str,
        expect_status: int,
        headers: dict | None = None,
        params: dict | None = None,
        data: dict | None = None,
    ) -> None:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            async with self.client._session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers,
            ) as resp:
                if resp.status == expect_status:
                    resp_data = await resp.read()
                    with open(os.path.normpath(filename), "wb") as f:
                        f.write(resp_data)
                    return

                if resp.status < 500 or attempt == MAX_ATTEMPTS:
                    raise ValueError(
                        f"Expected {method} {url} to return {expect_status}, got {resp.status}",
                    )
                logger.warning(
                    f"{method} {url} returned {resp.status}, "
                    f"retrying ({attempt}/{MAX_ATTEMPTS})",
                )
            await asyncio.sleep(RETRY_DELAY * attempt)

    async def run(self) -> None:
        self._register_routes()
        for route in self.routes:
            logger.info(f"Running {route}")
            await route()


class TestGeneratorV1(TestGeneratorBase):
    def __init__(self, api_key: str) -> None:
        super().__init__()

        self.client = aiosu.v1.Client(token=api_key)
        self._ensure_dir(f"{DATA_DIR}/v1")
        self._default_params = {"k": api_key}

    def _register_routes(self) -> None:
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_beatmaps",
            f"{DATA_DIR}/v1/get_beatmap_200.json",
            params=self._default_params,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_user",
            f"{DATA_DIR}/v1/get_user_200.json",
            params=self._default_params | {"u": "peppy"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_scores",
            f"{DATA_DIR}/v1/get_beatmap_scores_200.json",
            params=self._default_params | {"b": "2906626"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_user_best",
            f"{DATA_DIR}/v1/get_user_bests_200.json",
            params=self._default_params | {"u": "peppy"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_user_recent",
            f"{DATA_DIR}/v1/get_user_recents_200.json",
            params=self._default_params | {"u": "lifeline"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_match",
            f"{DATA_DIR}/v1/get_match_200.json",
            params=self._default_params | {"mp": "105019274"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_replay",
            f"{DATA_DIR}/v1/get_replay_200.json",
            params=self._default_params | {"m": "0", "b": "2906626", "u": "4819811"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/get_replay",
            f"{DATA_DIR}/v1/get_replay_404.json",
            params=self._default_params | {"m": "0", "b": "2906626", "u": "peppy"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/osu/2906626",
            f"{DATA_DIR}/v1/get_beatmap_osu_200.osu",
        )

    async def run(self) -> None:
        self.client._session = aiohttp.ClientSession()
        try:
            await super().run()
        finally:
            await self.client.aclose()


class TestGeneratorV2(TestGeneratorBase):
    def __init__(self, token: aiosu.models.OAuthToken) -> None:
        super().__init__()

        self.client = aiosu.v2.Client(token=token)
        self._ensure_dir(f"{DATA_DIR}/v2")

    def _register_routes(self) -> None:
        self._register_route(
            "GET",
            f"{BASE_URL}/beatmaps/artists/tracks",
            f"{DATA_DIR}/v2/get_featured_artists_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/seasonal-backgrounds",
            f"{DATA_DIR}/v2/get_seasonal_backgrounds_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/changelog",
            f"{DATA_DIR}/v2/get_changelog_listing_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/changelog/lazer/2023.815.0",
            f"{DATA_DIR}/v2/get_changelog_build_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/changelog/lazer/thiswill404",
            f"{DATA_DIR}/v2/get_changelog_build_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/changelog/lazer",
            f"{DATA_DIR}/v2/lookup_changelog_build_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/changelog/thiswill404",
            f"{DATA_DIR}/v2/lookup_changelog_build_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/news",
            f"{DATA_DIR}/v2/get_news_listing_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/news/1",
            f"{DATA_DIR}/v2/get_news_post_200.json",
            params={"key": "id"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/news/0",
            f"{DATA_DIR}/v2/get_news_post_404.json",
            expect_status=404,
            params={"key": "id"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/wiki/en/Main_page",
            f"{DATA_DIR}/v2/get_wiki_page_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/wiki/en/thiswill404",
            f"{DATA_DIR}/v2/get_wiki_page_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/comments",
            f"{DATA_DIR}/v2/get_comments_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/comments/1",
            f"{DATA_DIR}/v2/get_comment_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/comments/0",
            f"{DATA_DIR}/v2/get_comment_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/search",
            f"{DATA_DIR}/v2/search_200.json",
            params={"query": "peppy"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/me",
            f"{DATA_DIR}/v2/get_me_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/friends",
            f"{DATA_DIR}/v2/get_own_friends_200.json",
            headers={"x-api-version": "20241022"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/peppy",
            f"{DATA_DIR}/v2/get_user_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/thisusernameistoolongtoexistsoitwill404",
            f"{DATA_DIR}/v2/get_user_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users",
            f"{DATA_DIR}/v2/get_users_200.json",
            params={"ids": [7782553, 2]},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7782553/kudosu",
            f"{DATA_DIR}/v2/get_user_kudosu_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/kudosu",
            f"{DATA_DIR}/v2/get_user_kudosu_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/11367222/scores/recent",
            f"{DATA_DIR}/v2/get_user_recents_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/scores/recent",
            f"{DATA_DIR}/v2/get_user_recents_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7782553/scores/best",
            f"{DATA_DIR}/v2/get_user_bests_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/scores/best",
            f"{DATA_DIR}/v2/get_user_bests_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7562902/scores/firsts",
            f"{DATA_DIR}/v2/get_user_firsts_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/scores/firsts",
            f"{DATA_DIR}/v2/get_user_firsts_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7782553/scores/pinned",
            f"{DATA_DIR}/v2/get_user_pinned_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/scores/pinned",
            f"{DATA_DIR}/v2/get_user_pinned_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/2906626/scores/users/4819811/all",
            f"{DATA_DIR}/v2/get_user_beatmap_scores_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/0/scores/users/4819811/all",
            f"{DATA_DIR}/v2/get_user_beatmap_scores_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7782553/beatmapsets/favourite",
            f"{DATA_DIR}/v2/get_user_beatmaps_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/beatmapsets/favourite",
            f"{DATA_DIR}/v2/get_user_beatmaps_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7782553/beatmapsets/most_played",
            f"{DATA_DIR}/v2/get_user_most_played_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/beatmapsets/most_played",
            f"{DATA_DIR}/v2/get_user_most_played_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/7562902/recent_activity",
            f"{DATA_DIR}/v2/get_user_recent_activity_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/users/0/recent_activity",
            f"{DATA_DIR}/v2/get_user_recent_activity_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/events",
            f"{DATA_DIR}/v2/get_events_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/2906626/scores",
            f"{DATA_DIR}/v2/get_beatmap_scores_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/0/scores",
            f"{DATA_DIR}/v2/get_beatmap_scores_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/2906626",
            f"{DATA_DIR}/v2/get_beatmap_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/0",
            f"{DATA_DIR}/v2/get_beatmap_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps",
            f"{DATA_DIR}/v2/get_beatmaps_200.json",
            params={"ids": [2906626, 2395787]},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/lookup",
            f"{DATA_DIR}/v2/lookup_beatmap_200.json",
            params={"id": 2354779},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/lookup",
            f"{DATA_DIR}/v2/lookup_beatmap_404.json",
            expect_status=404,
            params={"id": 0},
        )
        self._register_route(
            "POST",
            f"{BASE_URL}/api/v2/beatmaps/2906626/attributes",
            f"{DATA_DIR}/v2/get_beatmap_attributes_200.json",
        )
        self._register_route(
            "POST",
            f"{BASE_URL}/api/v2/beatmaps/0/attributes",
            f"{DATA_DIR}/v2/get_beatmap_attributes_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/1107500",
            f"{DATA_DIR}/v2/get_beatmapset_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/0",
            f"{DATA_DIR}/v2/get_beatmapset_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/lookup",
            f"{DATA_DIR}/v2/lookup_beatmapset_200.json",
            params={"beatmap_id": 1107500},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/lookup",
            f"{DATA_DIR}/v2/lookup_beatmapset_404.json",
            expect_status=404,
            params={"beatmap_id": 0},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/search",
            f"{DATA_DIR}/v2/search_beatmapsets_200.json",
            params={"q": "doja cat say so"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/packs",
            f"{DATA_DIR}/v2/get_beatmap_packs_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/packs/L1",
            f"{DATA_DIR}/v2/get_beatmap_pack_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmaps/packs/L0",
            f"{DATA_DIR}/v2/get_beatmap_pack_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/events",
            f"{DATA_DIR}/v2/get_beatmapset_events_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/discussions",
            f"{DATA_DIR}/v2/get_beatmapset_discussions_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/discussions/posts",
            f"{DATA_DIR}/v2/get_beatmapset_discussion_posts_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/beatmapsets/discussions/votes",
            f"{DATA_DIR}/v2/get_beatmapset_discussion_votes_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/4220635589",
            f"{DATA_DIR}/v2/get_score_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/4220635589",
            f"{DATA_DIR}/v2/get_score_lazer_200.json",
            headers={"x-api-version": "20220705"},
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/0",
            f"{DATA_DIR}/v2/get_score_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/0",
            f"{DATA_DIR}/v2/get_score_lazer_404.json",
            expect_status=404,
            headers={"x-api-version": "20220705"},
        )
        # Invalid score IDs no longer return a 404 on the download routes;
        # the request stalls until the gateway responds with a 504, so the
        # 504 fixtures are kept in the repository instead of being generated.
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/4220635589/download",
            f"{DATA_DIR}/v2/get_score_replay_200.osr",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/1581778626/download",
            f"{DATA_DIR}/v2/get_score_replay_lazer_200.osr",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rankings/osu/performance",
            f"{DATA_DIR}/v2/get_rankings_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rankings/osu/invalid",
            f"{DATA_DIR}/v2/get_rankings_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rankings/kudosu",
            f"{DATA_DIR}/v2/get_rankings_kudosu_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/spotlights",
            f"{DATA_DIR}/v2/get_spotlights_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/forums/topics/7",
            f"{DATA_DIR}/v2/get_forum_topic_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/forums/topics/0",
            f"{DATA_DIR}/v2/get_forum_topic_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/matches",
            f"{DATA_DIR}/v2/get_multiplayer_matches_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/matches/105019274",
            f"{DATA_DIR}/v2/get_multiplayer_match_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/matches/0",
            f"{DATA_DIR}/v2/get_multiplayer_match_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms",
            f"{DATA_DIR}/v2/get_multiplayer_rooms_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/1",
            f"{DATA_DIR}/v2/get_multiplayer_room_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/0",
            f"{DATA_DIR}/v2/get_multiplayer_room_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/1/leaderboard",
            f"{DATA_DIR}/v2/get_multiplayer_leaderboard_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/0/leaderboard",
            f"{DATA_DIR}/v2/get_multiplayer_leaderboard_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/583093/playlist/5307446/scores",
            f"{DATA_DIR}/v2/get_multiplayer_scores_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/rooms/0/playlist/1/scores",
            f"{DATA_DIR}/v2/get_multiplayer_scores_404.json",
            expect_status=404,
        )
        for mode in API_MODES:
            self._register_route(
                "GET",
                f"{BASE_URL}/api/v2/users/3792472/scores/best",
                f"{DATA_DIR}/v2/score_{mode}.json",
                params={"mode": mode, "limit": 1},
            )

    async def run(self) -> None:
        await self.client._prepare_token()
        self.client._session = aiohttp.ClientSession(
            headers=await self.client._get_headers(),
        )
        try:
            await super().run()

            for mode in API_MODES:
                with open(f"{DATA_DIR}/v2/score_{mode}.json") as f:
                    data = f.read()
                    data_json = orjson.loads(data)
                    for score in data_json:
                        await self._save_data(
                            "POST",
                            f"{BASE_URL}/api/v2/beatmaps/{score['beatmap']['id']}/attributes",
                            f"{DATA_DIR}/v2/difficulty_attributes_{mode}.json",
                            200,
                            params={"ruleset_id": score["mode_int"]},
                        )
        finally:
            await self.client.aclose()


class TestGeneratorDev(TestGeneratorBase):
    """Generates data for endpoints that mutate state, against https://dev.ppy.sh."""

    def __init__(self, token: aiosu.models.OAuthToken) -> None:
        super().__init__()

        self.client = aiosu.v2.Client(token=token, base_url=BASE_URL_DEV)
        self._ensure_dir(f"{DATA_DIR}/v2")

    def _register_routes(self) -> None:
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/forums/topics",
            f"{DATA_DIR}/v2/create_forum_topic_200.json",
            data={"title": "Test topic", "body": "Test body", "forum_id": 74},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/forums/topics/515/reply",
            f"{DATA_DIR}/v2/reply_forum_topic_200.json",
            data={"body": "Test body"},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/forums/topics/515",
            f"{DATA_DIR}/v2/edit_forum_topic_title_200.json",
            data={"forum_topic": {"topic_title": "Test topic"}},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/forums/posts/638",
            f"{DATA_DIR}/v2/edit_forum_post_200.json",
            data={"body": "Test body"},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/ack",
            f"{DATA_DIR}/v2/get_chat_ack_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels/5",
            f"{DATA_DIR}/v2/get_channel_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels/0",
            f"{DATA_DIR}/v2/get_channel_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels",
            f"{DATA_DIR}/v2/get_channels_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels/5/messages",
            f"{DATA_DIR}/v2/get_channel_messages_200.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels/0/messages",
            f"{DATA_DIR}/v2/get_channel_messages_404.json",
            expect_status=404,
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/channels",
            f"{DATA_DIR}/v2/create_chat_channel_200.json",
            data={"type": "PM", "message": "Test", "target_id": 665},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/chat/channels/6/users/664",
            f"{DATA_DIR}/v2/join_channel_200.json",
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/channels/5/messages",
            f"{DATA_DIR}/v2/send_message_200.json",
            data={"message": "Test"},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/new",
            f"{DATA_DIR}/v2/send_private_message_200.json",
            data={"message": "Test", "target_id": 665},
        )

    async def run(self) -> None:
        await self.client._prepare_token()
        self.client._session = aiohttp.ClientSession(
            headers=await self.client._get_headers(),
        )
        try:
            await super().run()
        finally:
            await self.client.aclose()


async def main() -> None:
    load_dotenv()

    api_key = os.environ.get("OSU_API_KEY", "")
    generator_v1 = TestGeneratorV1(api_key=api_key)
    await generator_v1.run()

    token = await get_token("OSU_", BASE_URL)
    generator_v2 = TestGeneratorV2(token=token)
    await generator_v2.run()

    if os.environ.get("OSU_DEV_ACCESS_TOKEN") or os.environ.get("OSU_DEV_CLIENT_ID"):
        dev_token = await get_token("OSU_DEV_", BASE_URL_DEV)
        generator_dev = TestGeneratorDev(token=dev_token)
        await generator_dev.run()
    else:
        logger.info(
            "Skipping dev endpoints: set OSU_DEV_CLIENT_ID and OSU_DEV_CLIENT_SECRET "
            "(or OSU_DEV_ACCESS_TOKEN) to generate them",
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except ValueError as e:
        logger.error(f"Error while generating test data: {e}")
        sys.exit(1)
