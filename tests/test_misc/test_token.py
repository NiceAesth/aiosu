from __future__ import annotations

import pytest

import aiosu
from aiosu.models import Scopes


@pytest.fixture
def auth_token():
    return {
        "access_token": "verylongstring",
        "expires_in": 86400,
        "refresh_token": "anotherlongstring",
        "token_type": "Bearer",
    }


@pytest.fixture
def credentials_token():
    return {
        "access_token": "verylongstring",
        "expires_in": 86400,
        "token_type": "Bearer",
    }


def test_auth_token(auth_token):
    expected_scopes = Scopes.PUBLIC | Scopes.IDENTIFY
    token = aiosu.models.OAuthToken.parse_obj(auth_token)
    assert token.scopes is expected_scopes
    assert token.can_refresh


def test_credentials_token(credentials_token):
    expected_scopes = Scopes.PUBLIC
    token = aiosu.models.OAuthToken.parse_obj(credentials_token)
    assert token.scopes is expected_scopes
    assert not token.can_refresh
