from __future__ import annotations

from typing import TypeVar

import orjson
import pytest

import aiosu
from aiosu.helpers import from_list

types = ["recents", "bests", "firsts"]

T = TypeVar("T")


@pytest.fixture
def scores():
    def _scores(mode="osu", score_type="recents"):
        with open(f"tests/data/v2/multiple_score_{mode}_{score_type}.json", "rb") as f:
            data = orjson.loads(f.read())
        return data

    return _scores


def test_osu_accuracy(scores):
    calc = aiosu.utils.accuracy.OsuAccuracyCalculator()
    for score_type in types:
        score_list = scores("osu", score_type)
        for score in from_list(aiosu.models.Score.model_validate, score_list):
            acc = calc.calculate(score)
            assert acc == score.accuracy


def test_taiko_accuracy(scores):
    calc = aiosu.utils.accuracy.TaikoAccuracyCalculator()
    for score_type in types:
        score_list = scores("taiko", score_type)
        for score in from_list(aiosu.models.Score.model_validate, score_list):
            acc = calc.calculate(score)
            assert acc == score.accuracy


def test_mania_accuracy(scores):
    calc = aiosu.utils.accuracy.ManiaAccuracyCalculator()
    for score_type in types:
        score_list = scores("mania", score_type)
        for score in from_list(aiosu.models.Score.model_validate, score_list):
            acc = calc.calculate(score)
            assert acc == score.accuracy


def test_catch_accuracy(scores):
    calc = aiosu.utils.accuracy.CatchAccuracyCalculator()
    for score_type in types:
        score_list = scores("fruits", score_type)
        for score in from_list(aiosu.models.Score.model_validate, score_list):
            acc = calc.calculate(score)
            assert acc == score.accuracy
