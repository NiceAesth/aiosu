from __future__ import annotations

from typing import TypeVar

import aiosu
from aiosu.helpers import from_list

T = TypeVar("T")


def test_osu_performance(performance_scores, difficulty_attributes):
    score_list = performance_scores("osu")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("osu")["attributes"],
        )
        calc = aiosu.utils.performance.OsuPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_taiko_performance(performance_scores, difficulty_attributes):
    score_list = performance_scores("taiko")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("taiko")["attributes"],
        )
        calc = aiosu.utils.performance.TaikoPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_mania_performance(performance_scores, difficulty_attributes):
    score_list = performance_scores("mania")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("mania")["attributes"],
        )
        calc = aiosu.utils.performance.ManiaPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0


def test_catch_performance(performance_scores, difficulty_attributes):
    score_list = performance_scores("fruits")
    for score in from_list(aiosu.models.Score.model_validate, score_list):
        diffatrib = aiosu.models.BeatmapDifficultyAttributes.model_validate(
            difficulty_attributes("fruits")["attributes"],
        )
        calc = aiosu.utils.performance.CatchPerformanceCalculator(diffatrib)
        performance_attributes = calc.calculate(score)
        assert performance_attributes.total > 0
