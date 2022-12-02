from __future__ import annotations

import datetime

from .models import BaseModel


class OAuthToken(BaseModel):
    token_type: str = "Bearer"
    access_token: str = ""
    refresh_token: str = ""
    expires_on: datetime.datetime = datetime.datetime.utcfromtimestamp(0)
