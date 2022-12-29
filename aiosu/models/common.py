"""
This module contains models for miscellaneous objects.
"""
from __future__ import annotations

from datetime import datetime

from emojiflags.lookup import lookup as flag_lookup  # type: ignore
from pydantic import validator

from .base import BaseModel


class TimestampedCount(BaseModel):
    start_date: datetime
    count: int

    @validator("start_date", pre=True)
    def _date_validate(cls, v: str) -> datetime:
        return datetime.strptime(v, "%Y-%m-%d")


class Achievement(BaseModel):
    achieved_at: datetime
    achievement_id: int


class Country(BaseModel):
    code: str
    name: str

    @property
    def flag_emoji(self) -> str:
        """Emoji for the flag.

        :return: Unicode emoji representation of the country's flag
        :rtype: str
        """
        return flag_lookup(self.code)
