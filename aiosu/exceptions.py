"""
This module contains custom exception types.
"""
from __future__ import annotations

__all__ = ("APIException",)


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
