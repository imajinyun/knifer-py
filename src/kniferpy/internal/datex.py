from __future__ import annotations

from datetime import datetime, timedelta

from kniferpy.verr import ValidationError

# Common strftime patterns aligned with knifer-go/vdate layouts.
NORM_PATTERN = "%Y-%m-%d %H:%M:%S"
NORM_DATE_PATTERN = "%Y-%m-%d"
NORM_TIME_PATTERN = "%H:%M:%S"
NORM_DATETIME_PATTERN = "%Y-%m-%d %H:%M:%S"
PURE_DATE_PATTERN = "%Y%m%d"
PURE_DATETIME_PATTERN = "%Y%m%d%H%M%S"
UTC_PATTERN = "%Y-%m-%dT%H:%M:%SZ"
HTTP_PATTERN = "%a, %d %b %Y %H:%M:%S GMT"

_PARSE_PATTERNS: tuple[str, ...] = (
    NORM_PATTERN,
    NORM_DATE_PATTERN,
    NORM_TIME_PATTERN,
    PURE_DATETIME_PATTERN,
    PURE_DATE_PATTERN,
    UTC_PATTERN,
    "%Y-%m-%dT%H:%M:%S%z",
    "%a, %d %b %Y %H:%M:%S %Z",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
)

_END_OF_DAY_MICROSECOND = 999_999


def now() -> datetime:
    return datetime.now()


def today() -> datetime:
    return begin_of_day(now())


def format_date(value: datetime, layout: str = "") -> str:
    if layout == "":
        layout = NORM_PATTERN
    return value.strftime(layout)


def format_norm(value: datetime) -> str:
    return value.strftime(NORM_PATTERN)


def format_date_only(value: datetime) -> str:
    return value.strftime(NORM_DATE_PATTERN)


def format_time_only(value: datetime) -> str:
    return value.strftime(NORM_TIME_PATTERN)


def parse(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValidationError(
            message="empty date string",
            code="knifer.date.empty",
        )
    for pattern in _PARSE_PATTERNS:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    raise ValidationError(
        message=f"unsupported date format: {value}",
        code="knifer.date.unsupported_format",
        context={"value": value},
    )


def parse_layout(value: str, layout: str) -> datetime:
    try:
        return datetime.strptime(value.strip(), layout)
    except ValueError as exc:
        raise ValidationError(
            message=f"parse date with layout failed: {value}",
            code="knifer.date.parse_failed",
            context={"value": value, "layout": layout},
        ) from exc


def begin_of_day(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(value: datetime) -> datetime:
    return value.replace(hour=23, minute=59, second=59, microsecond=_END_OF_DAY_MICROSECOND)


def begin_of_month(value: datetime) -> datetime:
    return begin_of_day(value).replace(day=1)


def end_of_month(value: datetime) -> datetime:
    first_next = offset_month(begin_of_month(value), 1)
    return end_of_day(first_next - timedelta(days=1))


def begin_of_year(value: datetime) -> datetime:
    return begin_of_day(value).replace(month=1, day=1)


def end_of_year(value: datetime) -> datetime:
    return end_of_day(value.replace(month=12, day=31))


def offset_day(value: datetime, days: int) -> datetime:
    return value + timedelta(days=days)


def offset_month(value: datetime, months: int) -> datetime:
    # Mirror Go's AddDate normalization: keep the day-of-month offset and let
    # overflow roll into the following month (e.g. Jan 31 + 1m -> Mar 3).
    total = (value.year * 12 + (value.month - 1)) + months
    year, month = divmod(total, 12)
    first = value.replace(year=year, month=month + 1, day=1)
    return first + timedelta(days=value.day - 1)


def offset_year(value: datetime, years: int) -> datetime:
    return offset_month(value, years * 12)


def offset_hour(value: datetime, hours: int) -> datetime:
    return value + timedelta(hours=hours)


def offset_minute(value: datetime, minutes: int) -> datetime:
    return value + timedelta(minutes=minutes)


def offset_second(value: datetime, seconds: int) -> datetime:
    return value + timedelta(seconds=seconds)


def between_days(a: datetime, b: datetime) -> int:
    return abs(b - a).days


def is_same_day(a: datetime, b: datetime) -> bool:
    return a.date() == b.date()


# ---------------------------------------------------------------------------
# Chinese lunar calendar, Gan-Zhi and Solar Terms
# ---------------------------------------------------------------------------

_MIN_LUNAR_YEAR = 1900
_MAX_LUNAR_YEAR = 2100
_LUNAR_BASE_DATE = datetime(1900, 1, 31)

_HEAVENLY_STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
_EARTHLY_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
_ZODIAC_ANIMALS = ("鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪")

_SOLAR_TERM_NAMES = (
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
    "冬至",
)

_SOLAR_TERM_MINUTES = (
    0,
    21208,
    42467,
    63836,
    85337,
    107014,
    128867,
    150921,
    173149,
    195551,
    218072,
    240693,
    263343,
    285989,
    308563,
    331033,
    353350,
    375494,
    397447,
    419210,
    440795,
    462224,
    483532,
    504758,
)

_LUNAR_INFO = (
    0x04BD8,
    0x04AE0,
    0x0A570,
    0x054D5,
    0x0D260,
    0x0D950,
    0x16554,
    0x056A0,
    0x09AD0,
    0x055D2,
    0x04AE0,
    0x0A5B6,
    0x0A4D0,
    0x0D250,
    0x1D255,
    0x0B540,
    0x0D6A0,
    0x0ADA2,
    0x095B0,
    0x14977,
    0x04970,
    0x0A4B0,
    0x0B4B5,
    0x06A50,
    0x06D40,
    0x1AB54,
    0x02B60,
    0x09570,
    0x052F2,
    0x04970,
    0x06566,
    0x0D4A0,
    0x0EA50,
    0x06E95,
    0x05AD0,
    0x02B60,
    0x186E3,
    0x092E0,
    0x1C8D7,
    0x0C950,
    0x0D4A0,
    0x1D8A6,
    0x0B550,
    0x056A0,
    0x1A5B4,
    0x025D0,
    0x092D0,
    0x0D2B2,
    0x0A950,
    0x0B557,
    0x06CA0,
    0x0B550,
    0x15355,
    0x04DA0,
    0x0A5D0,
    0x14573,
    0x052D0,
    0x0A9A8,
    0x0E950,
    0x06AA0,
    0x0AEA6,
    0x0AB50,
    0x04B60,
    0x0AAE4,
    0x0A570,
    0x05260,
    0x0F263,
    0x0D950,
    0x05B57,
    0x056A0,
    0x096D0,
    0x04DD5,
    0x04AD0,
    0x0A4D0,
    0x0D4D4,
    0x0D250,
    0x0D558,
    0x0B540,
    0x0B6A0,
    0x195A6,
    0x095B0,
    0x049B0,
    0x0A974,
    0x0A4B0,
    0x0B27A,
    0x06A50,
    0x06D40,
    0x0AF46,
    0x0AB60,
    0x09570,
    0x04AF5,
    0x04970,
    0x064B0,
    0x074A3,
    0x0EA50,
    0x06B58,
    0x05AC0,
    0x0AB60,
    0x096D5,
    0x092E0,
    0x0C960,
    0x0D954,
    0x0D4A0,
    0x0DA50,
    0x07552,
    0x056A0,
    0x0ABB7,
    0x025D0,
    0x092D0,
    0x0CAB5,
    0x0A950,
    0x0B4A0,
    0x0BAA4,
    0x0AD50,
    0x055D9,
    0x04BA0,
    0x0A5B0,
    0x15176,
    0x052B0,
    0x0A930,
    0x07954,
    0x06AA0,
    0x0AD50,
    0x05B52,
    0x04B60,
    0x0A6E6,
    0x0A4E0,
    0x0D260,
    0x0EA65,
    0x0D530,
    0x05AA0,
    0x076A3,
    0x096D0,
    0x04BD7,
    0x04AD0,
    0x0A4D0,
    0x1D0B6,
    0x0D250,
    0x0D520,
    0x0DD45,
    0x0B5A0,
    0x056D0,
    0x055B2,
    0x049B0,
    0x0A577,
    0x0A4B0,
    0x0AA50,
    0x1B255,
    0x06D20,
    0x0ADA0,
    0x14B63,
    0x09370,
    0x049F8,
    0x04970,
    0x064B0,
    0x168A6,
    0x0EA50,
    0x06B20,
    0x1A6C4,
    0x0AAE0,
    0x0A2E0,
    0x0D2E3,
    0x0C960,
    0x0D557,
    0x0D4A0,
    0x0DA50,
    0x05D55,
    0x056A0,
    0x0A6D0,
    0x055D4,
    0x052D0,
    0x0A9B8,
    0x0A950,
    0x0B4A0,
    0x0B6A6,
    0x0AD50,
    0x055A0,
    0x0ABA4,
    0x0A5B0,
    0x052B0,
    0x0B273,
    0x06930,
    0x07337,
    0x06AA0,
    0x0AD50,
    0x14B55,
    0x04B60,
    0x0A570,
    0x054E4,
    0x0D160,
    0x0E968,
    0x0D520,
    0x0DAA0,
    0x16AA6,
    0x056D0,
    0x04AE0,
    0x0A9D4,
    0x0A2D0,
    0x0D150,
    0x0F252,
    0x0D520,
)


class SolarDate:
    """Gregorian calendar date."""

    __slots__ = ("year", "month", "day")

    def __init__(self, year: int, month: int, day: int) -> None:
        self.year = year
        self.month = month
        self.day = day

    def __repr__(self) -> str:
        return f"SolarDate({self.year}, {self.month}, {self.day})"


class LunarDate:
    """Chinese lunar calendar date."""

    __slots__ = (
        "year",
        "month",
        "day",
        "is_leap_month",
        "year_gan_zhi",
        "month_gan_zhi",
        "day_gan_zhi",
        "zodiac",
    )

    def __init__(
        self,
        year: int,
        month: int,
        day: int,
        is_leap_month: bool = False,
        year_gan_zhi: str = "",
        month_gan_zhi: str = "",
        day_gan_zhi: str = "",
        zodiac: str = "",
    ) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.is_leap_month = is_leap_month
        self.year_gan_zhi = year_gan_zhi
        self.month_gan_zhi = month_gan_zhi
        self.day_gan_zhi = day_gan_zhi
        self.zodiac = zodiac

    def __repr__(self) -> str:
        return (
            f"LunarDate({self.year}, {self.month}, {self.day}, "
            f"leap={self.is_leap_month}, gz={self.year_gan_zhi}, z={self.zodiac})"
        )


def _lunar_year_days(year: int) -> int:
    """Total days in a lunar year."""
    info = _LUNAR_INFO[year - _MIN_LUNAR_YEAR]
    total = 348  # 12 * 29
    bit = 0x8000
    while bit > 0x8:
        if info & bit:
            total += 1
        bit >>= 1
    leap = info & 0xF
    if leap:
        total += 30 if (info & 0x10000) else 29
    return total


def _lunar_month_days(year: int, month: int, is_leap: bool = False) -> int:
    info = _LUNAR_INFO[year - _MIN_LUNAR_YEAR]
    if is_leap:
        if (info & 0xF) != month:
            return 0
        return 30 if (info & 0x10000) else 29
    return 30 if (info & (0x10000 >> month)) else 29


def leap_month(year: int) -> int:
    """Return the leap month number for a lunar year (0 if none)."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR:
        raise ValidationError(
            message=f"lunar year out of range [{_MIN_LUNAR_YEAR}, {_MAX_LUNAR_YEAR}]: {year}",
            code="knifer.date.lunar_year_range",
            context={"year": year},
        )
    return _LUNAR_INFO[year - _MIN_LUNAR_YEAR] & 0xF


def is_leap_month(year: int, month: int) -> bool:
    """Check if a month is a leap month in a lunar year."""
    return (
        _MIN_LUNAR_YEAR <= year <= _MAX_LUNAR_YEAR
        and 1 <= month <= 12
        and leap_month(year) == month
    )


def lunar_month_days(year: int, month: int, is_leap: bool = False) -> int:
    """Return the number of days in a lunar month."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR:
        raise ValidationError(
            message=f"lunar year out of range [{_MIN_LUNAR_YEAR}, {_MAX_LUNAR_YEAR}]: {year}",
            code="knifer.date.lunar_year_range",
            context={"year": year},
        )
    if month < 1 or month > 12:
        raise ValidationError(
            message=f"lunar month out of range [1,12]: {month}",
            code="knifer.date.lunar_month_range",
            context={"month": month},
        )
    return _lunar_month_days(year, month, is_leap)


def lunar_year_days(year: int) -> int:
    """Return the total number of days in a lunar year."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR:
        raise ValidationError(
            message=f"lunar year out of range [{_MIN_LUNAR_YEAR}, {_MAX_LUNAR_YEAR}]: {year}",
            code="knifer.date.lunar_year_range",
            context={"year": year},
        )
    return _lunar_year_days(year)


def _gan_zhi(offset: int) -> str:
    offset %= 60
    if offset < 0:
        offset += 60
    return _HEAVENLY_STEMS[offset % 10] + _EARTHLY_BRANCHES[offset % 12]


def _solar_term_day(year: int, term_index: int) -> int:
    """Return the day of month for a solar term."""
    _TROPICAL_YEAR_MILLIS = 31556925974.7
    base = datetime(1900, 1, 6, 2, 5, 0)
    millis = _TROPICAL_YEAR_MILLIS * (year - 1900) + _SOLAR_TERM_MINUTES[term_index] * 60 * 1000
    delta = timedelta(milliseconds=millis)
    return (base + delta).day


def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    """Convert a Gregorian date to a Chinese lunar date."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR:
        raise ValidationError(
            message=f"solar year out of range [{_MIN_LUNAR_YEAR}, {_MAX_LUNAR_YEAR}]: {year}",
            code="knifer.date.lunar_year_range",
            context={"year": year},
        )

    target = datetime(year, month, day)
    offset = (target - _LUNAR_BASE_DATE).days

    # Find the lunar year
    lunar_y = _MIN_LUNAR_YEAR
    while lunar_y <= _MAX_LUNAR_YEAR:
        days = lunar_year_days(lunar_y)
        if offset < days:
            break
        offset -= days
        lunar_y += 1

    leap = leap_month(lunar_y)
    is_leap = False
    lunar_m = 1
    while lunar_m <= 12:
        m_days = lunar_month_days(lunar_y, lunar_m, is_leap)
        if offset < m_days:
            break
        offset -= m_days
        if leap == lunar_m and not is_leap:
            is_leap = True
            lunar_m -= 1
        else:
            is_leap = False
        lunar_m += 1

    lunar_day = offset + 1
    solar = datetime(year, month, day)

    return LunarDate(
        year=lunar_y,
        month=lunar_m,
        day=lunar_day,
        is_leap_month=is_leap,
        year_gan_zhi=year_gan_zhi(lunar_y),
        month_gan_zhi=month_gan_zhi(solar.year, solar.month),
        day_gan_zhi=day_gan_zhi(solar.year, solar.month, solar.day),
        zodiac=zodiac(lunar_y),
    )


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> SolarDate:
    """Convert a Chinese lunar date to a Gregorian date."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR:
        raise ValidationError(
            message=f"lunar year out of range [{_MIN_LUNAR_YEAR}, {_MAX_LUNAR_YEAR}]: {year}",
            code="knifer.date.lunar_year_range",
            context={"year": year},
        )
    if month < 1 or month > 12:
        raise ValidationError(
            message=f"invalid lunar month: {month}",
            code="knifer.date.lunar_month_range",
            context={"month": month},
        )
    if is_leap and leap_month(year) != month:
        raise ValidationError(
            message=f"lunar year {year} has no leap month {month}",
            code="knifer.date.no_leap_month",
            context={"year": year, "month": month},
        )
    month_days = lunar_month_days(year, month, is_leap)
    if day < 1 or day > month_days:
        raise ValidationError(
            message=f"invalid lunar day: {day}",
            code="knifer.date.invalid_lunar_day",
            context={"day": day},
        )

    offset = 0
    for y in range(_MIN_LUNAR_YEAR, year):
        offset += lunar_year_days(y)

    leap = leap_month(year)
    for m in range(1, month):
        offset += lunar_month_days(year, m, False)
        if leap == m:
            offset += lunar_month_days(year, m, True)

    if is_leap:
        offset += lunar_month_days(year, month, False)

    offset += day - 1
    result = _LUNAR_BASE_DATE + timedelta(days=offset)
    return SolarDate(result.year, result.month, result.day)


def zodiac(year: int) -> str:
    """Return the Chinese zodiac animal for a given year."""
    if year <= 0:
        return ""
    return _ZODIAC_ANIMALS[(year - 4) % 12]


def year_gan_zhi(year: int) -> str:
    """Return the Gan-Zhi (Heavenly Stem + Earthly Branch) of a year."""
    if year <= 0:
        return ""
    return _gan_zhi(year - 4)


def month_gan_zhi(year: int, month: int) -> str:
    """Return the Gan-Zhi of a month in a given year."""
    if year <= 0 or month < 1 or month > 12:
        return ""
    stem = (year * 2 + month + 3) % 10
    branch = (month + 1) % 12
    return _HEAVENLY_STEMS[stem] + _EARTHLY_BRANCHES[branch]


def day_gan_zhi(year: int, month: int, day: int) -> str:
    """Return the Gan-Zhi of a specific day."""
    target = datetime(year, month, day)
    offset = (target - _LUNAR_BASE_DATE).days
    return _gan_zhi(offset + 40)


def solar_term(year: int, month: int, day: int) -> str:
    """Return the solar term name for a given date, or empty string."""
    if year < _MIN_LUNAR_YEAR or year > _MAX_LUNAR_YEAR or month < 1 or month > 12:
        return ""
    for i in range((month - 1) * 2, (month - 1) * 2 + 2):
        if _solar_term_day(year, i) == day:
            return _SOLAR_TERM_NAMES[i]
    return ""
