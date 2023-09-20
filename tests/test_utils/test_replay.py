from __future__ import annotations

from io import BytesIO

import pytest

import aiosu

modes = ["osu", "mania", "fruits", "taiko", "lazer"]


@pytest.fixture
def replay_file(mode="osu"):
    def _replay_file(mode=mode):
        with open(f"tests/data/replay_{mode}.osr", "rb") as f:
            data = f.read()
        return data

    return _replay_file


def test_parse_replay(replay_file):
    for mode in modes:
        with BytesIO(replay_file(mode)) as data:
            replay = aiosu.utils.replay.parse_file(data)
            assert isinstance(replay, aiosu.models.ReplayFile)


def test_write_replay(replay_file):
    for mode in modes:
        with BytesIO(replay_file(mode)) as data:
            replay = aiosu.utils.replay.parse_file(data)
            with BytesIO() as f:
                aiosu.utils.replay.write_replay(f, replay)
                f.seek(0)
                new_replay = aiosu.utils.replay.parse_file(f)
                assert replay == new_replay
