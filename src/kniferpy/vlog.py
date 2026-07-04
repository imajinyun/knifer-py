"""Leveled console logging.

Emit leveled log records to the console with a simple ``[date] [level] name:
msg`` format. Records at or above the ``WARN`` level go to stderr; the rest go
to stdout. Both a per-name :class:`ConsoleLog` and module-level convenience
functions backed by a shared static logger are provided, along with an ANSI
:class:`ConsoleColorLog`.

Templates accept ``{}`` positional placeholders (``"user {}"``) or ``%``-style
format strings (``"user %s"``); an empty template concatenates the arguments.
Malformed ``%`` formats fail safe instead of raising.

The threshold ordering is ``ALL < TRACE < DEBUG < INFO < WARN < ERROR < FATAL <
OFF``; a logger emits when its threshold is at or below the record level.

Only the console loggers are ported. knifer-go's ``LogFactory`` injection,
named-logger cache, ``*WithOptions`` per-call configuration, functional
constructor options, and injectable ``ColorFactory`` are intentionally omitted;
pass keyword arguments to the constructors and use the standard library
``logging`` module when you need handlers, files, or structured output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, TextIO

from kniferpy.internal import logx
from kniferpy.internal.logx import ConsoleColorLog, ConsoleLog, Level

__all__ = [
    "ConsoleColorLog",
    "ConsoleLog",
    "Level",
    "debug",
    "debugf",
    "default_logger",
    "error",
    "errorf",
    "fatal",
    "fatalf",
    "get_factory",
    "get_level",
    "info",
    "infof",
    "log_at",
    "log_at_e",
    "logger",
    "new_console_color_log",
    "new_console_log",
    "new_isolated_logger",
    "render_message",
    "set_level",
    "set_log_factory",
    "trace",
    "tracef",
    "warn",
    "warnf",
]


def new_console_log(
    name: str,
    *,
    level: Level | None = None,
    clock: Callable[[], datetime] | None = None,
    out: TextIO | None = None,
    err_out: TextIO | None = None,
    time_layout: str = "",
) -> ConsoleLog:
    """Create a :class:`ConsoleLog` writing to stdout/stderr."""
    return logx.new_console_log(
        name,
        level=level,
        clock=clock,
        out=out,
        err_out=err_out,
        time_layout=time_layout,
    )


def new_console_color_log(
    name: str,
    *,
    level: Level | None = None,
    clock: Callable[[], datetime] | None = None,
    out: TextIO | None = None,
    err_out: TextIO | None = None,
    time_layout: str = "",
) -> ConsoleColorLog:
    """Create a :class:`ConsoleColorLog` writing ANSI-colored output."""
    return logx.new_console_color_log(
        name,
        level=level,
        clock=clock,
        out=out,
        err_out=err_out,
        time_layout=time_layout,
    )


def render_message(template: str, *args: object) -> str:
    """Render a log message from a template and arguments."""
    return logx.render_message(template, *args)


def set_level(level: Level) -> None:
    """Set the global console threshold; records below it are dropped."""
    logx.set_console_level(level)


def get_level() -> Level:
    """Return the global console threshold."""
    return logx.get_console_level()


def trace(*args: object) -> None:
    """Log trace-level output through the static logger."""
    logx.trace(*args)


def tracef(template: str, *args: object) -> None:
    """Log formatted trace-level output through the static logger."""
    logx.tracef(template, *args)


def debug(*args: object) -> None:
    """Log debug-level output through the static logger."""
    logx.debug(*args)


def debugf(template: str, *args: object) -> None:
    """Log formatted debug-level output through the static logger."""
    logx.debugf(template, *args)


def info(*args: object) -> None:
    """Log info-level output through the static logger."""
    logx.info(*args)


def infof(template: str, *args: object) -> None:
    """Log formatted info-level output through the static logger."""
    logx.infof(template, *args)


def warn(*args: object) -> None:
    """Log warn-level output through the static logger."""
    logx.warn(*args)


def warnf(template: str, *args: object) -> None:
    """Log formatted warn-level output through the static logger."""
    logx.warnf(template, *args)


def error(*args: object) -> None:
    """Log error-level output through the static logger."""
    logx.error(*args)


def errorf(template: str, *args: object) -> None:
    """Log formatted error-level output through the static logger."""
    logx.errorf(template, *args)


def log_at(level: Level, template: str, *args: object) -> None:
    """Log at ``level`` through the static logger."""
    logx.log_at(level, template, *args)


def log_at_e(level: Level, err: BaseException | None, template: str, *args: object) -> None:
    """Log at ``level`` with an attached error through the static logger."""
    logx.log_at_e(level, err, template, *args)


def fatal(*args: object) -> None:
    """Log fatal-level output through the static logger."""
    logx.fatal(*args)


def fatalf(template: str, *args: object) -> None:
    """Log formatted fatal-level output through the static logger."""
    logx.fatalf(template, *args)


def set_log_factory(factory) -> None:
    """Set the logger factory used by the static logger."""
    logx.set_log_factory(factory)


def get_factory():
    """Return the current logger factory."""
    return logx.get_factory()


def logger(name: str) -> ConsoleLog:
    """Return a named logger from the factory."""
    return logx.logger(name)


def default_logger() -> ConsoleLog:
    """Return the default logger."""
    return logx.default_logger()


def new_isolated_logger(name: str) -> ConsoleLog:
    """Create an isolated logger with a new factory."""
    return logx.new_isolated_logger(name)
