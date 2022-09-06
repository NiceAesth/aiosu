from __future__ import annotations

import datetime

from .models import BaseModel


class OAuthToken(BaseModel):
    access_token: str = None
    refresh_token: str = None
    expires_on: datetime.datetime = datetime.datetime.utcfromtimestamp(0)
