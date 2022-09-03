from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from emojiflags.lookup import lookup as flag_lookup


@dataclass
class TimestampedCount:
    start_date: datetime
    count: int


@dataclass
class Achievement:
    achieved_at: datetime
    achievement_id: int


@dataclass
class Country:
    code: str
    name: str

    @property
    def flag_emoji(self) -> str:
        return flag_lookup(self.code)
