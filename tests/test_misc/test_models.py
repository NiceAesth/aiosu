from __future__ import annotations

import pydantic
import pytest

import aiosu


class SampleBaseModel(aiosu.models.BaseModel):
    simple: str
    mods: aiosu.models.Mods
    gamemode: aiosu.models.Gamemode


class SampleFrozenModel(aiosu.models.FrozenModel):
    simple: str
    mods: aiosu.models.Mods
    gamemode: aiosu.models.Gamemode


def test_base_model():
    model = SampleBaseModel(simple="test", mods="HD", gamemode="osu")
    model_json = model.model_dump_json()
    new_model = SampleBaseModel.model_validate_json(model_json)

    assert new_model == model

    model.simple = "Test"
    assert model.simple == "Test"


def test_frozen_model():
    model = SampleFrozenModel(simple="test", mods="HD", gamemode="osu")
    model_json = model.model_dump_json()
    new_model = SampleFrozenModel.model_validate_json(model_json)
    assert new_model == model

    with pytest.raises(pydantic.ValidationError):
        model.simple = "Test"
