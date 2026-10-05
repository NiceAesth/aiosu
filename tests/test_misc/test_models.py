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

    assert int(hd_mods | dt_mods) == 72
    assert int(hd_mods | dt_mod) == 72
    assert int(hd_mod | dt_mod) == 72

    assert int(hd_mods & dt_mods) == 0
    assert int(hd_mods & dt_mod) == 0
    assert int(hd_mod & dt_mod) == 0

    assert int(hd_mods & hd_mod) == 8

    assert str(hd_mods) == "HD"
    assert str(hd_mod) == "HD"
    assert str(combined_mods) == str(special_mods) == "NCPF"

    with pytest.raises(TypeError):
        hd_mods & "DT"


@pytest.mark.parametrize(
    ("name", "acronym", "bitmask"),
    [
        ("NoMod", "NM", 0),
        ("Hidden", "HD", 8),
        ("DoubleTime", "DT", 64),
        ("Nightcore", "NC", 512),
        ("Perfect", "PF", 16384),
        ("ScoreV2", "SV2", 536870912),
        ("Mirror", "MR", 1073741824),
    ],
)
def test_named_mod_constants(name, acronym, bitmask):
    mod = getattr(aiosu.models.Mod, name)

    assert isinstance(mod, aiosu.models.Mod)
    assert mod.name == name
    assert mod.short_name == str(mod) == acronym
    assert mod.value == mod.bitmask == int(mod) == bitmask
    assert aiosu.models.Mod(bitmask) == mod
    assert aiosu.models.Mod(mod) == mod
    assert mod in aiosu.models.Mods(acronym)
    assert name not in aiosu.models.Mod.model_fields


def test_named_mod_constant_operations():
    mod = aiosu.models.Mod
    mods = aiosu.models.Mods
    combined = mod.Hidden | mod.DoubleTime

    assert isinstance(combined, mods)
    assert int(combined) == 72
    assert combined.to_api() == [{"acronym": "HD"}, {"acronym": "DT"}]
    assert (combined & mod.Hidden) == mods("HD")
    assert (combined ^ mod.Hidden) == mods("DT")
    assert (8 | mod.DoubleTime) == combined
    assert int(mod.Nightcore | mod.Perfect) == 16992
    assert mods(16992).to_acronyms() == ["NC", "PF"]
    assert not mod.NoMod
    assert not (mod.Hidden & mod.DoubleTime)


def test_mod_group_bitmasks():
    assert type(aiosu.models.KeyMod) is int
    assert type(aiosu.models.FreemodAllowed) is int
    assert type(aiosu.models.ScoreIncreaseMods) is int
    assert type(aiosu.models.SpeedChangingMods) is int
    assert aiosu.models.ScoreIncreaseMods == 1112
    assert aiosu.models.SpeedChangingMods == 832


def test_mod_settings_legacy_conversion():
    mod = aiosu.models.Mod("DT", settings={"speed_change": 1.2})
    assert mod != aiosu.models.Mod.DoubleTime
    assert aiosu.models.Mod(mod) == mod
    assert aiosu.models.Mods(mod).to_api() == [
        {"acronym": "DT", "settings": {"speed_change": 1.2}},
    ]
    assert int(mod) == 64
    assert int(aiosu.models.Mods([aiosu.models.Mod.Hidden, mod])) == 72
    assert int(mod | aiosu.models.Mod.Hidden) == 72
    assert int(aiosu.models.Mod("NC", settings={"speed_change": 1.2})) == 512
    assert (
        int(aiosu.models.Mods([{"acronym": "NC", "settings": {"speed_change": 1.2}}]))
        == 576
    )
    with pytest.raises(ValueError):
        int(aiosu.models.Mod("CL"))


@pytest.mark.parametrize("mode", list(aiosu.models.Gamemode))
def test_statistics_mode(mode):
    counts = {
        "count_300": 10,
        "count_100": 5,
        "count_50": 3,
        "count_geki": 2,
        "count_katu": 4,
        "count_miss": 1,
    }
    statistics = aiosu.models.ScoreStatistics(mode=mode, **counts)

    assert statistics.mode == mode
    for name, count in counts.items():
        assert getattr(statistics, name) == count
    assert "mode" not in statistics.model_dump()
    if mode == aiosu.models.Gamemode.CTB:
        assert statistics.large_tick_hit == 5
        assert statistics.small_tick_hit == 3
        assert statistics.small_tick_miss == 4
    elif mode == aiosu.models.Gamemode.TAIKO:
        assert statistics.large_bonus == 6
    else:
        assert statistics.ok == 5
        assert statistics.meh == 3


def test_statistics_mode_from_payload():
    statistics = aiosu.models.ScoreStatistics.model_validate(
        {"mode": "fruits", "great": 10, "large_tick_hit": 5, "small_tick_hit": 3},
    )
    assert statistics.mode == aiosu.models.Gamemode.CTB
    assert statistics.count_100 == 5
    assert statistics.count_50 == 3


def test_score_sets_statistics_mode():
    statistics = aiosu.models.ScoreStatistics(great=10, large_tick_hit=5)
    score = aiosu.models.Score(
        user_id=1,
        accuracy=1,
        mods="NM",
        score=1000,
        max_combo=15,
        passed=True,
        perfect=True,
        statistics=statistics,
        rank="S",
        created_at="2026-10-06T00:00:00Z",
        mode=aiosu.models.Gamemode.CTB,
        replay=False,
    )
    assert score.statistics.mode == aiosu.models.Gamemode.CTB
    assert score.statistics.count_100 == 5
    assert "mode" not in score.model_dump()["statistics"]
