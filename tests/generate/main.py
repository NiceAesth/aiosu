"""
This module is used to generate test data for aiosu tests from the osu! API.
"""
from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC
from abc import abstractmethod
from functools import partial
from typing import Optional

import aiohttp
import orjson
from dotenv import load_dotenv

import aiosu


API_MODES = ["osu", "taiko", "fruits", "mania"]
BASE_URL = "https://osu.ppy.sh"
BASE_URL_LAZER = "https://lazer.ppy.sh"
BASE_URL_DEV = "https://dev.ppy.sh"
DATA_DIR = "../data"

logger = logging.getLogger("aiosu")


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
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
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
    def _register_routes(self) -> None:
        ...

    def _ensure_dir(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path)

    async def _save_data(
        self,
        method: str,
        url: str,
        filename: str,
        expect_status: int,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> None:
        async with self.client._session.request(
            method,
            url,
            data=data,
            params=params,
            headers=headers,
        ) as resp:
            if resp.status != expect_status:
                raise ValueError(
                    f"Expected {method} {url} to return {expect_status}, got {resp.status}",
                )

            resp_data = await resp.read()
            with open(filename, "wb") as f:
                f.write(resp_data)

    async def run(self) -> None:
        self._register_routes()
        for route in self.routes:
            logger.info(f"Running {route}")
            try:
                await route()
            except ValueError as e:
                logger.error(f"Error while running {route}: {e}")
                exit(1)


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
            params=self._default_params | {"u": "mrekk"},
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
        await super().run()
        await self.client.close()


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
            f"{BASE_URL}/api/v2/users/7562902/scores/recent",
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
            f"{BASE_URL}/api/v2/beatmapsets/search/doja cat say so",
            f"{DATA_DIR}/v2/search_beatmapsets_200.json",
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
            f"{BASE_URL}/api/v2/scores/osu/0",
            f"{DATA_DIR}/v2/get_score_404.json",
            expect_status=404,
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/4220635589/download",
            f"{DATA_DIR}/v2/get_score_replay_200.osr",
        )
        self._register_route(
            "GET",
            f"{BASE_URL}/api/v2/scores/osu/0/download",
            f"{DATA_DIR}/v2/get_score_replay_404.json",
            expect_status=404,
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
        """
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/forums/topics",
            f"{DATA_DIR}/v2/create_forum_topic_200.json",
            data={"title": "Test topic", "body": "Test body", "forum_id": 7},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/forums/topics/7/reply",
            f"{DATA_DIR}/v2/reply_forum_topic_200.json",
            data={"body": "Test body"},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/forums/topics/7/title",
            f"{DATA_DIR}/v2/edit_forum_topic_title_200.json",
            data={"title": "Test topic"},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/forums/posts/7",
            f"{DATA_DIR}/v2/edit_forum_post_200.json",
            data={"body": "Test body"},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/ack",
            f"{DATA_DIR}/v2/get_chat_ack.json",
        )
        self._register_route(
            "GET",
            f"{BASE_URL_DEV}/api/v2/chat/channels/1",
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
            f"{BASE_URL_DEV}/api/v2/chat/channels/1/messages",
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
            data={"message": "Test", "target_id": 664},
        )
        self._register_route(
            "PUT",
            f"{BASE_URL_DEV}/api/v2/chat/channels/1/users/665",
            f"{DATA_DIR}/v2/join_channel_200.json",
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/channels/1/messages",
            f"{DATA_DIR}/v2/send_message_200.json",
            data={"message": "Test"},
        )
        self._register_route(
            "POST",
            f"{BASE_URL_DEV}/api/v2/chat/chat/new",
            f"{DATA_DIR}/v2/send_private_message_200.json",
            data={"message": "Test", "target_id": 664},
        )
        """
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
            f"{BASE_URL}/api/v2/rooms/1/playlist/1/scores",
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

        await self.client.close()


async def main() -> None:
    load_dotenv()

    api_key = os.environ.get("OSU_API_KEY", "")
    generator_v1 = TestGeneratorV1(api_key=api_key)
    await generator_v1.run()

    token = aiosu.models.OAuthToken(
        access_token=os.environ.get("OSU_ACCESS_TOKEN", ""),
        refresh_token="",
        expires_in=86400,
    )
    generator_v2 = TestGeneratorV2(token=token)
    await generator_v2.run()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
