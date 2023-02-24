from __future__ import annotations

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
    model_json = model.json()
    new_model = SampleBaseModel.parse_raw(model_json)

    assert new_model == model

    model.simple = "Test"
    assert model.simple == "Test"


def test_frozen_model():
    model = SampleFrozenModel(simple="test", mods="HD", gamemode="osu")
    model_json = model.json()
    new_model = SampleFrozenModel.parse_raw(model_json)
    assert new_model == model

    with pytest.raises(TypeError):
        model.simple = "Test"
