from __future__ import annotations

import datetime

from .models import BaseModel
from .user import User


class Background(BaseModel):
    url: str
    user: User


class SeasonalBackgroundSet(BaseModel):
    ends_at: datetime.datetime
    backgrounds: list[Background]
