"""
This module contains models for API v2 token objects.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from functools import cached_property

import jwt
from pydantic import computed_field
from pydantic import model_validator

from .base import FrozenModel
from .scopes import Scopes

__all__ = ("OAuthToken",)


class OAuthToken(FrozenModel):
    token_type: str = "Bearer"
    """Defaults to 'Bearer'"""
    access_token: str = ""
    refresh_token: str = ""
    expires_on: datetime = datetime.utcfromtimestamp(31536000)
    """Can be a datetime.datetime object or a string. Alternatively, expires_in may be passed representing the number of seconds the token will be valid for."""

    @computed_field  # type: ignore
    @cached_property
    def owner_id(self) -> int:
        if not self.access_token:
            return 0
        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
        if decoded["sub"]:
            return int(decoded["sub"])
        return 0

    @computed_field  # type: ignore
    @cached_property
    def scopes(self) -> Scopes:
        if not self.access_token:
            return Scopes.PUBLIC
        decoded = jwt.decode(self.access_token, options={"verify_signature": False})
        return Scopes.from_api_list(decoded["scopes"])

    @computed_field  # type: ignore
    @cached_property
    def can_refresh(self) -> bool:
        """Returns True if the token can be refreshed."""
        return bool(self.refresh_token)

    @model_validator(mode="before")
    @classmethod
    def _set_expires_on(cls, values: dict[str, object]) -> dict[str, object]:
        expires_in = values.get("expires_in")
        if isinstance(expires_in, int):
            values["expires_on"] = datetime.utcnow() + timedelta(
                seconds=expires_in,
            )
        return values
