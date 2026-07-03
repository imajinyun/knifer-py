"""Cron expression parsing and matching.

Parse cron expressions and test whether a :class:`~datetime.datetime` matches,
or compute the next matching moment. Supports 5-, 6-, and 7-field expressions,
lists, ranges, steps, wildcards, month and weekday aliases, ``|`` alternatives,
and the ``L`` last-day-of-month token.

Only the pure expression logic is ported; the goroutine-based scheduler,
timer, and executor from knifer-go are intentionally omitted. Combine
:func:`next_time` with the standard library ``sched``/``asyncio`` when you need
to run tasks.
"""

from __future__ import annotations

from datetime import datetime

from kniferpy.internal import cronx
from kniferpy.internal.cronx import Part, Pattern

__all__ = [
    "Part",
    "Pattern",
    "match",
    "must_new_pattern",
    "new_pattern",
    "next_time",
]


def new_pattern(expr: str) -> Pattern:
    """Parse ``expr`` into a :class:`Pattern`."""
    return cronx.new_pattern(expr)


def must_new_pattern(expr: str) -> Pattern:
    """Parse ``expr`` into a :class:`Pattern`, raising on any error."""
    return cronx.must_new_pattern(expr)


def match(expr: str, moment: datetime, match_second: bool = False) -> bool:
    """Parse ``expr`` and report whether ``moment`` matches it."""
    return cronx.match(expr, moment, match_second)


def next_time(expr: str, after: datetime, match_second: bool = False) -> datetime | None:
    """Parse ``expr`` and return the first matching moment after ``after``."""
    return cronx.next_time(expr, after, match_second)
