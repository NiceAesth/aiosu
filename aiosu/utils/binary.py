"""
This module contains functions for reading and writing binary data.
"""

from __future__ import annotations

import lzma
import struct
from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    from typing import BinaryIO

_lzma_format = lzma.FORMAT_ALONE

__all__ = (
    "pack",
    "pack_byte",
    "pack_float16",
    "pack_float32",
    "pack_float64",
    "pack_int",
    "pack_long",
    "pack_replay_data",
    "pack_short",
    "pack_string",
    "pack_timestamp",
    "pack_uleb128",
    "unpack",
    "unpack_byte",
    "unpack_float16",
    "unpack_float32",
    "unpack_float64",
    "unpack_int",
    "unpack_long",
    "unpack_replay_data",
    "unpack_short",
    "unpack_string",
    "unpack_timestamp",
    "unpack_uleb128",
)


def unpack(file: BinaryIO, fmt: str) -> int:
    r"""Unpack a value from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :param fmt: The format to unpack.
    :type fmt: str
    :return: The unpacked value.
    :rtype: int
    """
    return struct.unpack(fmt, file.read(struct.calcsize(fmt)))[0]


def unpack_byte(file: BinaryIO) -> int:
    r"""Unpack a byte from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked byte.
    :rtype: int
    """
    return unpack(file, "<b")


def unpack_short(file: BinaryIO) -> int:
    r"""Unpack a short from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked short.
    :rtype: int
    """
    return unpack(file, "<h")


def unpack_int(file: BinaryIO) -> int:
    r"""Unpack an integer from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked integer.
    :rtype: int
    """
    return unpack(file, "<i")


def unpack_long(file: BinaryIO) -> int:
    r"""Unpack a long from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked long.
    :rtype: int
    """
    return unpack(file, "q")


def unpack_float16(file: BinaryIO) -> float:
    r"""Unpack a float16 from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked float16.
    :rtype: float
    """
    return unpack(file, "<e")


def unpack_float32(file: BinaryIO) -> float:
    r"""Unpack a float32 from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked float32.
    :rtype: float
    """
    return unpack(file, "<f")


def unpack_float64(file: BinaryIO) -> float:
    r"""Unpack a float64 from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked float64.
    :rtype: float
    """
    return unpack(file, "<d")


def unpack_timestamp(file: BinaryIO) -> datetime:
    r"""Unpack a timestamp from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked timestamp.
    :rtype: datetime
    """
    seconds = unpack_long(file) // 10000000 - 62135596800
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def unpack_uleb128(file: BinaryIO) -> int:
    r"""Unpack a ULEB128 from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked ULEB128.
    :rtype: int
    """
    result = 0
    shift = 0
    while True:
        byte = unpack_byte(file)
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            break
        shift += 7
    return result


def unpack_string(file: BinaryIO) -> str:
    r"""Unpack a string from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The unpacked string.
    :rtype: str
    """
    fb = file.read(1)
    if fb == b"\x00":
        return ""
    length = unpack_uleb128(file)
    return file.read(length).decode("utf-8")


def unpack_replay_data(file: BinaryIO) -> str:
    r"""Unpack the replay data from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The replay event data.
    :rtype: str
    """
    length = unpack_int(file)
    if length == 0:
        return ""
    data = file.read(length)
    data = lzma.decompress(data)
    return data.decode("ascii")


def pack(file: BinaryIO, fmt: str, value: object) -> None:
    r"""Pack a value into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param fmt: The format to pack with.
    :type fmt: str
    :param value: The value to pack.
    :type value: object
    """
    file.write(struct.pack(fmt, value))


def pack_byte(file: BinaryIO, value: int) -> None:
    r"""Pack a byte into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<b", value)


def pack_short(file: BinaryIO, value: int) -> None:
    r"""Pack a short into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<h", value)


def pack_int(file: BinaryIO, value: int) -> None:
    r"""Pack an integer into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<i", value)


def pack_long(file: BinaryIO, value: int) -> None:
    r"""Pack a long into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<q", value)


def pack_float16(file: BinaryIO, value: float) -> None:
    r"""Pack a float16 into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: float
    """
    pack(file, "<e", value)


def pack_float32(file: BinaryIO, value: float) -> None:
    r"""Pack a float32 into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: float
    """
    pack(file, "<f", value)


def pack_float64(file: BinaryIO, value: float) -> None:
    r"""Pack a float64 into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: float
    """
    pack(file, "<d", value)


def pack_timestamp(file: BinaryIO, value: datetime) -> None:
    r"""Pack a timestamp into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: datetime
    """
    seconds = (value.timestamp() + 62135596800) * 10000000
    pack_long(file, int(seconds))


def pack_uleb128(file: BinaryIO, value: int) -> None:
    r"""Pack a ULEB128 into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        pack_byte(file, byte)
        if not value:
            break


def pack_string(file: BinaryIO, value: Union[bytes, str]) -> None:
    r"""Pack a string into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: Union[bytes, str]
    """
    pack_byte(file, 11)
    if not value:
        file.write(b"\x00")
        return
    pack_uleb128(file, len(value))
    file.write(value.encode("utf-8") if isinstance(value, str) else value)


def pack_replay_data(file: BinaryIO, data: str) -> None:
    r"""Pack the replay data into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param data: The data to pack.
    :type data: str
    """
    encoded_data = data.encode("ascii")
    compressed = lzma.compress(encoded_data, format=_lzma_format)
    pack_int(file, len(compressed))
    file.write(compressed)
