from __future__ import annotations

from typing import TypeVar

import aiosu
from aiosu.helpers import from_list

T = TypeVar("T")


def test_osu_accuracy(accuracy_scores):
    calc = aiosu.utils.accuracy.OsuAccuracyCalculator()
    score_list = accuracy_scores("osu")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_taiko_accuracy(accuracy_scores):
    calc = aiosu.utils.accuracy.TaikoAccuracyCalculator()
    score_list = accuracy_scores("taiko")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_mania_accuracy(accuracy_scores):
    calc = aiosu.utils.accuracy.ManiaAccuracyCalculator()
    score_list = accuracy_scores("mania")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy


def test_catch_accuracy(accuracy_scores):
    calc = aiosu.utils.accuracy.CatchAccuracyCalculator()
    score_list = accuracy_scores("fruits")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        acc = calc.calculate(score)
        assert acc == score.accuracy
