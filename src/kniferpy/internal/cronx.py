from __future__ import annotations

from datetime import datetime, timedelta
from enum import IntEnum

from kniferpy.verr import ValidationError

# The day-of-month field uses 32 as the sentinel for the ``L`` (last day) token.
_LAST_DAY_SENTINEL = 32

_MONTH_ALIAS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Weekday aliases run Sunday=0 through Saturday=6, matching Go's time.Weekday.
_WEEK_ALIAS = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}


class Part(IntEnum):
    """A cron field position, ordered second through year."""

    SECOND = 0
    MINUTE = 1
    HOUR = 2
    DAY_OF_MONTH = 3
    MONTH = 4
    DAY_OF_WEEK = 5
    YEAR = 6

    @property
    def min_value(self) -> int:
        """Return the minimum valid value for this field."""
        return _PART_RANGES[self][0]

    @property
    def max_value(self) -> int:
        """Return the maximum valid value for this field."""
        return _PART_RANGES[self][1]

    def check_value(self, value: int) -> None:
        """Raise :class:`ValidationError` when ``value`` is out of range."""
        low, high = _PART_RANGES[self]
        if value < low or value > high:
            raise ValidationError(
                message=(
                    f"value {value} out of range [{low}, {high}] for part {self.name.lower()}"
                ),
                code="knifer.cron.out_of_range",
            )


_PART_RANGES: dict[Part, tuple[int, int]] = {
    Part.SECOND: (0, 59),
    Part.MINUTE: (0, 59),
    Part.HOUR: (0, 23),
    Part.DAY_OF_MONTH: (1, 32),  # 32 is the sentinel for "L".
    Part.MONTH: (1, 12),
    Part.DAY_OF_WEEK: (0, 6),
    Part.YEAR: (1970, 2099),
}

# Field parse order for a full seven-field expression.
_PART_ORDER = (
    Part.SECOND,
    Part.MINUTE,
    Part.HOUR,
    Part.DAY_OF_MONTH,
    Part.MONTH,
    Part.DAY_OF_WEEK,
    Part.YEAR,
)


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _last_day_of_month(month: int, leap: bool) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if month == 2:
        return 29 if leap else 28
    return 31


def _cron_error(message: str) -> ValidationError:
    return ValidationError(message=message, code="knifer.cron.invalid")


def _enumerate(begin: int, end: int, step: int) -> list[int]:
    """Return values in ``[begin, end]`` advancing by ``step`` (inclusive)."""
    if step <= 0:
        step = 1
    if begin > end:
        return []
    return list(range(begin, end + 1, step))


def _parse_int(text: str) -> int:
    """Parse an integer the way Go's strconv.Atoi does (no surrounding space)."""
    stripped = text.strip()
    if stripped != text or not stripped:
        raise ValueError(f"invalid integer {text!r}")
    # Reject floats and other non-integer forms.
    body = stripped[1:] if stripped[:1] in "+-" else stripped
    if not body.isdigit():
        raise ValueError(f"invalid integer {text!r}")
    return int(stripped)


def _parse_single(part: Part, value: str) -> int:
    """Parse one number, alias, ``L`` token, or negative wrap-around value."""
    v = value.strip()
    if not v:
        raise _cron_error("empty value")
    lower = v.lower()
    if lower == "l":
        return part.max_value
    if part is Part.MONTH and lower in _MONTH_ALIAS:
        return _MONTH_ALIAS[lower]
    if part is Part.DAY_OF_WEEK and lower in _WEEK_ALIAS:
        return _WEEK_ALIAS[lower]
    try:
        n = _parse_int(v)
    except ValueError as exc:
        raise _cron_error(f"invalid number {v!r}") from exc
    # Weekday 7 is an alias for Sunday (0).
    if part is Part.DAY_OF_WEEK and n == 7:
        n = 0
    # Negative values count back from the field maximum.
    if n < 0:
        n += part.max_value
    part.check_value(n)
    return n


def _parse_range(part: Part, value: str, step: int) -> list[int]:
    """Parse forms such as ``a``, ``a-b``, ``*``, and ``?``."""
    if value in ("*", "?"):
        return _enumerate(part.min_value, part.max_value, step)

    # Single value (including a lone negative like "-3").
    if "-" not in value or (value.startswith("-") and value.count("-") == 1):
        single = _parse_single(part, value)
        if step == 1:
            return [single]
        return _enumerate(single, part.max_value, step)

    # Range a-b; a leading '-' marks a negative start value.
    idx = value.find("-")
    if value[0] == "-":
        rest = value[1:].find("-")
        idx = rest + 1 if rest >= 0 else -1
    if idx < 0:
        return [_parse_single(part, value)]

    begin = _parse_single(part, value[:idx])
    end = _parse_single(part, value[idx + 1 :])
    if begin <= end:
        return _enumerate(begin, end, step)
    # A reversed range b-a wraps: [b..max] followed by [min..a].
    return _enumerate(begin, part.max_value, step) + _enumerate(part.min_value, end, step)


def _parse_range_step(part: Part, value: str) -> list[int]:
    """Parse forms such as ``a/n``, ``*/n``, and ``a-b/n``."""
    step = 1
    range_str = value
    slash = value.find("/")
    if slash >= 0:
        range_str = value[:slash]
        step_str = value[slash + 1 :]
        try:
            step = _parse_int(step_str)
        except ValueError as exc:
            raise _cron_error(f"invalid step {step_str!r}") from exc
        if step <= 0:
            raise _cron_error(f"invalid step {step_str!r}")
    return _parse_range(part, range_str, step)


def _parse_part_values(part: Part, value: str) -> list[int]:
    """Parse a comma-separated field into the set of matchable values."""
    result: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            raise _cron_error(f"empty list element in {value!r}")
        result.extend(_parse_range_step(part, token))
    return result


class _Matcher:
    """Matches a numeric field value against a fixed set."""

    __slots__ = ("_values",)

    def __init__(self, values: list[int]) -> None:
        self._values = frozenset(values)

    def matches(self, value: int) -> bool:
        return value in self._values


class _AlwaysMatcher(_Matcher):
    """Matches every value (the ``*`` and ``?`` fields)."""

    def __init__(self) -> None:  # noqa: D107 - trivial override
        super().__init__([])

    def matches(self, value: int) -> bool:
        return True


class _DayOfMonthMatcher(_Matcher):
    """Matches a day-of-month value, honoring the ``L`` last-day token."""

    __slots__ = ("_is_last",)

    def __init__(self, values: list[int]) -> None:
        super().__init__(values)
        self._is_last = _LAST_DAY_SENTINEL in self._values

    def matches_day(self, day: int, month: int, leap: bool) -> bool:
        if self.matches(day):
            return True
        return self._is_last and day == _last_day_of_month(month, leap)


def _new_matcher(part: Part, value: str) -> _Matcher:
    value = value.strip()
    if not value:
        raise _cron_error("empty cron field")
    values = _parse_part_values(part, value)
    if part is Part.DAY_OF_MONTH:
        return _DayOfMonthMatcher(values)
    return _Matcher(values)


def _new_pattern_matchers(expr: str) -> tuple[_Matcher, ...]:
    """Parse one ``|``-free expression into seven field matchers."""
    parts = expr.split()
    count = len(parts)
    if count == 5:
        # minute hour dom month dow -> add a leading second and a trailing year.
        parts = ["0", *parts, "*"]
    elif count == 6:
        # second minute hour dom month dow -> add a trailing year.
        parts = [*parts, "*"]
    elif count != 7:
        raise _cron_error(f"invalid cron expression {expr!r} (parts={count})")

    matchers: list[_Matcher] = []
    for part, raw in zip(_PART_ORDER, parts):
        if raw in ("*", "?"):
            matchers.append(_AlwaysMatcher())
        else:
            matchers.append(_new_matcher(part, raw))
    return tuple(matchers)


def _fields_of(moment: datetime, match_second: bool) -> tuple[int, int, int, int, int, int, int]:
    """Return ``(second, minute, hour, day, month, weekday, year)`` for matching.

    Weekday runs Sunday=0 through Saturday=6; ``second`` is -1 when ignored.
    """
    second = moment.second if match_second else -1
    weekday = moment.isoweekday() % 7  # Monday..Sunday -> 1..6, 0 for Sunday.
    return (
        second,
        moment.minute,
        moment.hour,
        moment.day,
        moment.month,
        weekday,
        moment.year,
    )


class Pattern:
    """A parsed cron expression supporting ``|``-separated alternatives.

    Accepts 5-field (``min hour dom month dow``), 6-field (leading seconds), or
    7-field (trailing year) expressions. Supports lists (``,``), ranges (``-``),
    steps (``/``), wildcards (``*``/``?``), month and weekday aliases, and the
    ``L`` last-day-of-month token.
    """

    __slots__ = ("_groups", "_raw")

    def __init__(self, expr: str) -> None:
        expr = expr.strip()
        if not expr:
            raise _cron_error("empty cron expression")
        groups: list[tuple[_Matcher, ...]] = []
        for group in expr.split("|"):
            group = group.strip()
            if not group:
                raise _cron_error(f"empty sub-expression in {expr!r}")
            groups.append(_new_pattern_matchers(group))
        self._raw = expr
        self._groups = tuple(groups)

    @property
    def raw(self) -> str:
        """Return the original expression string."""
        return self._raw

    def _group_matches(self, group: tuple[_Matcher, ...], fields: tuple[int, ...]) -> bool:
        second, minute, hour, day, month, weekday, year = fields
        if second >= 0 and not group[Part.SECOND].matches(second):
            return False
        if not group[Part.MINUTE].matches(minute):
            return False
        if not group[Part.HOUR].matches(hour):
            return False
        dom = group[Part.DAY_OF_MONTH]
        if isinstance(dom, _DayOfMonthMatcher):
            if not dom.matches_day(day, month, _is_leap_year(year)):
                return False
        elif not dom.matches(day):
            return False
        if not group[Part.MONTH].matches(month):
            return False
        if not group[Part.DAY_OF_WEEK].matches(weekday):
            return False
        return group[Part.YEAR].matches(year)

    def match(self, moment: datetime, match_second: bool = False) -> bool:
        """Report whether ``moment`` satisfies the pattern.

        When ``match_second`` is false the seconds field is ignored.
        """
        fields = _fields_of(moment, match_second)
        return any(self._group_matches(group, fields) for group in self._groups)

    def next_time(self, after: datetime, match_second: bool = False) -> datetime | None:
        """Return the first matching moment strictly after ``after``.

        Scans forward one minute (or one second when ``match_second`` is true)
        at a time. Returns ``None`` when no match occurs before the supported
        year range (2099) is exceeded.
        """
        step = timedelta(seconds=1) if match_second else timedelta(minutes=1)
        if match_second:
            current = after.replace(microsecond=0) + step
        else:
            current = after.replace(second=0, microsecond=0) + step
        max_year = Part.YEAR.max_value
        while current.year <= max_year:
            if self.match(current, match_second):
                return current
            current += step
        return None


def new_pattern(expr: str) -> Pattern:
    """Parse ``expr`` into a :class:`Pattern`."""
    return Pattern(expr)


def must_new_pattern(expr: str) -> Pattern:
    """Parse ``expr`` into a :class:`Pattern`, raising on any error."""
    return Pattern(expr)


def match(expr: str, moment: datetime, match_second: bool = False) -> bool:
    """Parse ``expr`` and report whether ``moment`` matches it."""
    return Pattern(expr).match(moment, match_second)


def next_time(expr: str, after: datetime, match_second: bool = False) -> datetime | None:
    """Parse ``expr`` and return the first matching moment after ``after``."""
    return Pattern(expr).next_time(after, match_second)
