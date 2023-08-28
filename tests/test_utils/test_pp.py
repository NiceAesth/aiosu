from __future__ import annotations

from typing import TypeVar

import orjson
import pytest

import aiosu
from aiosu.helpers import from_list

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
    def _scores(mode="osu"):
        with open(f"tests/data/v2/score_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _scores


def test_osu_performance(scores, difficulty_attributes):
    score_list = scores("osu")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("osu")["attributes"],
        )
        calc = aiosu.utils.performance.OsuPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_taiko_performance(scores, difficulty_attributes):
    score_list = scores("taiko")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("taiko")["attributes"],
        )
        calc = aiosu.utils.performance.TaikoPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_mania_performance(scores, difficulty_attributes):
    score_list = scores("mania")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("mania")["attributes"],
        )
        calc = aiosu.utils.performance.ManiaPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_catch_performance(scores, difficulty_attributes):
    score_list = scores("fruits")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("fruits")["attributes"],
        )
        calc = aiosu.utils.performance.CatchPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0
