from datetime import datetime

import pytest

from kniferpy import vdate
from kniferpy.verr import ValidationError


def test_format_helpers() -> None:
    value = datetime(2026, 7, 2, 13, 45, 30)
    assert vdate.format_norm(value) == "2026-07-02 13:45:30"
    assert vdate.format_date_only(value) == "2026-07-02"
    assert vdate.format_time_only(value) == "13:45:30"
    assert vdate.format_date(value) == "2026-07-02 13:45:30"
    assert vdate.format_date(value, "%Y%m%d") == "20260702"


def test_parse_common_formats() -> None:
    assert vdate.parse("2026-07-02 13:45:30") == datetime(2026, 7, 2, 13, 45, 30)
    assert vdate.parse("2026-07-02") == datetime(2026, 7, 2)
    assert vdate.parse("20260702") == datetime(2026, 7, 2)
    assert vdate.parse(" 2026/07/02 ") == datetime(2026, 7, 2)
    with pytest.raises(ValidationError):
        vdate.parse("")
    with pytest.raises(ValidationError):
        vdate.parse("not-a-date")


def test_parse_layout() -> None:
    assert vdate.parse_layout("02.07.2026", "%d.%m.%Y") == datetime(2026, 7, 2)
    with pytest.raises(ValidationError):
        vdate.parse_layout("bad", "%d.%m.%Y")


def test_begin_end_of_periods() -> None:
    value = datetime(2026, 2, 15, 8, 30, 0)
    assert vdate.begin_of_day(value) == datetime(2026, 2, 15, 0, 0, 0, 0)
    assert vdate.end_of_day(value) == datetime(2026, 2, 15, 23, 59, 59, 999_999)
    assert vdate.begin_of_month(value) == datetime(2026, 2, 1, 0, 0, 0, 0)
    # 2026 is not a leap year: February ends on the 28th.
    assert vdate.end_of_month(value) == datetime(2026, 2, 28, 23, 59, 59, 999_999)
    assert vdate.begin_of_year(value) == datetime(2026, 1, 1, 0, 0, 0, 0)
    assert vdate.end_of_year(value) == datetime(2026, 12, 31, 23, 59, 59, 999_999)


def test_offsets() -> None:
    value = datetime(2026, 7, 2, 12, 0, 0)
    assert vdate.offset_day(value, 3) == datetime(2026, 7, 5, 12, 0, 0)
    assert vdate.offset_day(value, -2) == datetime(2026, 6, 30, 12, 0, 0)
    assert vdate.offset_month(value, 6) == datetime(2027, 1, 2, 12, 0, 0)
    assert vdate.offset_year(value, 1) == datetime(2027, 7, 2, 12, 0, 0)
    assert vdate.offset_hour(value, 13) == datetime(2026, 7, 3, 1, 0, 0)
    assert vdate.offset_minute(value, 90) == datetime(2026, 7, 2, 13, 30, 0)
    assert vdate.offset_second(value, 61) == datetime(2026, 7, 2, 12, 1, 1)


def test_offset_month_overflow() -> None:
    # Mirror Go AddDate: Jan 31 + 1 month rolls into March.
    assert vdate.offset_month(datetime(2026, 1, 31), 1) == datetime(2026, 3, 3)


def test_between_and_same_day() -> None:
    a = datetime(2026, 7, 2, 23, 0, 0)
    b = datetime(2026, 7, 5, 1, 0, 0)
    assert vdate.between_days(a, b) == 2
    assert vdate.between_days(b, a) == 2
    assert vdate.is_same_day(a, datetime(2026, 7, 2, 1, 0, 0))
    assert not vdate.is_same_day(a, b)


def test_now_and_today() -> None:
    current = vdate.now()
    start = vdate.today()
    assert isinstance(current, datetime)
    assert start == vdate.begin_of_day(start)
    assert vdate.is_same_day(current, start)
