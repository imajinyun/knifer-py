from __future__ import annotations

from datetime import datetime

import pytest

from kniferpy import vcron
from kniferpy.internal import cronx
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


def test_part_constants_and_check_value() -> None:
    assert vcron.PartSecond is vcron.Part.SECOND
    assert vcron.PartMinute is vcron.Part.MINUTE
    assert vcron.PartHour is vcron.Part.HOUR
    assert vcron.PartDayOfMonth is vcron.Part.DAY_OF_MONTH
    assert vcron.PartMonth is vcron.Part.MONTH
    assert vcron.PartDayOfWeek is vcron.Part.DAY_OF_WEEK
    assert vcron.PartYear is vcron.Part.YEAR
    vcron.Part.MINUTE.check_value(59)
    with pytest.raises(ValidationError) as exc_info:
        vcron.Part.MINUTE.check_value(60)
    assert exc_info.value.code == "knifer.cron.out_of_range"


def test_internal_parse_helpers_and_errors() -> None:
    assert cronx._is_leap_year(2024)
    assert not cronx._is_leap_year(2100)
    assert cronx._last_day_of_month(2, True) == 29
    assert cronx._last_day_of_month(2, False) == 28
    assert cronx._last_day_of_month(4, False) == 30
    assert cronx._last_day_of_month(13, False) == 31
    assert cronx._enumerate(1, 5, 2) == [1, 3, 5]
    assert cronx._enumerate(5, 1, 2) == []
    assert cronx._enumerate(1, 3, 0) == [1, 2, 3]
    assert cronx._parse_int("+7") == 7
    with pytest.raises(ValueError):
        cronx._parse_int(" 7")
    with pytest.raises(ValueError):
        cronx._parse_int("1.2")
    with pytest.raises(ValidationError):
        cronx._parse_single(vcron.Part.MINUTE, "")
    with pytest.raises(ValidationError):
        cronx._parse_range_step(vcron.Part.MINUTE, "*/bad")
    with pytest.raises(ValidationError):
        cronx._parse_part_values(vcron.Part.MINUTE, "1,,2")


def test_negative_values_question_wildcard_and_matcher_edges() -> None:
    assert cronx._parse_single(vcron.Part.DAY_OF_WEEK, "7") == 0
    assert cronx._parse_single(vcron.Part.MINUTE, "-1") == 58
    assert cronx._parse_range(vcron.Part.HOUR, "?", 20) == [0, 20]
    assert cronx._parse_range(vcron.Part.HOUR, "22-2", 1) == [22, 23, 0, 1, 2]
    assert cronx.AlwaysTrueMatcher.match(999)
    assert cronx.AlwaysTrueMatcher.next_after(5) == 5
    matcher = cronx._new_matcher(vcron.Part.MINUTE, "1,2")
    assert matcher.matches(1)
    assert not matcher.matches(3)
    with pytest.raises(ValidationError):
        cronx._new_matcher(vcron.Part.MINUTE, "")


def test_pattern_construction_variants_and_next_time_none() -> None:
    six = vcron.new_pattern("0 0 12 * * *")
    seven = vcron.new_pattern("0 0 12 1 jan mon 2024")
    assert six.match(_dt(2024, 1, 1, 12, 0, 0), match_second=True)
    assert seven.raw == "0 0 12 1 jan mon 2024"
    assert vcron.must_new_pattern("0 0 * * *").raw == "0 0 * * *"
    assert vcron.must_new_pattern_with_options("0 0 * * *").raw == "0 0 * * *"
    assert vcron.new_pattern_with_options("0 0 * * *").raw == "0 0 * * *"
    assert vcron.next_time("0 0 0 1 1 * 2099", _dt(2099, 1, 2)) is None


class _Task:
    def __init__(self, events: list[str], label: str = "task", fail: bool = False) -> None:
        self.events = events
        self.label = label
        self.fail = fail

    def execute(self) -> None:
        self.events.append(self.label)
        if self.fail:
            raise RuntimeError("boom")


class _Listener:
    def __init__(self, events: list[str], fail: bool = False) -> None:
        self.events = events
        self.fail = fail

    def on_start(self, executor: vcron.TaskExecutor) -> None:
        self.events.append(f"start:{executor.cron_task.id}")
        if self.fail:
            raise RuntimeError("listener start")

    def on_succeeded(self, executor: vcron.TaskExecutor) -> None:
        self.events.append(f"ok:{executor.cron_task.id}")
        if self.fail:
            raise RuntimeError("listener ok")

    def on_failed(self, executor: vcron.TaskExecutor, error: BaseException) -> None:
        self.events.append(f"fail:{executor.cron_task.id}:{error}")
        if self.fail:
            raise RuntimeError("listener fail")


def test_task_func_cron_task_listener_and_task_table() -> None:
    events: list[str] = []
    task = vcron.TaskFunc(lambda: events.append("func"))
    pattern = vcron.new_pattern("0 0 * * *")
    cron_task = vcron.new_cron_task("id1", "0 0 * * *", task)
    executor = vcron.TaskExecutor(cron_task=cron_task)
    table = vcron.new_task_table()
    listener = vcron.SimpleTaskListener()

    assert executor.task() is task
    task.execute()
    cron_task.execute()
    cron_task.set_pattern(vcron.new_pattern("0 1 * * *"))
    assert cron_task.pattern.raw == "0 1 * * *"
    listener.on_start(executor)
    listener.on_succeeded(executor)
    listener.on_failed(executor, RuntimeError("x"))
    table.add("id1", pattern, task)
    assert table.get("id1") is not None
    assert table.get_pattern("id1") is pattern
    assert table.get_task("id1") is task
    assert table.ids() == ["id1"]
    assert table.size() == 1
    assert not table.is_empty()
    assert table.items()[0].id == "id1"
    assert table.update_pattern("id1", vcron.new_pattern("0 2 * * *"))
    assert table.get_pattern("id1").raw == "0 2 * * *"
    assert not table.update_pattern("missing", pattern)
    assert table.remove("id1")
    assert not table.remove("id1")
    assert table.is_empty()
    with pytest.raises(ValidationError):
        table.add("dup", pattern, task)
        table.add("dup", pattern, task)
    assert events == ["func", "func"]


def test_scheduler_management_and_synchronous_execution() -> None:
    events: list[str] = []
    scheduler = vcron.new_scheduler(match_second=True)
    listener = _Listener(events)
    noisy_listener = _Listener(events, fail=True)
    scheduler.set_executor(lambda fn: fn())
    scheduler.set_runner(lambda fn: fn())
    assert scheduler.config().match_second is True
    assert scheduler.set_match_second(False) is scheduler
    assert not scheduler.is_match_second()
    scheduler.set_match_second_e(True)
    assert scheduler.set_time_zone("UTC") is scheduler
    scheduler.set_time_zone_e("UTC")
    assert scheduler.config().location == "UTC"
    assert scheduler.add_listener(listener) is scheduler
    scheduler.add_listener(noisy_listener)
    scheduler.remove_listener(noisy_listener)

    scheduler.schedule_with_id("ok", "* * * * *", _Task(events, "ok-task"))
    scheduler.schedule_pattern(
        "fail", vcron.new_pattern("* * * * *"), _Task(events, "fail-task", True)
    )
    auto_id = scheduler.schedule_func("* * * * *", lambda: events.append("auto"))
    assert scheduler.get_task("ok") is not None
    assert scheduler.get_pattern("ok") is not None
    assert scheduler.size() == 3
    assert not scheduler.is_empty()
    assert scheduler.update_pattern("ok", "0 * * * *")
    assert not scheduler.update_pattern("missing", "* * * * *")
    scheduler._execute_task(scheduler._table.get("ok"))
    scheduler._execute_task(scheduler._table.get("fail"))
    assert scheduler.running_count() == 0
    assert scheduler.launching_count() == 0
    assert "ok-task" in events
    assert any(event.startswith("fail:fail:") for event in events)
    assert scheduler.deschedule(auto_id)
    scheduler.clear()
    assert scheduler.is_empty()


def test_scheduler_lifecycle_and_started_errors() -> None:
    scheduler = vcron.new_scheduler()
    scheduler.set_executor(lambda fn: fn())
    scheduler.start()
    assert scheduler.is_started()
    scheduler.start()
    with pytest.raises(RuntimeError):
        scheduler.set_match_second_e(True)
    with pytest.raises(RuntimeError):
        scheduler.set_time_zone_e("UTC")
    scheduler.stop(clear_tasks=False)
    scheduler.wait()
    scheduler.shutdown(clear_tasks=False)
    scheduler.restart()
    assert scheduler.is_started()
    scheduler.shutdown(clear_tasks=False)


def test_default_scheduler_functions_and_errors() -> None:
    scheduler = vcron.configure_default_scheduler(match_second=True)
    scheduler.set_executor(lambda fn: fn())
    assert vcron.default_scheduler() is scheduler
    assert vcron.default_scheduler_with_options() is scheduler
    assert vcron.new_config() == vcron.Config()
    assert vcron.new_config_with_options() == vcron.Config()
    vcron.cron_set_match_second(False)
    vcron.cron_set_match_second_with_options(True)
    vcron.set_match_second(False)
    vcron.cron_set_match_second_e(False)
    vcron.cron_set_match_second_e_with_options(True)
    task_id = vcron.schedule_func("* * * * *", lambda: None)
    task_id_2 = vcron.cron_schedule_func("* * * * *", lambda: None)
    task_id_3 = vcron.cron_schedule_func_with_options("* * * * *", lambda: None)
    vcron.schedule_with_id("fixed", "* * * * *", _Task([]))
    vcron.cron_schedule_with_id_with_options("fixed2", "* * * * *", _Task([]))
    assert vcron.update_pattern("fixed", "0 * * * *")
    assert vcron.cron_update_pattern_with_options("fixed2", "0 * * * *")
    assert vcron.remove(task_id)
    assert vcron.cron_remove_with_options(task_id_2)
    assert vcron.remove(task_id_3)
    assert vcron.running_count() == 0
    assert vcron.cron_launching_count() == 0
    vcron.start()
    with pytest.raises(RuntimeError):
        vcron.cron_set_match_second_e(False)
    vcron.stop()
    vcron.restart()
    vcron.shutdown(clear_tasks=False)
    vcron.cron_start_with_options()
    vcron.cron_stop_with_options()
    vcron.cron_restart_with_options()
    vcron.cron_shutdown_with_options(clear_tasks=False)
    err = vcron.new_cron_error("bad %s", "cron")
    wrapped = vcron.wrap_cron_error(RuntimeError("root"), "wrap %s", "cron")
    assert str(err) == "bad cron"
    assert "root" in str(wrapped)
