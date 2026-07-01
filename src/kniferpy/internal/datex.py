from __future__ import annotations

from datetime import datetime, timedelta

from kniferpy.verr import ValidationError

# Common strftime patterns aligned with knifer-go/vdate layouts.
NORM_PATTERN = "%Y-%m-%d %H:%M:%S"
NORM_DATE_PATTERN = "%Y-%m-%d"
NORM_TIME_PATTERN = "%H:%M:%S"
PURE_DATE_PATTERN = "%Y%m%d"
PURE_DATETIME_PATTERN = "%Y%m%d%H%M%S"
UTC_PATTERN = "%Y-%m-%dT%H:%M:%SZ"

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
    return value.replace(
        hour=23, minute=59, second=59, microsecond=_END_OF_DAY_MICROSECOND
    )


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
