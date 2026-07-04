"""Cron expression parsing, matching, and scheduling.

Parse cron expressions and test whether a :class:`~datetime.datetime` matches,
compute the next matching moment, or schedule recurring tasks using a built-in
scheduler.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from kniferpy.internal import cronx
from kniferpy.internal.cronx import (
    CronTask,
    Part,
    Pattern,
    Scheduler,
    SimpleTaskListener,
    Task,
    TaskFunc,
    TaskListener,
    TaskTable,
    configure_default_scheduler,
    remove,
    restart,
    running_count,
    schedule,
    schedule_func,
    schedule_with_id,
    set_match_second,
    shutdown,
    start,
    stop,
    update_pattern,
)

__all__ = [
    "Part",
    "Pattern",
    "CronTask",
    "Scheduler",
    "Task",
    "TaskFunc",
    "TaskListener",
    "SimpleTaskListener",
    "TaskTable",
    "match",
    "must_new_pattern",
    "new_pattern",
    "next_time",
    # Global scheduler
    "configure_default_scheduler",
    "schedule",
    "schedule_func",
    "schedule_with_id",
    "remove",
    "update_pattern",
    "start",
    "stop",
    "shutdown",
    "restart",
    "set_match_second",
    "running_count",
]


def new_pattern(expr: str) -> Pattern:
    return cronx.new_pattern(expr)


def must_new_pattern(expr: str) -> Pattern:
    return cronx.must_new_pattern(expr)


def match(expr: str, moment: datetime, match_second: bool = False) -> bool:
    return cronx.match(expr, moment, match_second)


def next_time(expr: str, after: datetime, match_second: bool = False) -> datetime | None:
    return cronx.next_time(expr, after, match_second)