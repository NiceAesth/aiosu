from __future__ import annotations

from ..base import BaseModel


class Replay(BaseModel):
    """Replay API object."""

    content: str  # test
    """Encoded LZMA data of the replay"""
    encoding: str
    """The encoding used"""
