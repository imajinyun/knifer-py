from __future__ import annotations

from datetime import datetime

import pytest

from kniferpy import vcron
from kniferpy.verr import ValidationError


def _dt(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(year, month, day, hour, minute, second)


def test_step_range_every_15_minutes() -> None:
    pattern = vcron.new_pattern("*/15 * * * *")
    for minute in (0, 15, 30, 45):
        assert pattern.match(_dt(2024, 1, 1, 0, minute)) is True
    for minute in (1, 7, 14, 16, 31, 44, 46, 59):
        assert pattern.match(_dt(2024, 1, 1, 0, minute)) is False


def test_day_of_week_alias() -> None:
    pattern = vcron.new_pattern("0 9 * * mon")
    assert pattern.match(_dt(2024, 1, 1, 9, 0)) is True  # Monday.
    assert pattern.match(_dt(2024, 1, 2, 9, 0)) is False  # Tuesday.


def test_month_alias() -> None:
    pattern = vcron.new_pattern("0 0 1 jan *")
    assert pattern.match(_dt(2024, 1, 1)) is True
    assert pattern.match(_dt(2024, 2, 1)) is False


def test_list_field() -> None:
    pattern = vcron.new_pattern("0,15,30,45 * * * *")
    for minute in (0, 15, 30, 45):
        assert pattern.match(_dt(2024, 1, 1, 0, minute)) is True
    assert pattern.match(_dt(2024, 1, 1, 0, 20)) is False


def test_hour_range() -> None:
    pattern = vcron.new_pattern("0 9-17 * * *")
    for hour in range(9, 18):
        assert pattern.match(_dt(2024, 1, 1, hour)) is True
    for hour in (0, 8, 18, 23):
        assert pattern.match(_dt(2024, 1, 1, hour)) is False


def test_last_day_of_month_leap_and_non_leap() -> None:
    pattern = vcron.new_pattern("0 0 L * *")
    assert pattern.match(_dt(2024, 2, 29)) is True  # Leap year.
    assert pattern.match(_dt(2024, 2, 28)) is False
    assert pattern.match(_dt(2023, 2, 28)) is True  # Non-leap year.


def test_second_field() -> None:
    pattern = vcron.new_pattern("30 0 12 * * *")
    assert pattern.match(_dt(2024, 1, 1, 12, 0, 30), match_second=True) is True
    assert pattern.match(_dt(2024, 1, 1, 12, 0, 31), match_second=True) is False


def test_second_ignored_when_match_second_false() -> None:
    pattern = vcron.new_pattern("30 0 12 * * *")
    # With seconds ignored, any second within 12:00 matches.
    assert pattern.match(_dt(2024, 1, 1, 12, 0, 31), match_second=False) is True


def test_or_expression() -> None:
    pattern = vcron.new_pattern("0 9 * * mon | 0 17 * * fri")
    assert pattern.match(_dt(2024, 1, 1, 9, 0)) is True  # Monday 09:00.
    assert pattern.match(_dt(2024, 1, 5, 17, 0)) is True  # Friday 17:00.
    assert pattern.match(_dt(2024, 1, 2, 9, 0)) is False  # Tuesday.


def test_year_field() -> None:
    pattern = vcron.new_pattern("0 0 0 1 1 * 2024")
    assert pattern.match(_dt(2024, 1, 1)) is True
    assert pattern.match(_dt(2025, 1, 1)) is False


def test_weekday_seven_is_sunday() -> None:
    pattern = vcron.new_pattern("0 0 * * 7")
    assert pattern.match(_dt(2024, 1, 7)) is True  # Sunday.
    assert pattern.match(_dt(2024, 1, 1)) is False  # Monday.


def test_reversed_range_wraps() -> None:
    # Hours 22-2 wraps to {22, 23, 0, 1, 2}.
    pattern = vcron.new_pattern("0 22-2 * * *")
    for hour in (22, 23, 0, 1, 2):
        assert pattern.match(_dt(2024, 1, 1, hour)) is True
    for hour in (3, 12, 21):
        assert pattern.match(_dt(2024, 1, 1, hour)) is False


def test_module_level_match() -> None:
    assert vcron.match("0 0 * * *", _dt(2024, 1, 1, 0, 0)) is True
    assert vcron.match("0 0 * * *", _dt(2024, 1, 1, 1, 0)) is False


def test_raw_property() -> None:
    pattern = vcron.new_pattern("  0 12 * * *  ")
    assert pattern.raw == "0 12 * * *"


def test_next_time_minute_granularity() -> None:
    pattern = vcron.new_pattern("0 12 * * *")
    result = pattern.next_time(_dt(2024, 1, 1, 10, 30))
    assert result == _dt(2024, 1, 1, 12, 0)


def test_next_time_rolls_to_next_day() -> None:
    pattern = vcron.new_pattern("0 8 * * *")
    result = pattern.next_time(_dt(2024, 1, 1, 9, 0))
    assert result == _dt(2024, 1, 2, 8, 0)


def test_next_time_is_strictly_after() -> None:
    pattern = vcron.new_pattern("0 12 * * *")
    # Starting exactly on a match returns the next day's match.
    result = pattern.next_time(_dt(2024, 1, 1, 12, 0))
    assert result == _dt(2024, 1, 2, 12, 0)


def test_next_time_second_granularity() -> None:
    pattern = vcron.new_pattern("30 0 12 * * *")
    result = pattern.next_time(_dt(2024, 1, 1, 12, 0, 0), match_second=True)
    assert result == _dt(2024, 1, 1, 12, 0, 30)


def test_next_time_module_level() -> None:
    result = vcron.next_time("0 0 1 1 *", _dt(2024, 6, 1))
    assert result == _dt(2025, 1, 1, 0, 0)


def test_five_field_default_seconds_zero() -> None:
    pattern = vcron.new_pattern("0 12 * * *")
    # Second field defaults to 0, so only :00 matches when matching seconds.
    assert pattern.match(_dt(2024, 1, 1, 12, 0, 0), match_second=True) is True
    assert pattern.match(_dt(2024, 1, 1, 12, 0, 5), match_second=True) is False


def test_empty_expression_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("   ")


def test_wrong_field_count_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("0 0 0 0")


def test_out_of_range_value_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("99 * * * *")


def test_invalid_step_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("*/0 * * * *")


def test_invalid_number_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("abc * * * *")


def test_empty_sub_expression_raises() -> None:
    with pytest.raises(ValidationError):
        vcron.new_pattern("0 0 * * * | ")


def test_part_range_metadata() -> None:
    assert vcron.Part.MINUTE.min_value == 0
    assert vcron.Part.MINUTE.max_value == 59
    assert vcron.Part.MONTH.max_value == 12
