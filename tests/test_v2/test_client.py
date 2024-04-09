from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import aiosu

from ..classes import mock_request

if TYPE_CHECKING:
    from collections.abc import Mapping

STATUS_CAN_200 = {
    200: "application/json",
}
STATUS_CAN_404 = {
    200: "application/json",
    404: "application/json",
}
STATUS_CAN_404_HTML = {
    200: "application/json",
    404: "text/html",
}
STATUS_CAN_404_OCTET = {
    200: "application/octet-stream",
    404: "application/json",
}


@pytest.fixture(autouse=True)
def token():
    token = aiosu.models.OAuthToken(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiZnJpZW5kcy5yZWFkIiwiaWRlbnRpZnkiLCJwdWJsaWMiXX0.dps4hJ4HwjQ7scacQRBHs1FN0tcGPfYPCUxQjt6ueEo4Q-G-BmkJSGQo6dDhXD1WnXFJdW14prl_fzjvBi7U-9Y7AcLHSMRSbmRa2uS7KciZv7vHpS6Cs64uZO1WqBpOswZJtCfjBeimSrvU9O_zezg3cujrhNTCwbsBOaK1mR9YtxXhw4Y6ORLKqS9ahF1FyXBIZ3pSFBFOxbAtIIDwtZq9CDbffqQrVL7MiNojPBVmhReomf2pSyNM0UIA5u7pCXQOsb4VvmhSPGj7HPoORNyc6CM1iwcmGsrEPDL3d1ZtNtYyiLtarvUZx1WUau9GDAs-AtJ9XaypJTqUjfya7g",
        refresh_token="hi",
        expires_in=86400,
    )
    return token


def get_data(func_name: str, status_code: int, extension: str = "json") -> bytes:
    with open(f"tests/data/v2/{func_name}_{status_code}.{extension}", "rb") as f:
        data = f.read()
        return data


def generate_test(
    func,
    status_codes: Mapping[int, str],
    func_kwargs: Mapping = {},
):
    data_name = func.__name__
    if func_kwargs.get("new_format"):
        data_name = f"{func.__name__}_lazer"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code, content_type", status_codes.items())
    async def test_generated(status_code, content_type, token, mocker):
        async with aiosu.v2.Client(token=token) as client:
            file_extension = "json"
            if content_type == "application/octet-stream":
                file_extension = "osr"
            data = get_data(data_name, status_code, file_extension)
            resp = mock_request(status_code, content_type, data)
            mocker.patch(
                "aiosu.v2.Client._request",
                wraps=resp,
            )
            if status_code == 200:
                data = await func(client, **func_kwargs)
            else:
                with pytest.raises(aiosu.exceptions.APIException):
                    data = await func(client, **func_kwargs)

    test_generated.__name__ = f"test_{data_name}"
    return test_generated


tests = [
    generate_test(aiosu.v2.Client.get_featured_tracks, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_seasonal_backgrounds, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_changelog_listing, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_changelog_build,
        STATUS_CAN_404,
        func_kwargs={"stream": "lazer", "build": "2023.815.0"},
    ),
    generate_test(
        aiosu.v2.Client.lookup_changelog_build,
        STATUS_CAN_404,
        func_kwargs={"changelog_query": "lazer"},
    ),
    generate_test(aiosu.v2.Client.get_news_listing, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_news_post,
        STATUS_CAN_404,
        func_kwargs={"news_query": 1},
    ),
    generate_test(
        aiosu.v2.Client.get_wiki_page,
        STATUS_CAN_404_HTML,
        func_kwargs={"locale": "en", "path": "Main_page"},
    ),
    generate_test(aiosu.v2.Client.get_comments, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_comment,
        STATUS_CAN_404,
        func_kwargs={"comment_id": 1},
    ),
    generate_test(
        aiosu.v2.Client.search,
        STATUS_CAN_200,
        func_kwargs={"query": "peppy"},
    ),
    generate_test(
        aiosu.v2.Client.get_me,
        STATUS_CAN_200,
    ),
    generate_test(
        aiosu.v2.Client.get_own_friends,
        STATUS_CAN_200,
    ),
    generate_test(
        aiosu.v2.Client.get_user,
        STATUS_CAN_404,
        func_kwargs={"user_query": 1},
    ),
    generate_test(
        aiosu.v2.Client.get_users,
        STATUS_CAN_200,
        func_kwargs={"user_ids": [7782553, 2]},
    ),
    generate_test(
        aiosu.v2.Client.get_user_kudosu,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_recents,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_bests,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_firsts,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_pinned,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_beatmap_scores,
        STATUS_CAN_404,
        func_kwargs={"user_id": 4819811, "beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v2.Client.get_user_beatmaps,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553, "type": "favourite"},
    ),
    generate_test(
        aiosu.v2.Client.get_user_most_played,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(
        aiosu.v2.Client.get_user_recent_activity,
        STATUS_CAN_404,
        func_kwargs={"user_id": 7782553},
    ),
    generate_test(aiosu.v2.Client.get_events, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_beatmap_scores,
        STATUS_CAN_404,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v2.Client.get_beatmap,
        STATUS_CAN_404,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v2.Client.get_beatmaps,
        STATUS_CAN_200,
        func_kwargs={"beatmap_ids": [2906626, 2395787]},
    ),
    generate_test(
        aiosu.v2.Client.lookup_beatmap,
        STATUS_CAN_404,
        func_kwargs={"id": 2906626},
    ),
    generate_test(
        aiosu.v2.Client.get_beatmap_attributes,
        STATUS_CAN_404,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v2.Client.get_beatmapset,
        STATUS_CAN_404,
        func_kwargs={"beatmapset_id": 1107500},
    ),
    generate_test(
        aiosu.v2.Client.lookup_beatmapset,
        STATUS_CAN_404,
        func_kwargs={"beatmap_id": 1107500},
    ),
    generate_test(
        aiosu.v2.Client.search_beatmapsets,
        STATUS_CAN_200,
        func_kwargs={"query": "doja cat say so"},
    ),
    generate_test(aiosu.v2.Client.get_beatmap_packs, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_beatmap_pack,
        STATUS_CAN_404,
        func_kwargs={"pack_tag": "L1"},
    ),
    generate_test(aiosu.v2.Client.get_beatmapset_events, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_beatmapset_discussions, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_beatmapset_discussion_posts, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_beatmapset_discussion_votes, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_score,
        STATUS_CAN_404,
        func_kwargs={"score_id": 4220635589, "mode": "osu"},
    ),
    generate_test(
        aiosu.v2.Client.get_score,
        STATUS_CAN_404,
        func_kwargs={"score_id": 4220635589, "mode": "osu", "new_format": True},
    ),
    generate_test(
        aiosu.v2.Client.get_score_replay,
        STATUS_CAN_404_OCTET,
        func_kwargs={"score_id": 4220635589, "mode": "osu"},
    ),
    generate_test(
        aiosu.v2.Client.get_rankings,
        STATUS_CAN_404,
        func_kwargs={"mode": "osu", "type": "performance"},
    ),
    generate_test(aiosu.v2.Client.get_rankings_kudosu, STATUS_CAN_200),
    generate_test(aiosu.v2.Client.get_spotlights, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_forum_topic,
        STATUS_CAN_404,
        func_kwargs={"topic_id": 7},
    ),
    generate_test(aiosu.v2.Client.get_multiplayer_matches, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_multiplayer_match,
        STATUS_CAN_404,
        func_kwargs={"match_id": 105019274},
    ),
    generate_test(aiosu.v2.Client.get_multiplayer_rooms, STATUS_CAN_200),
    generate_test(
        aiosu.v2.Client.get_multiplayer_room,
        STATUS_CAN_404,
        func_kwargs={"room_id": 1},
    ),
    generate_test(
        aiosu.v2.Client.get_multiplayer_leaderboard,
        STATUS_CAN_404,
        func_kwargs={"room_id": 1},
    ),
    generate_test(
        aiosu.v2.Client.get_multiplayer_scores,
        STATUS_CAN_404,
        func_kwargs={"room_id": 583093, "playlist_id": 5307446},
    ),
]

for test_func in tests:
    globals()[test_func.__name__] = test_func
