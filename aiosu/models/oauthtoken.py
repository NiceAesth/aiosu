"""
This module contains models for API v2 token objects.
"""
from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

import jwt
from pydantic import root_validator

from .base import BaseModel
from .scopes import Scopes

if TYPE_CHECKING:
    from typing import Any

__all__ = ("OAuthToken",)


class OAuthToken(BaseModel):
    token_type: str = "Bearer"
    """Defaults to 'Bearer'"""
    access_token: str = ""
    refresh_token: str = ""
    expires_on: datetime = datetime.utcfromtimestamp(0)
    """Can be a datetime.datetime object or a string. Alternatively, expires_in may be passed representing the number of seconds the token will be valid for."""

    @property
    def owner_id(self) -> int:
        if not self.access_token:
            return 0
        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
        if decoded["sub"]:
            return int(decoded["sub"])
        return 0

    @property
    def scopes(self) -> Scopes:
        if not self.access_token:
            return Scopes.PUBLIC
        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
        return Scopes.from_api_list(decoded["scopes"])

    @root_validator(pre=True)
    def _set_expires_on(cls, values: dict[str, Any]) -> dict[str, Any]:
        if isinstance(values.get("expires_in"), int):
            values["expires_on"] = datetime.utcnow() + timedelta(
                seconds=values["expires_in"],
            )
        return values

    @property
    def can_refresh(self) -> bool:
        """Returns True if the token can be refreshed."""
        return bool(self.refresh_token)
