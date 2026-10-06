from __future__ import annotations

import aiosu
from aiosu.models import Scopes


def test_auth_token(auth_token_data):
    expected_scopes = Scopes.PUBLIC | Scopes.IDENTIFY
    token = aiosu.models.OAuthToken.model_validate(auth_token_data)
    assert token.scopes is expected_scopes
    assert token.can_refresh


def test_credentials_token(credentials_token_data):
    expected_scopes = Scopes.PUBLIC
    token = aiosu.models.OAuthToken.model_validate(credentials_token_data)
    assert token.scopes is expected_scopes
    assert not token.can_refresh
