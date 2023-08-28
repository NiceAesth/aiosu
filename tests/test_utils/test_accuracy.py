from __future__ import annotations

from typing import TypeVar

import orjson
import pytest

import aiosu
from aiosu.helpers import from_list

T = TypeVar("T")


@pytest.fixture
def scores():
    def _scores(mode="osu"):
        with open(f"tests/data/v2/score_{mode}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _scores


def test_osu_accuracy(scores):
    calc = aiosu.utils.accuracy.OsuAccuracyCalculator()
    score_list = scores("osu")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_taiko_accuracy(scores):
    calc = aiosu.utils.accuracy.TaikoAccuracyCalculator()
    score_list = scores("taiko")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_mania_accuracy(scores):
    calc = aiosu.utils.accuracy.ManiaAccuracyCalculator()
    score_list = scores("mania")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_catch_accuracy(scores):
    calc = aiosu.utils.accuracy.CatchAccuracyCalculator()
    score_list = scores("fruits")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy
