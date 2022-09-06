from __future__ import annotations

from aiosu.classes import BaseModel
from aiosu.classes import Mod
from aiosu.classes import Mods


class Test(BaseModel):
    mods: Mods


test = Test(mods="HDDT")
dict = test.json()
print(dict)
test2 = Test.parse_raw(dict)
print(test2)
