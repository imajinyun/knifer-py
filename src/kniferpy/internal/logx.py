from __future__ import annotations

import sys
from datetime import datetime
from enum import IntEnum
from typing import Callable, Protocol, TextIO

# Default timestamp format, the strftime analog of knifer-go's
# "2006-01-02 15:04:05" layout.
CONSOLE_LOG_TIME_LAYOUT = "%Y-%m-%d %H:%M:%S"

# The static/default logger name, matching knifer-go's fixed "static" name.
STATIC_LOG_NAME = "static"


class Level(IntEnum):
    """Log severity ordered from most to least detailed.

    ``ALL < TRACE < DEBUG < INFO < WARN < ERROR < FATAL < OFF``. A logger emits
    a record when its threshold level is less than or equal to the record's
    level, so ``ALL`` lets everything through and ``OFF`` filters everything.
    """

    ALL = 0
    TRACE = 1
    DEBUG = 2
    INFO = 3
    WARN = 4
    ERROR = 5
    FATAL = 6
    OFF = 7

    def __str__(self) -> str:
        return self.name


# LogLevel alias for Go compat
LogLevel = Level

# LogLevel constants for Go compat
LogLevelAll = Level.ALL
LogLevelTrace = Level.TRACE
LogLevelDebug = Level.DEBUG
LogLevelInfo = Level.INFO
LogLevelWarn = Level.WARN
LogLevelError = Level.ERROR
LogLevelFatal = Level.FATAL
LogLevelOff = Level.OFF


# Injectable color factory: maps Level to ANSI escape code
ColorFactory = Callable[[Level], str]


class Log(Protocol):
    """Protocol matching the knifer-go Log interface."""

    def get_name(self) -> str: ...
    def is_enabled(self, level: Level) -> bool: ...
    def is_trace_enabled(self) -> bool: ...
    def is_debug_enabled(self) -> bool: ...
    def is_info_enabled(self) -> bool: ...
    def is_warn_enabled(self) -> bool: ...
    def is_error_enabled(self) -> bool: ...
    def trace(self, *args: object) -> None: ...
    def tracef(self, template: str, *args: object) -> None: ...
    def debug(self, *args: object) -> None: ...
    def debugf(self, template: str, *args: object) -> None: ...
    def info(self, *args: object) -> None: ...
    def infof(self, template: str, *args: object) -> None: ...
    def warn(self, *args: object) -> None: ...
    def warnf(self, template: str, *args: object) -> None: ...
    def error(self, *args: object) -> None: ...
    def errorf(self, template: str, *args: object) -> None: ...
    def log(self, level: Level, template: str, *args: object) -> None: ...
    def log_e(
        self, level: Level, err: BaseException | None, template: str, *args: object
    ) -> None: ...


class LogFactory(Protocol):
    """Protocol for log factory injection (Go LogFactory equivalent)."""

    def create_log(self, name: str) -> Log: ...


# Injectable color factory for customizing per-level colors
_color_factory: ColorFactory | None = None


def set_color_factory(factory: ColorFactory | None) -> None:
    """Set an injectable color factory for the static logger."""
    global _color_factory
    _color_factory = factory


def get_color_factory() -> ColorFactory | None:
    """Return the current color factory."""
    return _color_factory


#         set_log_color_factory = set_color_factory
#         set_log_level = set_console_level
#         get_log_level = get_console_level


def _format_arg(value: object) -> str:
    """Render a single log argument using Python's ``str``."""
    return str(value)


def _replace_placeholders(template: str, args: tuple[object, ...]) -> str:
    """Replace ``{}`` placeholders positionally, leaving extras literal."""
    out: list[str] = []
    idx = 0
    i = 0
    n = len(template)
    while i < n:
        if i + 1 < n and template[i] == "{" and template[i + 1] == "}":
            if idx < len(args):
                out.append(_format_arg(args[idx]))
                idx += 1
            else:
                out.append("{}")
            i += 2
            continue
        out.append(template[i])
        i += 1
    return "".join(out)


def render_message(template: str, *args: object) -> str:
    """Render a log message from a template and arguments.

    An empty template concatenates the arguments space-separated. A template
    containing ``{}`` fills those placeholders positionally. Otherwise the
    template is treated as a ``%``-style format string; malformed formats fail
    safe by appending the arguments instead of raising.
    """
    if template == "":
        return " ".join(_format_arg(a) for a in args)
    if "{}" in template:
        return _replace_placeholders(template, args)
    if not args:
        return template
    try:
        return template % args
    except (TypeError, ValueError):
        return template + " " + " ".join(_format_arg(a) for a in args)


# Global console threshold shared by loggers without an instance-level override.
_console_level: Level = Level.DEBUG


def set_console_level(level: Level) -> None:
    """Set the global console threshold; records below it are dropped."""
    global _console_level
    _console_level = level


def get_console_level() -> Level:
    """Return the global console threshold."""
    return _console_level


class ConsoleLog:
    """Leveled logger that writes to stdout, with warnings and errors on stderr.

    The default threshold is the global console level (``DEBUG``). Output format
    is ``[date] [level] name: msg``. A clock and writers may be injected for
    deterministic tests; an instance level overrides the global threshold.
    """

    __slots__ = ("name", "_level", "_clock", "_out", "_err_out", "_time_layout")

    def __init__(
        self,
        name: str,
        *,
        level: Level | None = None,
        clock: Callable[[], datetime] | None = None,
        out: TextIO | None = None,
        err_out: TextIO | None = None,
        time_layout: str = "",
    ) -> None:
        self.name = name
        self._level = level
        self._clock = clock
        self._out = out
        self._err_out = err_out
        self._time_layout = time_layout or CONSOLE_LOG_TIME_LAYOUT

    # --- Configuration ------------------------------------------------------

    def get_name(self) -> str:
        """Return the logger name."""
        return self.name

    def set_output(self, out: TextIO | None, err_out: TextIO | None) -> None:
        """Redirect stdout/stderr targets, mainly for tests."""
        self._out = out
        self._err_out = err_out

    def _now(self) -> datetime:
        return self._clock() if self._clock is not None else datetime.now()

    def _target_writer(self, level: Level) -> TextIO:
        if level >= Level.WARN:
            return self._err_out if self._err_out is not None else sys.stderr
        return self._out if self._out is not None else sys.stdout

    # --- Enablement ---------------------------------------------------------

    def is_enabled(self, level: Level) -> bool:
        """Report whether ``level`` passes this logger's threshold."""
        threshold = self._level if self._level is not None else get_console_level()
        return threshold <= level

    def is_trace_enabled(self) -> bool:
        return self.is_enabled(Level.TRACE)

    def is_debug_enabled(self) -> bool:
        return self.is_enabled(Level.DEBUG)

    def is_info_enabled(self) -> bool:
        return self.is_enabled(Level.INFO)

    def is_warn_enabled(self) -> bool:
        return self.is_enabled(Level.WARN)

    def is_error_enabled(self) -> bool:
        return self.is_enabled(Level.ERROR)

    # --- Emission -----------------------------------------------------------

    def _write(self, level: Level, err: BaseException | None, template: str, *args: object) -> None:
        msg = render_message(template, *args)
        line = f"[{self._now().strftime(self._time_layout)}] [{level.name:<5}] {self.name}: {msg}"
        if err is not None:
            line += f" | error: {err}"
        print(line, file=self._target_writer(level))

    def log_e(self, level: Level, err: BaseException | None, template: str, *args: object) -> None:
        """Emit at ``level`` with an attached error when the level is enabled."""
        if not self.is_enabled(level):
            return
        self._write(level, err, template, *args)

    def log(self, level: Level, template: str, *args: object) -> None:
        """Emit at ``level`` when the level is enabled."""
        self.log_e(level, None, template, *args)

    def trace(self, *args: object) -> None:
        self.log(Level.TRACE, "", *args)

    def tracef(self, template: str, *args: object) -> None:
        self.log(Level.TRACE, template, *args)

    def debug(self, *args: object) -> None:
        self.log(Level.DEBUG, "", *args)

    def debugf(self, template: str, *args: object) -> None:
        self.log(Level.DEBUG, template, *args)

    def info(self, *args: object) -> None:
        self.log(Level.INFO, "", *args)

    def infof(self, template: str, *args: object) -> None:
        self.log(Level.INFO, template, *args)

    def warn(self, *args: object) -> None:
        self.log(Level.WARN, "", *args)

    def warnf(self, template: str, *args: object) -> None:
        self.log(Level.WARN, template, *args)

    def error(self, *args: object) -> None:
        self.log(Level.ERROR, "", *args)

    def errorf(self, template: str, *args: object) -> None:
        self.log(Level.ERROR, template, *args)

    def fatal(self, *args: object) -> None:
        self.log(Level.FATAL, "", *args)

    def fatalf(self, template: str, *args: object) -> None:
        self.log(Level.FATAL, template, *args)


# ANSI color codes used by ConsoleColorLog.
_ANSI_RESET = "\033[0m"
_ANSI_DEFAULT = "\033[39m"
_ANSI_RED = "\033[31m"
_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_MAGENTA = "\033[35m"
_ANSI_CYAN = "\033[36m"
_ANSI_WHITE = "\033[37m"

_LEVEL_COLORS = {
    Level.TRACE: _ANSI_MAGENTA,
    Level.DEBUG: _ANSI_GREEN,
    Level.INFO: _ANSI_GREEN,
    Level.WARN: _ANSI_YELLOW,
    Level.ERROR: _ANSI_RED,
    Level.FATAL: _ANSI_RED,
}


class ConsoleColorLog(ConsoleLog):
    """Console logger that wraps each field in ANSI colors.

    The color map is fixed (magenta trace, green debug/info, yellow warn, red
    error/fatal); knifer-go's injectable ``ColorFactory`` is intentionally
    omitted to keep the facade small.
    """

    __slots__ = ()

    def _write(self, level: Level, err: BaseException | None, template: str, *args: object) -> None:
        msg = render_message(template, *args)
        color = _LEVEL_COLORS.get(level, _ANSI_DEFAULT)
        line = (
            f"{_ANSI_WHITE}[{self._now().strftime(self._time_layout)}]{_ANSI_RESET} "
            f"{color}[{level.name:<5}]{_ANSI_RESET} "
            f"{_ANSI_CYAN}{self.name}{_ANSI_RESET}: {msg}"
        )
        if err is not None:
            line += f" | error: {err}"
        print(line, file=self._target_writer(level))


def new_console_log(
    name: str,
    *,
    level: Level | None = None,
    clock: Callable[[], datetime] | None = None,
    out: TextIO | None = None,
    err_out: TextIO | None = None,
    time_layout: str = "",
) -> ConsoleLog:
    """Create a :class:`ConsoleLog`."""
    return ConsoleLog(
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
    """Create a :class:`ConsoleColorLog`."""
    return ConsoleColorLog(
        name,
        level=level,
        clock=clock,
        out=out,
        err_out=err_out,
        time_layout=time_layout,
    )


# The shared static logger backing the module-level convenience functions.
_static_logger = ConsoleLog(STATIC_LOG_NAME)


def trace(*args: object) -> None:
    """Log trace-level output through the static logger."""
    _static_logger.trace(*args)


def tracef(template: str, *args: object) -> None:
    """Log formatted trace-level output through the static logger."""
    _static_logger.tracef(template, *args)


def debug(*args: object) -> None:
    """Log debug-level output through the static logger."""
    _static_logger.debug(*args)


def debugf(template: str, *args: object) -> None:
    """Log formatted debug-level output through the static logger."""
    _static_logger.debugf(template, *args)


def info(*args: object) -> None:
    """Log info-level output through the static logger."""
    _static_logger.info(*args)


def infof(template: str, *args: object) -> None:
    """Log formatted info-level output through the static logger."""
    _static_logger.infof(template, *args)


def warn(*args: object) -> None:
    """Log warn-level output through the static logger."""
    _static_logger.warn(*args)


def warnf(template: str, *args: object) -> None:
    """Log formatted warn-level output through the static logger."""
    _static_logger.warnf(template, *args)


def error(*args: object) -> None:
    """Log error-level output through the static logger."""
    _static_logger.error(*args)


def errorf(template: str, *args: object) -> None:
    """Log formatted error-level output through the static logger."""
    _static_logger.errorf(template, *args)


def log_at(level: Level, template: str, *args: object) -> None:
    """Log at ``level`` through the static logger."""
    _static_logger.log(level, template, *args)


def log_at_e(level: Level, err: BaseException | None, template: str, *args: object) -> None:
    """Log at ``level`` with an attached error through the static logger."""
    _static_logger.log_e(level, err, template, *args)


def fatal(*args: object) -> None:
    """Log fatal-level output through the static logger."""
    _static_logger.fatal(*args)


def fatalf(template: str, *args: object) -> None:
    """Log formatted fatal-level output through the static logger."""
    _static_logger.fatalf(template, *args)


# Logger factory / named loggers
_LogFactory = Callable[[str], "ConsoleLog"]
_log_factory: _LogFactory | None = None
_logger_cache: dict[str, ConsoleLog] = {}


def set_log_factory(factory: _LogFactory | None) -> None:
    global _log_factory
    _log_factory = factory


def get_factory() -> _LogFactory | None:
    return _log_factory


def logger(name: str) -> ConsoleLog:
    if name in _logger_cache:
        return _logger_cache[name]
    lg = _log_factory(name) if _log_factory is not None else ConsoleLog(name)
    _logger_cache[name] = lg
    return lg


def default_logger() -> ConsoleLog:
    return _static_logger


def new_isolated_logger(name: str) -> ConsoleLog:
    return ConsoleLog(name)


# Aliases for Go compat
set_log_color_factory = set_color_factory
set_log_level = set_console_level
get_log_level = get_console_level
