from __future__ import annotations

import aiosu

model = aiosu.models.BaseModel()  # aiosu classes are pydantic models
dict_model = model.model_dump()
dict_json = model.model_dump_json()

# see: https://pydantic-docs.helpmanual.io/usage/models/#helper-functions
new_model = aiosu.models.BaseModel.model_validate(dict_model)  # dict to class
new_model = aiosu.models.BaseModel.model_validate_json(
    dict_json,
)  # json string to class
new_model = aiosu.models.BaseModel.model_validate_file(
    "./path/to/file",
)  # file to class

# models which are also supported in API v1 can be obtained with
data = {}
mode = aiosu.models.Gamemode.STANDARD
score = aiosu.models.Score._from_api_v1(data, mode)
beatmapset = aiosu.models.Beatmapset._from_api_v1(data)

# aiosu has a helper module with various utilities
data_list = [{}]
beatmaps = aiosu.helpers.from_list(data_list, aiosu.models.Beatmap.model_validate)
