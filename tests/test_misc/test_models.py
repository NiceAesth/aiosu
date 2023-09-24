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


def test_mods():
    hd_mods = aiosu.models.Mods("HD")
    dt_mods = aiosu.models.Mods("DT")
    special_mods = aiosu.models.Mods("NCPF")
    combined_mods = aiosu.models.Mods("DTNCSDPF")
    hd_mod = aiosu.models.Mod("HD")
    dt_mod = aiosu.models.Mod("DT")

    assert int(hd_mods) == 8
    assert int(dt_mods) == 64
    assert int(special_mods) == int(combined_mods) == 16992

    assert hd_mods | dt_mods == 72
    assert hd_mods | dt_mod == 72
    assert hd_mod | dt_mod == 72

    assert hd_mods & dt_mods == 0
    assert hd_mods & dt_mod == 0
    assert hd_mod & dt_mod == 0

    assert hd_mods & hd_mod == 8

    assert str(hd_mods) == "HD"
    assert str(hd_mod) == "HD"
    assert str(combined_mods) == str(special_mods) == "NCPF"

    with pytest.raises(TypeError):
        hd_mods & "DT"
