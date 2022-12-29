from __future__ import annotations

from typing import TypeVar

import orjson
import pytest

import aiosu
from aiosu.helpers import from_list

types = ["recents", "bests", "firsts"]

T = TypeVar("T")


@pytest.fixture
def difficulty_attributes():
    def _difficulty_attributes(mode="osu"):
        with open(f"tests/data/v2/difficulty_attributes_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _difficulty_attributes


@pytest.fixture
def scores():
    def _scores(mode="osu", type="recents"):
        with open(f"tests/data/v2/multiple_score_{mode}_{type}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _scores


def test_osu_performance(scores, difficulty_attributes):
    for score_type in types:
        score_list = scores("osu", score_type)
        for score in from_list(aiosu.models.Score.parse_obj, score_list):
            diffatrib = aiosu.models.BeatmapDifficultyAttributes.parse_obj(
                difficulty_attributes("osu")[str(score.beatmap.id)]["attributes"],
            )
            calc = aiosu.utils.performance.OsuPerformanceCalculator(diffatrib)
            performance_attributes = calc.calculate(score)
            assert performance_attributes.total > 0


def test_taiko_performance(scores, difficulty_attributes):
    for score_type in types:
        score_list = scores("taiko", score_type)
        for score in from_list(aiosu.models.Score.parse_obj, score_list):
            diffatrib = aiosu.models.BeatmapDifficultyAttributes.parse_obj(
                difficulty_attributes("taiko")[str(score.beatmap.id)]["attributes"],
            )
            calc = aiosu.utils.performance.TaikoPerformanceCalculator(diffatrib)
            performance_attributes = calc.calculate(score)
            assert performance_attributes.total > 0


def test_mania_performance(scores, difficulty_attributes):
    for score_type in types:
        score_list = scores("mania", score_type)
        for score in from_list(aiosu.models.Score.parse_obj, score_list):
            diffatrib = aiosu.models.BeatmapDifficultyAttributes.parse_obj(
                difficulty_attributes("mania")[str(score.beatmap.id)]["attributes"],
            )
            calc = aiosu.utils.performance.ManiaPerformanceCalculator(diffatrib)
            performance_attributes = calc.calculate(score)
            assert performance_attributes.total > 0


def test_catch_performance(scores, difficulty_attributes):
    for score_type in types:
        score_list = scores("fruits", score_type)
        for score in from_list(aiosu.models.Score.parse_obj, score_list):
            diffatrib = aiosu.models.BeatmapDifficultyAttributes.parse_obj(
                difficulty_attributes("fruits")[str(score.beatmap.id)]["attributes"],
            )
            calc = aiosu.utils.performance.CatchPerformanceCalculator(diffatrib)
            performance_attributes = calc.calculate(score)
            assert performance_attributes.total > 0
