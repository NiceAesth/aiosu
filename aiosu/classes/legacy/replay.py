from __future__ import annotations

from ..models import BaseModel


class Replay(BaseModel):
    content: str
    encoding: str
