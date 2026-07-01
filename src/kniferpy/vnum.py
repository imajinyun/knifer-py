from __future__ import annotations

from collections.abc import Sequence

from kniferpy.internal import numx


def is_number(value: str) -> bool:
    return numx.is_number(value)


def is_integer(value: str) -> bool:
    return numx.is_integer(value)


def is_double(value: str) -> bool:
    return numx.is_double(value)


def is_digits(value: str) -> bool:
    return numx.is_digits(value)


def is_prime(n: int) -> bool:
    return numx.is_prime(n)


def is_odd(n: int) -> bool:
    return numx.is_odd(n)


def is_even(n: int) -> bool:
    return numx.is_even(n)


def is_power_of_two(n: int) -> bool:
    return numx.is_power_of_two(n)


def parse_int(value: str, default: int = 0) -> int:
    return numx.parse_int(value, default)


def parse_float(value: str, default: float = 0.0) -> float:
    return numx.parse_float(value, default)


def clamp(value: float, low: float, high: float) -> float:
    return numx.clamp(value, low, high)


def is_in(value: float, low: float, high: float) -> bool:
    return numx.is_in(value, low, high)


def compare(a: float, b: float) -> int:
    return numx.compare(a, b)


def sum_values(values: Sequence[float]) -> float:
    return numx.sum_values(values)


def avg_values(values: Sequence[float]) -> float:
    return numx.avg_values(values)


def min_value(values: Sequence[float]) -> float:
    return numx.min_value(values)


def max_value(values: Sequence[float]) -> float:
    return numx.max_value(values)


def ceil_div(a: int, b: int) -> int:
    return numx.ceil_div(a, b)


def gcd(m: int, n: int) -> int:
    return numx.gcd(m, n)


def lcm(m: int, n: int) -> int:
    return numx.lcm(m, n)


def round_half_up(value: float, scale: int = 0) -> float:
    return numx.round_half_up(value, scale)


def factorial(n: int) -> int:
    return numx.factorial(n)


def num_range(start: int, stop: int, step: int = 1) -> list[int]:
    return numx.num_range(start, stop, step)


def range_closed(start: int, stop: int, step: int = 1) -> list[int]:
    return numx.range_closed(start, stop, step)
