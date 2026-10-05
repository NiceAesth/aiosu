from __future__ import annotations

import math

SQRT2 = 1.4142135623730950


def logistic(
    x: float,
    midpoint_offset: float,
    multiplier: float,
    max_value: float = 1.0,
) -> float:
    return max_value / (1 + math.exp(multiplier * (midpoint_offset - x)))


def norm(p: float, *values: float) -> float:
    total = 0.0
    for x in values:
        total += math.pow(x, p)
    return math.pow(total, 1.0 / p)


def smoothstep(x: float, start: float, end: float) -> float:
    x = max(0.0, min((x - start) / (end - start), 1.0))
    return x * x * (3.0 - 2.0 * x)


def reverse_lerp(x: float, start: float, end: float) -> float:
    return max(0.0, min((x - start) / (end - start), 1.0))


def erf(x: float) -> float:
    if x == 0:
        return 0.0
    if x == math.inf:
        return 1.0
    if x == -math.inf:
        return -1.0
    if math.isnan(x):
        return math.nan

    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    tau = t * (
        0.254829592
        + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    result = 1.0 - tau * math.exp(-x * x)
    return result if x >= 0 else -result


def erf_inv(x: float) -> float:
    if x <= -1:
        return -math.inf
    if x >= 1:
        return math.inf
    if x == 0:
        return 0.0

    a = 0.147
    sgn = 1.0 if x > 0 else -1.0
    x = abs(x)

    ln = math.log(1 - x * x)
    t1 = 2 / (math.pi * a) + ln / 2
    t2 = ln / a
    base_approx = math.sqrt(t1 * t1 - t2) - t1
    c = math.pow((x - 0.85) / 0.293, 8) if x >= 0.85 else 0.0
    return sgn * (math.sqrt(base_approx) + c)
