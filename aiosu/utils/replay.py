"""
This module contains functions to parse replay files.
"""
from __future__ import annotations

from typing import Any
from typing import BinaryIO

from ..models import ReplayFile
from ..models.files.replay import ReplayEvent
from ..models.files.replay import ReplayKey
from ..models.files.replay import ReplayLifebarEvent
from ..models.lazer import LazerReplayData
from ..models.mods import Mod
from .binary import pack_byte
from .binary import pack_float64
from .binary import pack_int
from .binary import pack_long
from .binary import pack_replay_data
from .binary import pack_short
from .binary import pack_string
from .binary import pack_timestamp
from .binary import unpack_byte
from .binary import unpack_float64
from .binary import unpack_int
from .binary import unpack_long
from .binary import unpack_replay_data
from .binary import unpack_short
from .binary import unpack_string
from .binary import unpack_timestamp


__all__ = (
    "parse_file",
    "parse_path",
    "write_replay",
    "write_path",
)


def _parse_replay_data(data: str) -> list[ReplayEvent]:
    """Parse replay event data and return a list of replay events."""
    events: list[ReplayEvent] = []
    for event in data.split(","):
        if event == "":
            continue
        event_data: list[str] = event.split("|")
        time: int = int(event_data[0])
        x: float = float(event_data[1])
        y: float = float(event_data[2])
        keys: ReplayKey = ReplayKey(int(event_data[3]))
        events.append(ReplayEvent(time=time, keys=keys, x=x, y=y))
    return events


def _parse_life_graph_data(data: str) -> list[ReplayLifebarEvent]:
    """Parse life bar data and return a list of life bar events."""
    events: list[ReplayLifebarEvent] = []
    for event in data.split(","):
        if event == "":
            continue
        event_data: list[str] = event.split("|")
        time: int = int(event_data[0])
        hp: float = float(event_data[1])
        events.append(ReplayLifebarEvent(time=time, hp=hp))
    return events


def parse_file(file: BinaryIO) -> ReplayFile:
    """Parse a replay file and return a dictionary with the replay data.

    :param file: The replay file.
    :type file: BinaryIO
    :return: The replay data.
    :rtype: Replay
    """
    replay: dict[str, Any] = {}
    statistics: dict[str, int] = {}
    replay["mode"] = unpack_byte(file)
    replay["version"] = unpack_int(file)
    replay["map_md5"] = unpack_string(file)
    replay["player_name"] = unpack_string(file)
    replay["replay_md5"] = unpack_string(file)
    statistics["count_300"] = unpack_short(file)
    statistics["count_100"] = unpack_short(file)
    statistics["count_50"] = unpack_short(file)
    statistics["count_geki"] = unpack_short(file)
    statistics["count_katu"] = unpack_short(file)
    statistics["count_miss"] = unpack_short(file)
    replay["statistics"] = statistics
    replay["score"] = unpack_int(file)
    replay["max_combo"] = unpack_short(file)
    replay["perfect_combo"] = unpack_byte(file)
    replay["mods"] = unpack_int(file)
    lifebar_data_str = unpack_string(file)
    replay["lifebar_data"] = _parse_life_graph_data(lifebar_data_str)
    replay["played_at"] = unpack_timestamp(file)
    replay_data_str = unpack_replay_data(file)
    replay["replay_data"] = _parse_replay_data(replay_data_str)
    if replay["version"] >= 20140721:
        replay["online_id"] = unpack_long(file)
    elif replay["version"] >= 20121008:
        replay["online_id"] = unpack_int(file)
    if Mod.Target & replay["mods"]:
        replay["mod_extras"] = unpack_float64(file)
    if replay["version"] >= 30000001:
        lazer_replay_data_str = unpack_replay_data(file)
        replay["lazer_replay_data"] = LazerReplayData.model_validate_json(
            lazer_replay_data_str,
        )
    return ReplayFile(**replay)


def parse_path(path: str) -> ReplayFile:
    """Parse a replay file and return a dictionary with the replay data.

    :param path: The path to the replay file.
    :type path: str
    :return: The replay data.
    :rtype: Replay
    """
    with open(path, "rb") as file:
        return parse_file(file)


def write_replay(file: BinaryIO, replay: ReplayFile) -> None:
    """Write a replay to a file.

    :param file: The file to write to.
    :type file: BinaryIO
    :param replay: The replay to write.
    :type replay: Replay
    """
    pack_byte(file, int(replay.mode))
    pack_int(file, replay.version)
    pack_string(file, replay.map_md5)
    pack_string(file, replay.player_name)
    pack_string(file, replay.replay_md5)
    pack_short(file, replay.statistics.count_300)
    pack_short(file, replay.statistics.count_100)
    pack_short(file, replay.statistics.count_50)
    pack_short(file, replay.statistics.count_geki)
    pack_short(file, replay.statistics.count_katu)
    pack_short(file, replay.statistics.count_miss)
    pack_int(file, replay.score)
    pack_short(file, replay.max_combo)
    pack_byte(file, replay.perfect_combo)
    pack_int(file, int(replay.mods))
    pack_string(
        file,
        ",".join(
            [f"{event.time}|{event.hp}" for event in replay.lifebar_data],
        ),
    )
    pack_timestamp(file, replay.played_at)
    pack_replay_data(
        file,
        ",".join(
            [
                f"{event.time}|{event.x}|{event.y}|{event.keys}"
                for event in replay.replay_data
            ],
        ),
    )
    if replay.version >= 2014_07_21:
        pack_long(file, replay.online_id)
    elif replay.version >= 2012_10_08:
        pack_int(file, replay.online_id)
    if replay.mod_extras is not None:
        pack_float64(file, replay.mod_extras)
    if replay.lazer_replay_data is not None:
        pack_replay_data(
            file,
            replay.lazer_replay_data.model_dump_json(
                exclude_unset=True,
                exclude_none=True,
            ),
        )


def write_path(path: str, replay: ReplayFile) -> None:
    """Write a replay to a file.

    :param path: The path to the file to write to.
    :type path: str
    :param replay: The replay to write.
    :type replay: Replay
    """
    with open(path, "wb") as file:
        write_replay(file, replay)
