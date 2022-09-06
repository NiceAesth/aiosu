from __future__ import annotations


class APIException(Exception):
    def __init__(self, type, message="") -> None:
        super().__init__(message)
        self.type = type
