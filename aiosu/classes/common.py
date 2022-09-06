from __future__ import annotations

import datetime

from emojiflags.lookup import lookup as flag_lookup

from .models import BaseModel


class TimestampedCount(BaseModel):
    start_date: datetime.datetime
    count: int


class Achievement(BaseModel):
    achieved_at: datetime.datetime
    achievement_id: int


class Country(BaseModel):
    code: str
    name: str

    @property
    def flag_emoji(self) -> str:
        return flag_lookup(self.code)
