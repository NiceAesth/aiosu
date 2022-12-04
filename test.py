from __future__ import annotations

import orjson

import aiosu
from aiosu.classes.legacy import Match

with open(f"tests/data/v1/match.json", "rb") as f:
    data = orjson.loads(f.read())
f.close()

match = Match.parse_obj(data)
print(match)
