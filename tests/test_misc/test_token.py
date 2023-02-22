from __future__ import annotations

import pytest

import aiosu
from aiosu.models import Scopes


@pytest.fixture
def auth_token():
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsiaWRlbnRpZnkiLCJwdWJsaWMiXX0.eHwSds48D1qqWkFI18PcL2YNO9-Agr6OUGg-zAdDq3uj6p6mkgUOmJqHQkMNK5JjzF3qF0XBou_0NgOfTz5tVg68T0P90CBi4SmMw5Ljp8ir5-Jbsq9abo4RCfQG_0kQNGtvTftoxYudaQQXD-BmpxfwSDXXxJJIdoYpPBBmiKFAF8C2wf6451F9i9hR77oF67I7_NjEP2xXiLVkYHuiwtvgZDHjPFKA8LvXXJCVLui-dZvW45SCz9u5Kr1NIR_lFFbp0GsQPDQZNz1PU20oswJlo7aKnH8OpAepP13G9cdy8wXbqn8nhsI4hunRcuTeqMDJsCThWx23D5rwfGIqag",
        "expires_in": 86400,
        "refresh_token": "anotherlongstring",
        "token_type": "Bearer",
    }


@pytest.fixture
def credentials_token():
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkZiIsImlhdCI6MTY3Mjk1MDI0NS45MjAxMzMsIm5iZiI6MTY3Mjk1MDI0NS45MjAxMzYsImV4cCI6MTY3MzAzNTc4NC4wMTY2MjEsInN1YiI6Ijc3ODI1NTMiLCJzY29wZXMiOlsicHVibGljIl19.DfzJZgQUpfF5MwNFS2iEDimSSm3PrFJQNNw9XF-l9kzgOyb4QSrKV79FxOI2TfBPHIP6BKs-SjwNlI_KJZBjtMM5jEIwmqzgfkZqSkUWkm7urqRi5Z0phR8x1FdwlDDhMiDX5L9o2Hxe5AEOlCWShDSTjBLwxLe7y9NXLSGicaZ_024TnT-aCevq2bcVBJTYE2GKRBWcgtk4rnwQ6TAf6nf6ZY0OS5t4NyfXLVvceU8GRdER_2GfqgidYOW85C_qPG82bBknWYdaZgNt-u4dMevQwuOrLDdXCX84g1y6BSRGaK3Pm9HAIOi714ZbEke1OikRIDK24WAZ0FJMOl0KrQ",
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
