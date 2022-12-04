"""
This module contains models for API v2 token objects.
"""
from __future__ import annotations

import datetime
from typing import Any

from pydantic import root_validator

from .models import BaseModel


class OAuthToken(BaseModel):
    token_type: str = "Bearer"
    """Defaults to 'Bearer'"""
    access_token: str = ""
    refresh_token: str = ""
    expires_on: datetime.datetime = datetime.datetime.utcfromtimestamp(0)
    """Can be a datetime.datetime object or a string. Alternatively, expires_in may be passed representing the number of seconds the token will be valid for."""

    @root_validator(pre=True)
    def _set_expires_on(cls, values: dict[str, Any]) -> dict[str, Any]:
        if isinstance(values.get("expires_in"), int):
            values["expires_on"] = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=values["expires_in"],
            )
        return values
