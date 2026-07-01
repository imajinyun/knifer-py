import pytest

from kniferpy import vnum
from kniferpy.verr import ValidationError


def test_validation() -> None:
    assert vnum.is_number("  -3.14 ")
    assert vnum.is_number("0xFF")
    assert vnum.is_integer("42")
    assert not vnum.is_integer("3.14")
    assert vnum.is_double("3.14")
    assert not vnum.is_double("3")
    assert vnum.is_digits("12345")
    assert not vnum.is_digits("-1")


def test_predicates() -> None:
    assert vnum.is_prime(7)
    assert not vnum.is_prime(1)
    assert vnum.is_odd(3)
    assert vnum.is_even(4)
    assert vnum.is_power_of_two(8)
    assert not vnum.is_power_of_two(6)


def test_parse_defaults() -> None:
    assert vnum.parse_int("42") == 42
    assert vnum.parse_int("bad", default=-1) == -1
    assert vnum.parse_float("3.5") == pytest.approx(3.5)
    assert vnum.parse_float("bad", default=1.0) == pytest.approx(1.0)


def test_compare_clamp_range() -> None:
    assert vnum.compare(1, 2) == -1
    assert vnum.compare(3, 3) == 0
    assert vnum.clamp(15, 0, 10) == 10
    assert vnum.is_in(5, 0, 10)
    assert vnum.ceil_div(7, 2) == 4
    assert vnum.gcd(12, 8) == 4
    assert vnum.lcm(4, 6) == 12
    assert vnum.num_range(0, 5, 2) == [0, 2, 4]
    assert vnum.range_closed(1, 3) == [1, 2, 3]


def test_aggregate_round_factorial() -> None:
    assert vnum.sum_values([1.0, 2.0, 3.0]) == pytest.approx(6.0)
    assert vnum.avg_values([2.0, 4.0]) == pytest.approx(3.0)
    assert vnum.avg_values([]) == pytest.approx(0.0)
    assert vnum.min_value([3.0, 1.0]) == pytest.approx(1.0)
    assert vnum.max_value([3.0, 1.0]) == pytest.approx(3.0)
    assert vnum.round_half_up(1.25, 1) == pytest.approx(1.3)
    assert vnum.round_half_up(-2.5) == pytest.approx(-3.0)
    assert vnum.factorial(5) == 120
    with pytest.raises(ValidationError):
        vnum.factorial(-1)
