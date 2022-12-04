from __future__ import annotations

import aiosu

model = aiosu.classes.BaseModel()  # aiosu classes are pydantic models
dict_model = model.dict()
dict_json = (
    model.json()
)  # aiosu uses the orjson module for any json operations for increased speed

# see: https://pydantic-docs.helpmanual.io/usage/models/#helper-functions
new_model = aiosu.classes.BaseModel.parse_obj(dict_model)  # dict to class
new_model = aiosu.classes.BaseModel.parse_raw(dict_json)  # json string to class
new_model = aiosu.classes.BaseModel.parse_file(path)  # file to class

# models which are also supported in API v1 can be obtained with
data = {}
score = aiosu.classes.Score._from_api_v1(data, mode)
beatmapset = aiosu.classes.Beatmapset._from_api_v1(data)

# aiosu has a helper module with various utilities
data_list = [{}]
beatmaps = aiosu.helpers.from_list(data_list, aiosu.classes.Beatmap.parse_obj)
