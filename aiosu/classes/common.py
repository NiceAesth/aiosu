from __future__ import annotations

import datetime

from emojiflags.lookup import lookup as flag_lookup
from pydantic import validator

from .models import BaseModel


class TimestampedCount(BaseModel):
    start_date: datetime.datetime
    count: int

    @validator("start_date", pre=True)
    def date_validate(cls, v):
        return datetime.datetime.strptime(v, "%Y-%m-%d")


class Achievement(BaseModel):
    achieved_at: datetime.datetime
    achievement_id: int


class Country(BaseModel):
    code: str
    name: str

    @property
    def flag_emoji(self) -> str:
        return flag_lookup(self.code)
