"""
This module contains models for API v2 token objects.
"""
from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from pydantic import root_validator

from .base import BaseModel
from .scopes import Scopes

if TYPE_CHECKING:
    from typing import Any


class OAuthToken(BaseModel):
    token_type: str = "Bearer"
    """Defaults to 'Bearer'"""
    access_token: str = ""
    refresh_token: str = ""
    expires_on: datetime = datetime.utcfromtimestamp(0)
    scopes: Scopes = Scopes.PUBLIC | Scopes.IDENTIFY
    """Can be a datetime.datetime object or a string. Alternatively, expires_in may be passed representing the number of seconds the token will be valid for."""

    @root_validator(pre=True)
    def _set_expires_on(cls, values: dict[str, Any]) -> dict[str, Any]:
        if isinstance(values.get("expires_in"), int):
            values["expires_on"] = datetime.utcnow() + timedelta(
                seconds=values["expires_in"],
            )
        return values

    @root_validator
    def _check_scopes(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not bool(values["refresh_token"]):
            values["scopes"] = Scopes.PUBLIC
        return values

    @property
    def can_refresh(self) -> bool:
        return bool(self.refresh_token)
