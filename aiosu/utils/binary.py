"""
This module contains functions for reading and writing binary data.
"""
from __future__ import annotations

import lzma
import struct
from datetime import datetime
from typing import BinaryIO


def unpack(file: BinaryIO, fmt: str) -> int:
    """Unpack a value from a file."""
    return struct.unpack(fmt, file.read(struct.calcsize(fmt)))[0]


def unpack_byte(file: BinaryIO) -> int:
    """Unpack a byte from a file."""
    return unpack(file, "<b")


def unpack_short(file: BinaryIO) -> int:
    """Unpack a short from a file."""
    return unpack(file, "<h")


def unpack_int(file: BinaryIO) -> int:
    """Unpack an integer from a file."""
    return unpack(file, "<i")


def unpack_long(file: BinaryIO) -> int:
    """Unpack a long from a file."""
    return unpack(file, "q")


def unpack_timestamp(file: BinaryIO) -> datetime:
    """Unpack a timestamp from a file."""
    seconds = unpack_long(file) / 10000000 - 62135596800
    return datetime.utcfromtimestamp(seconds)


def unpack_uleb128(file: BinaryIO) -> int:
    """Unpack a ULEB128 from a file."""
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
    """Unpack a string from a file."""
    fb = file.read(1)
    if fb == b"\x00":
        return ""
    length = unpack_uleb128(file)
    return file.read(length).decode("utf-8")


def unpack_replay_data(file: BinaryIO) -> str:
    """Unpack the replay data from a file.

    :param file: The file to unpack from.
    :type file: BinaryIO
    :return: The replay event data.
    :rtype: str
    """
    length = unpack_int(file)
    data = file.read(length)
    data = lzma.decompress(data)
    return data.decode("ascii")


def pack(file: BinaryIO, fmt: str, value: int) -> None:
    """Pack a value into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param fmt: The format to pack with.
    :type fmt: str
    :param value: The value to pack.
    :type value: int
    """
    file.write(struct.pack(fmt, value))


def pack_byte(file: BinaryIO, value: int) -> None:
    """Pack a byte into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<b", value)


def pack_short(file: BinaryIO, value: int) -> None:
    """Pack a short into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<h", value)


def pack_int(file: BinaryIO, value: int) -> None:
    """Pack an integer into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "<i", value)


def pack_long(file: BinaryIO, value: int) -> None:
    """Pack a long into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: int
    """
    pack(file, "q", value)


def pack_timestamp(file: BinaryIO, value: datetime) -> None:
    """Pack a timestamp into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: datetime
    """
    seconds = int(value.timestamp()) + 62135596800
    pack_long(file, seconds * 10000000)


def pack_uleb128(file: BinaryIO, value: int) -> None:
    """Pack a ULEB128 into a file.

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


def pack_string(file: BinaryIO, value: str) -> None:
    """Pack a string into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param value: The value to pack.
    :type value: str
    """
    if not value:
        file.write(b"\x00")
        return
    pack_uleb128(file, len(value))
    file.write(value.encode("utf-8"))


def pack_replay_data(file: BinaryIO, data: str) -> None:
    """Pack the replay data into a file.

    :param file: The file to pack into.
    :type file: BinaryIO
    :param data: The data to pack.
    :type data: str
    """
    encoded_data = data.encode("ascii")
    compressed = lzma.compress(encoded_data)
    pack_int(file, len(compressed))
    file.write(compressed)
