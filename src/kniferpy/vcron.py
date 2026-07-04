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
    ERR_SCHEDULER_STARTED,
    AlwaysTrueMatcher,
    Config,
    CronError,
    CronTask,
    Part,
    PartDayOfMonth,
    PartDayOfWeek,
    PartHour,
    PartMatcher,
    PartMinute,
    PartMonth,
    PartSecond,
    PartYear,
    Pattern,
    Scheduler,
    SimpleTaskListener,
    Task,
    TaskExecutor,
    TaskFunc,
    TaskListener,
    TaskTable,
    configure_default_scheduler,
    cron_schedule_func,
    cron_set_match_second,
    cron_set_match_second_e,
    new_cron_error,
    new_task_table,
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
    wrap_cron_error,
)

# ── Go-compat option type aliases ──────────────────────────────────────────────

from typing import Any, Callable as _Callable

SchedulerOption = _Callable[[Any], None]
DefaultSchedulerOption = _Callable[[Any], None]
ConfigOption = _Callable[[Any], None]
PatternOption = _Callable[[Any], None]

__all__ = [
    # Types
    "Part",
    "PartMatcher",
    "Pattern",
    "Config",
    "CronError",
    "CronTask",
    "TaskExecutor",
    "Scheduler",
    "Task",
    "TaskFunc",
    "TaskListener",
    "SimpleTaskListener",
    "TaskTable",
    # Part constants
    "PartSecond",
    "PartMinute",
    "PartHour",
    "PartDayOfMonth",
    "PartMonth",
    "PartDayOfWeek",
    "PartYear",
    # Matcher singleton
    "AlwaysTrueMatcher",
    # Error sentinel
    "ERR_SCHEDULER_STARTED",
    # Pattern functions
    "match",
    "must_new_pattern",
    "new_pattern",
    "next_time",
    # Global scheduler
    "configure_default_scheduler",
    "cron_schedule_func",
    "cron_set_match_second",
    "cron_set_match_second_e",
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
    "cron_launching_count",
    "new_config",
    "new_cron_error",
    "new_scheduler",
    "new_cron_task",
    "new_task_table",
    "default_scheduler",
    "wrap_cron_error",
    # Option types (Go compat)
    "SchedulerOption",
    "DefaultSchedulerOption",
    "ConfigOption",
    "PatternOption",
]


def new_pattern(expr: str) -> Pattern:
    return cronx.new_pattern(expr)


def must_new_pattern(expr: str) -> Pattern:
    return cronx.must_new_pattern(expr)


def match(expr: str, moment: datetime, match_second: bool = False) -> bool:
    return cronx.match(expr, moment, match_second)


def next_time(expr: str, after: datetime, match_second: bool = False) -> datetime | None:
    return cronx.next_time(expr, after, match_second)


cron_launching_count = cronx.cron_launching_count
new_config = cronx.new_config
new_scheduler = cronx.new_scheduler
new_cron_task = cronx.new_cron_task
new_task_table = cronx.new_task_table
default_scheduler = cronx.default_scheduler
cron_set_match_second = cronx.cron_set_match_second
cron_set_match_second_e = cronx.cron_set_match_second_e
cron_schedule_func = cronx.cron_schedule_func
new_cron_error = cronx.new_cron_error
wrap_cron_error = cronx.wrap_cron_error
CronError = cronx.CronError
ERR_SCHEDULER_STARTED = cronx.ERR_SCHEDULER_STARTED
Config = cronx.Config
AlwaysTrueMatcher = cronx.AlwaysTrueMatcher
PartMatcher = cronx.PartMatcher
PartSecond = cronx.PartSecond
PartMinute = cronx.PartMinute
PartHour = cronx.PartHour
PartDayOfMonth = cronx.PartDayOfMonth
PartMonth = cronx.PartMonth
PartDayOfWeek = cronx.PartDayOfWeek
PartYear = cronx.PartYear
TaskExecutor = cronx.TaskExecutor