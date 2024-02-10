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
STATUS_CAN_200_TEXT = {
    200: "text/plain",
}
STATUS_CAN_404 = {
    200: "application/json",
    404: "application/json",
}


def get_data(func_name: str, status_code: int, extension: str = "json") -> bytes:
    with open(f"tests/data/v1/{func_name}_{status_code}.{extension}", "rb") as f:
        data = f.read()
        return data


def generate_test(
    func,
    status_codes: Mapping[int, str],
    func_kwargs: Mapping[str, object] = {},
):
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code, content_type", status_codes.items())
    async def test_generated(status_code, content_type, mocker):
        async with aiosu.v1.Client(token="") as client:
            file_extension = "json"
            if content_type == "text/plain":
                file_extension = "osu"
            data = get_data(func.__name__, status_code, file_extension)
            resp = mock_request(status_code, content_type, data)
            mocker.patch(
                "aiosu.v1.Client._request",
                wraps=resp,
            )
            if status_code == 200:
                data = await func(client, **func_kwargs)
            else:
                with pytest.raises(aiosu.exceptions.APIException):
                    data = await func(client, **func_kwargs)

    test_generated.__name__ = f"test_{func.__name__}"
    return test_generated


tests = [
    generate_test(
        aiosu.v1.Client.get_beatmap,
        STATUS_CAN_200,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v1.Client.get_beatmap_scores,
        STATUS_CAN_200,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v1.Client.get_beatmap_osu,
        STATUS_CAN_200_TEXT,
        func_kwargs={"beatmap_id": 2906626},
    ),
    generate_test(
        aiosu.v1.Client.get_user,
        STATUS_CAN_200,
        func_kwargs={"user_query": "peppy"},
    ),
    generate_test(
        aiosu.v1.Client.get_user_recents,
        STATUS_CAN_200,
        func_kwargs={"user_query": 7562902},
    ),
    generate_test(
        aiosu.v1.Client.get_user_bests,
        STATUS_CAN_200,
        func_kwargs={"user_query": 7782553},
    ),
    generate_test(
        aiosu.v1.Client.get_match,
        STATUS_CAN_200,
        func_kwargs={"match_id": 105019274},
    ),
    generate_test(
        aiosu.v1.Client.get_replay,
        STATUS_CAN_200,
        func_kwargs={"mode": "osu", "beatmap_id": 2906626, "user_query": 4819811},
    ),
]

for test_func in tests:
    globals()[test_func.__name__] = test_func
