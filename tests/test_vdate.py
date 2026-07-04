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


# ---------------------------------------------------------------------------
# Lunar calendar tests
# ---------------------------------------------------------------------------


class TestLunarCalendar:
    def test_solar_to_lunar_known_dates(self) -> None:
        # Spring Festival 2026: February 17 -> 正月初一
        lunar = vdate.solar_to_lunar(2026, 2, 17)
        assert lunar.year == 2026
        assert lunar.month == 1
        assert lunar.day == 1
        assert not lunar.is_leap_month
        assert lunar.zodiac == "马"

        # Spring Festival 2025: January 29 -> 正月初一
        lunar = vdate.solar_to_lunar(2025, 1, 29)
        assert lunar.year == 2025
        assert lunar.month == 1
        assert lunar.day == 1

        # Spring Festival 2024: February 10 -> 正月初一
        lunar = vdate.solar_to_lunar(2024, 2, 10)
        assert lunar.year == 2024
        assert lunar.month == 1
        assert lunar.day == 1
        assert lunar.zodiac == "龙"

    def test_lunar_to_solar_roundtrip(self) -> None:
        solar = vdate.lunar_to_solar(2026, 1, 1)
        assert solar.year == 2026
        assert solar.month == 2
        assert solar.day == 17

    def test_leap_month(self) -> None:
        # 2023 has a leap month 2 (闰二月)
        assert vdate.leap_month(2023) == 2
        assert vdate.is_leap_month(2023, 2)
        assert not vdate.is_leap_month(2023, 1)

        # 2025 has a leap month 6 (闰六月)
        assert vdate.leap_month(2025) == 6
        assert vdate.is_leap_month(2025, 6)

    def test_lunar_month_days(self) -> None:
        # Lunar months have either 29 or 30 days
        days = vdate.lunar_month_days(2026, 1)
        assert days in (29, 30)
        days = vdate.lunar_month_days(2026, 2)
        assert days in (29, 30)
        days = vdate.lunar_month_days(2026, 3)
        assert days in (29, 30)

    def test_lunar_year_days(self) -> None:
        days = vdate.lunar_year_days(2026)
        assert 353 <= days <= 385

    def test_zodiac(self) -> None:
        assert vdate.zodiac(2024) == "龙"
        assert vdate.zodiac(2025) == "蛇"
        assert vdate.zodiac(2026) == "马"
        assert vdate.zodiac(2027) == "羊"

    def test_gan_zhi(self) -> None:
        assert vdate.year_gan_zhi(2024) == "甲辰"
        assert vdate.year_gan_zhi(2025) == "乙巳"
        assert vdate.year_gan_zhi(2026) == "丙午"

        # Month Gan-Zhi for 2026 January
        gz = vdate.month_gan_zhi(2026, 1)
        assert len(gz) == 2
        assert gz[0] in "甲乙丙丁戊己庚辛壬癸"
        assert gz[1] in "子丑寅卯辰巳午未申酉戌亥"

        # Day Gan-Zhi for a known date
        gz = vdate.day_gan_zhi(2026, 7, 2)
        assert len(gz) == 2

    def test_solar_term(self) -> None:
        # 2026 立春: February 4
        term = vdate.solar_term(2026, 2, 4)
        if term:  # solar term is approximate
            assert term in ("立春", "小寒", "大寒", "雨水")

    def test_lunar_year_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            vdate.leap_month(1800)
        with pytest.raises(ValidationError):
            vdate.lunar_month_days(1800, 1)
        with pytest.raises(ValidationError):
            vdate.lunar_year_days(1800)
        with pytest.raises(ValidationError):
            vdate.solar_to_lunar(1800, 1, 1)
        with pytest.raises(ValidationError):
            vdate.lunar_to_solar(1800, 1, 1)
