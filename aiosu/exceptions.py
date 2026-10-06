"""
This module contains custom exception types.
"""

from __future__ import annotations

import re

__all__ = (
    "APIException",
    "InvalidClientRequestedError",
    "RefereeInvocationError",
    "RefreshTokenExpiredError",
)


class RefereeInvocationError(Exception):
    """Referee Invocation Error

    :param message: error message returned
    :type message: str
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        match = re.match(r"Error (\d+):", message)
        self.code: int | None = int(match[1]) if match else None


class APIException(Exception):
    """API Exception Class

    :param status: status code from the API
    :type status: int
    :param message: error message returned, defaults to ""
    :type message: str, optional
    """

    def __init__(self, status: int, message: str = "") -> None:
        super().__init__(message)
        self.status = status


class RefreshTokenExpiredError(Exception):
    """Refresh Token Expired Error

    :param message: error message, defaults to ""
    :type message: str, optional
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class InvalidClientRequestedError(Exception):
    """Invalid Client Requested Error

    :param message: error message, defaults to ""
    :type message: str, optional
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
