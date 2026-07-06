from __future__ import annotations

import io
from collections.abc import Iterator
from datetime import datetime

import pytest

from kniferpy import vlog
from kniferpy.internal import logx
from kniferpy.vlog import Level


@pytest.fixture(autouse=True)
def _reset_global_level() -> Iterator[None]:
    """Keep the shared global threshold isolated between tests."""
    saved = vlog.get_level()
    vlog.set_level(Level.DEBUG)
    yield
    vlog.set_level(saved)


def _fixed_clock() -> datetime:
    return datetime(2026, 7, 3, 9, 30, 0)


def _make_logger(
    name: str = "app",
    *,
    level: Level | None = None,
    time_layout: str = "",
) -> tuple[vlog.ConsoleLog, io.StringIO, io.StringIO]:
    out = io.StringIO()
    err = io.StringIO()
    logger = vlog.new_console_log(
        name, clock=_fixed_clock, out=out, err_out=err, level=level, time_layout=time_layout
    )
    return logger, out, err


# --- Level --------------------------------------------------------------------


def test_level_ordering() -> None:
    assert Level.ALL < Level.TRACE < Level.DEBUG < Level.INFO
    assert Level.INFO < Level.WARN < Level.ERROR < Level.FATAL < Level.OFF


def test_level_str() -> None:
    assert str(Level.DEBUG) == "DEBUG"
    assert str(Level.WARN) == "WARN"
    assert f"{Level.INFO}" == "INFO"


# --- render_message -----------------------------------------------------------


def test_render_empty_template_concats_args() -> None:
    assert vlog.render_message("", "a", 1, True) == "a 1 True"


def test_render_empty_template_no_args() -> None:
    assert vlog.render_message("") == ""


def test_render_brace_placeholders() -> None:
    assert vlog.render_message("hello {}", "world") == "hello world"
    assert vlog.render_message("{} + {} = {}", 1, 2, 3) == "1 + 2 = 3"


def test_render_brace_missing_args_left_literal() -> None:
    assert vlog.render_message("{} and {}", "only") == "only and {}"


def test_render_percent_format() -> None:
    assert vlog.render_message("a=%d", 1) == "a=1"
    assert vlog.render_message("%s=%.1f", "x", 2.5) == "x=2.5"


def test_render_template_without_args_returned_verbatim() -> None:
    assert vlog.render_message("no placeholders here") == "no placeholders here"


def test_render_malformed_percent_fails_safe() -> None:
    # A stray %d with a non-numeric arg would normally raise; we append instead.
    assert vlog.render_message("value=%d", "oops") == "value=%d oops"
    assert vlog.render_message("value=%", 1) == "value=% 1"


# --- ConsoleLog output format -------------------------------------------------


def test_console_format() -> None:
    logger, out, err = _make_logger("svc")
    logger.info("started")
    assert out.getvalue() == "[2026-07-03 09:30:00] [INFO ] svc: started\n"
    assert err.getvalue() == ""


def test_console_level_padding() -> None:
    logger, out, _ = _make_logger()
    logger.debug("x")
    assert "[DEBUG]" in out.getvalue()
    logger.info("y")
    # INFO is padded to five columns.
    assert "[INFO ]" in out.getvalue()


def test_console_brace_template() -> None:
    logger, out, _ = _make_logger("t")
    logger.infof("user {} id {}", "kim", 7)
    assert out.getvalue() == "[2026-07-03 09:30:00] [INFO ] t: user kim id 7\n"


def test_warn_and_error_go_to_stderr() -> None:
    logger, out, err = _make_logger()
    logger.warn("careful")
    logger.error("boom")
    assert out.getvalue() == ""
    assert "[WARN ]" in err.getvalue()
    assert "[ERROR]" in err.getvalue()


def test_info_and_debug_go_to_stdout() -> None:
    logger, out, err = _make_logger()
    logger.debug("d")
    logger.info("i")
    assert "[DEBUG]" in out.getvalue()
    assert "[INFO ]" in out.getvalue()
    assert err.getvalue() == ""


def test_log_e_appends_error() -> None:
    logger, _, err = _make_logger()
    logger.log_e(Level.ERROR, ValueError("bad input"), "failed")
    assert err.getvalue() == (
        "[2026-07-03 09:30:00] [ERROR] app: failed | error: bad input\n"
    )


def test_custom_time_layout() -> None:
    logger, out, _ = _make_logger(time_layout="%H:%M:%S")
    logger.info("hi")
    assert out.getvalue() == "[09:30:00] [INFO ] app: hi\n"


# --- Filtering ----------------------------------------------------------------


def test_instance_level_overrides_global() -> None:
    logger, out, _ = _make_logger(level=Level.WARN)
    logger.info("dropped")
    assert out.getvalue() == ""
    assert not logger.is_info_enabled()
    assert logger.is_warn_enabled()


def test_global_level_filters() -> None:
    vlog.set_level(Level.ERROR)
    logger, out, err = _make_logger()
    logger.info("nope")
    logger.warn("also nope")
    logger.error("yes")
    assert out.getvalue() == ""
    assert "[ERROR]" in err.getvalue()
    assert "[WARN ]" not in err.getvalue()


def test_off_level_disables_everything() -> None:
    logger, out, err = _make_logger(level=Level.OFF)
    logger.error("silent")
    assert out.getvalue() == ""
    assert err.getvalue() == ""


def test_all_level_enables_everything() -> None:
    logger, out, _ = _make_logger(level=Level.ALL)
    logger.trace("t")
    assert "[TRACE]" in out.getvalue()


def test_is_enabled_checks() -> None:
    logger, _, _ = _make_logger(level=Level.INFO)
    assert not logger.is_trace_enabled()
    assert not logger.is_debug_enabled()
    assert logger.is_info_enabled()
    assert logger.is_warn_enabled()
    assert logger.is_error_enabled()


def test_get_name_and_set_output() -> None:
    logger, _, _ = _make_logger("named")
    assert logger.get_name() == "named"
    new_out = io.StringIO()
    logger.set_output(new_out, None)
    logger.info("routed")
    assert "routed" in new_out.getvalue()


def test_default_writer_fallbacks(capsys: pytest.CaptureFixture[str]) -> None:
    logger = vlog.new_console_log("fallback", clock=_fixed_clock, level=Level.ALL)
    logger.info("out")
    logger.error("err")
    captured = capsys.readouterr()
    assert "fallback: out" in captured.out
    assert "fallback: err" in captured.err


# --- Convenience level methods ------------------------------------------------


def test_all_level_shortcuts() -> None:
    logger, out, err = _make_logger(level=Level.ALL)
    logger.trace("tr")
    logger.tracef("tr {}", 1)
    logger.debug("de")
    logger.debugf("de {}", 2)
    logger.info("in")
    logger.infof("in {}", 3)
    logger.warn("wa")
    logger.warnf("wa {}", 4)
    logger.error("er")
    logger.errorf("er {}", 5)
    logger.fatal("fa")
    logger.fatalf("fa {}", 6)
    stdout = out.getvalue()
    stderr = err.getvalue()
    assert "[TRACE] app: tr" in stdout
    assert "[TRACE] app: tr 1" in stdout
    assert "[DEBUG] app: de 2" in stdout
    assert "[INFO ] app: in 3" in stdout
    assert "[WARN ] app: wa 4" in stderr
    assert "[ERROR] app: er 5" in stderr
    assert "[FATAL] app: fa 6" in stderr


# --- ConsoleColorLog ----------------------------------------------------------


def test_color_log_wraps_ansi() -> None:
    out = io.StringIO()
    logger = vlog.new_console_color_log("c", clock=_fixed_clock, out=out, level=Level.ALL)
    logger.info("colored")
    text = out.getvalue()
    assert "\033[" in text
    assert "colored" in text
    assert "\033[0m" in text


def test_color_log_error_to_stderr() -> None:
    err = io.StringIO()
    logger = vlog.new_console_color_log("c", clock=_fixed_clock, err_out=err)
    logger.error("bad")
    assert "bad" in err.getvalue()
    logger.log_e(Level.ERROR, RuntimeError("x"), "boom")
    assert "boom | error: x" in err.getvalue()


def test_color_log_default_color_for_unmapped_level() -> None:
    out = io.StringIO()
    logger = vlog.new_console_color_log("c", clock=_fixed_clock, out=out, level=Level.ALL)
    logger.log(Level.ALL, "all")
    assert "\033[39m[ALL  ]" in out.getvalue()


def test_color_factory_accessors() -> None:
    try:
        factory = lambda level: f"color-{level.name}"
        vlog.set_color_factory(factory)
        assert logx.get_color_factory() is factory
        # The facade currently forwards without returning the internal value.
        assert vlog.get_color_factory() is None
    finally:
        vlog.set_color_factory(None)


# --- Static logger convenience functions --------------------------------------


def test_static_functions(capsys: pytest.CaptureFixture[str]) -> None:
    vlog.set_level(Level.ALL)
    vlog.trace("t")
    vlog.debug("d")
    vlog.info("i")
    vlog.warn("w")
    vlog.error("e")
    vlog.fatal("f")
    captured = capsys.readouterr()
    assert "static: t" in captured.out
    assert "static: d" in captured.out
    assert "static: i" in captured.out
    assert "static: w" in captured.err
    assert "static: e" in captured.err
    assert "static: f" in captured.err


def test_static_formatted_functions(capsys: pytest.CaptureFixture[str]) -> None:
    vlog.set_level(Level.ALL)
    vlog.tracef("t {}", 1)
    vlog.debugf("d {}", 2)
    vlog.infof("i {}", 3)
    vlog.warnf("w {}", 4)
    vlog.errorf("e {}", 5)
    vlog.fatalf("f {}", 6)
    captured = capsys.readouterr()
    assert "static: t 1" in captured.out
    assert "static: i 3" in captured.out
    assert "static: w 4" in captured.err
    assert "static: f 6" in captured.err


def test_static_log_at(capsys: pytest.CaptureFixture[str]) -> None:
    vlog.set_level(Level.ALL)
    vlog.log_at(Level.INFO, "at {}", "info")
    vlog.log_at_e(Level.ERROR, RuntimeError("x"), "boom")
    captured = capsys.readouterr()
    assert "[INFO ] static: at info" in captured.out
    assert "[ERROR] static: boom | error: x" in captured.err


def test_logger_factory_cache_and_isolated_logger() -> None:
    saved_factory = logx.get_factory()
    saved_cache = dict(logx._logger_cache)
    try:
        logx._logger_cache.clear()
        created: list[str] = []

        def factory(name: str) -> vlog.ConsoleLog:
            created.append(name)
            return vlog.new_console_log(name)

        vlog.set_log_factory(factory)
        assert vlog.get_factory() is factory
        first = vlog.logger("svc")
        second = vlog.logger("svc")
        assert first is second
        assert created == ["svc"]

        logx._logger_cache.clear()
        vlog.set_log_factory(None)
        fallback = vlog.logger("fallback")
        assert isinstance(fallback, vlog.ConsoleLog)
        assert fallback.get_name() == "fallback"

        isolated = vlog.new_isolated_logger("isolated")
        assert isolated.get_name() == "isolated"
        assert vlog.default_logger().get_name() == "static"
    finally:
        logx._logger_cache.clear()
        logx._logger_cache.update(saved_cache)
        vlog.set_log_factory(saved_factory)
