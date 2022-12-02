from __future__ import annotations


class APIException(Exception):
    def __init__(self, status: int, message: str = "") -> None:
        super().__init__(message)
        self.status = status
