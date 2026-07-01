from __future__ import annotations

from datetime import datetime

from kniferpy.internal import datex
from kniferpy.internal.datex import (
    NORM_DATE_PATTERN,
    NORM_PATTERN,
    NORM_TIME_PATTERN,
    PURE_DATE_PATTERN,
    PURE_DATETIME_PATTERN,
    UTC_PATTERN,
)

__all__ = [
    "NORM_PATTERN",
    "NORM_DATE_PATTERN",
    "NORM_TIME_PATTERN",
    "PURE_DATE_PATTERN",
    "PURE_DATETIME_PATTERN",
    "UTC_PATTERN",
    "now",
    "today",
    "format_date",
    "format_norm",
    "format_date_only",
    "format_time_only",
    "parse",
    "parse_layout",
    "begin_of_day",
    "end_of_day",
    "begin_of_month",
    "end_of_month",
    "begin_of_year",
    "end_of_year",
    "offset_day",
    "offset_month",
    "offset_year",
    "offset_hour",
    "offset_minute",
    "offset_second",
    "between_days",
    "is_same_day",
]


def now() -> datetime:
    return datex.now()


def today() -> datetime:
    return datex.today()


def format_date(value: datetime, layout: str = "") -> str:
    return datex.format_date(value, layout)


def format_norm(value: datetime) -> str:
    return datex.format_norm(value)


def format_date_only(value: datetime) -> str:
    return datex.format_date_only(value)


def format_time_only(value: datetime) -> str:
    return datex.format_time_only(value)


def parse(value: str) -> datetime:
    return datex.parse(value)


def parse_layout(value: str, layout: str) -> datetime:
    return datex.parse_layout(value, layout)


def begin_of_day(value: datetime) -> datetime:
    return datex.begin_of_day(value)


def end_of_day(value: datetime) -> datetime:
    return datex.end_of_day(value)


def begin_of_month(value: datetime) -> datetime:
    return datex.begin_of_month(value)


def end_of_month(value: datetime) -> datetime:
    return datex.end_of_month(value)


def begin_of_year(value: datetime) -> datetime:
    return datex.begin_of_year(value)


def end_of_year(value: datetime) -> datetime:
    return datex.end_of_year(value)


def offset_day(value: datetime, days: int) -> datetime:
    return datex.offset_day(value, days)


def offset_month(value: datetime, months: int) -> datetime:
    return datex.offset_month(value, months)


def offset_year(value: datetime, years: int) -> datetime:
    return datex.offset_year(value, years)


def offset_hour(value: datetime, hours: int) -> datetime:
    return datex.offset_hour(value, hours)


def offset_minute(value: datetime, minutes: int) -> datetime:
    return datex.offset_minute(value, minutes)


def offset_second(value: datetime, seconds: int) -> datetime:
    return datex.offset_second(value, seconds)


def between_days(a: datetime, b: datetime) -> int:
    return datex.between_days(a, b)


def is_same_day(a: datetime, b: datetime) -> bool:
    return datex.is_same_day(a, b)
