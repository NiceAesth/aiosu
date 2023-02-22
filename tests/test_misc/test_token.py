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
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiI5OTk5IiwianRpIjoiYXNkIiwiaWF0IjoxNjc3MTA0NjU3LjU2NjUyNCwibmJmIjoxNjc3MTA0NjU3LjU2NjUyNSwiZXhwIjoxNjc3MTkxMDU3LjU1OTc1Nywic3ViIjoiIiwic2NvcGVzIjpbInB1YmxpYyJdfQ.ApjKrJg_k8PmMVYt1Fkj3_w0G2Mds7oXQMitRpEmTGER5I4hX16mwHwhiAryWXzDH0MnPTRzZDB8AE_mjN25AjK4I-B7dB0eWe6-7pOI3eYmxlFVIKtXseNkpAtEKA1vo2xsr06ngwUBxxrro2tE3W8CJNz7sQD_mt6fabh1V2OlTb-X8Dm6o732dknMm5S4yCTAsT_YeO1_4ovyTWkGkCxfJGD2MtPnFiX1ieFOBtPAaQafkrz2ncadzcGJpsKiwVBQAJGu4nkVffYxXa6jZ7ud1whBZfvpCmuzQjNEagqUUHFmjJYRdD92DcFjVe-e-3uwK2bDAJ2rKOYasvZyZg",
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
