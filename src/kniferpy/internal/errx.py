"""Error handling with stack traces, Sentry integration, and recovery.

Ports knifer-go's internal/errx with Python-idiomatic mappings:

- Go PanicError -> Python PanicError (wraps recovered exceptions)
- Go Collector -> Python Collector (aggregates background errors)
- Go Wrapper -> Python Wrapper (recovery wrapper with logging)
- Go stack traces -> Python traceback
- Go Sentry/logrus -> Python sentry_sdk / logging
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Protocol, runtime_checkable

_logger = logging.getLogger("kniferpy.errx")

# Sentry DSN environment variable key (Go compat)
SENTRY_DSN = "SENTRY_DSN"
SentryDSN = SENTRY_DSN

# ---------------------------------------------------------------------------
# Error codes (mirrors knifer-go ErrCode constants)
# ---------------------------------------------------------------------------

ERR_CODE_INVALID_INPUT = "knifer.invalid_input"
ERR_CODE_NOT_FOUND = "knifer.not_found"
ERR_CODE_UNSUPPORTED = "knifer.unsupported"
ERR_CODE_UNSAFE_RESOURCE = "knifer.unsafe_resource"
ERR_CODE_TIMEOUT = "knifer.timeout"
ERR_CODE_PROVIDER_FAILURE = "knifer.provider_failure"
ERR_CODE_INTERNAL = "knifer.internal"

_ERR_CODE_NAMES: dict[str, str] = {
    ERR_CODE_INVALID_INPUT: "ERR_CODE_INVALID_INPUT",
    ERR_CODE_NOT_FOUND: "ERR_CODE_NOT_FOUND",
    ERR_CODE_UNSUPPORTED: "ERR_CODE_UNSUPPORTED",
    ERR_CODE_UNSAFE_RESOURCE: "ERR_CODE_UNSAFE_RESOURCE",
    ERR_CODE_TIMEOUT: "ERR_CODE_TIMEOUT",
    ERR_CODE_PROVIDER_FAILURE: "ERR_CODE_PROVIDER_FAILURE",
    ERR_CODE_INTERNAL: "ERR_CODE_INTERNAL",
}


def err_code_name(code: str) -> str:
    return _ERR_CODE_NAMES.get(code, code)


# Default log function (can be overridden globally)
_default_log_func: LogFunc | None = None


def _get_default_log_func() -> LogFunc:
    if _default_log_func is not None:
        return _default_log_func
    return _builtin_log_func


def configure_default_log_func(log_func: LogFunc) -> None:
    """Replace the global default log function used by all errx helpers."""
    global _default_log_func
    _default_log_func = log_func


def reset_default_log_func() -> None:
    """Reset the global default log function to the built-in."""
    global _default_log_func
    _default_log_func = None


# ── Go-compat EmptyFormatter ────────────────────────────────────────────────

EmptyFormatter = type("EmptyFormatter", (), {})  # Go: empty formatter sentinel


# ── Go-compat ResetStackFrameCache ──────────────────────────────────────────

def reset_stack_frame_cache() -> None:
    """Reset the stack frame cache (Go compat, no-op in Python)."""
    pass


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class KniferError(Exception):
    message: str
    code: str = "knifer.error"
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def error_code(self) -> str:
        return self.code


class ValidationError(KniferError):
    pass


class SecurityError(KniferError):
    pass


class DecodeError(KniferError):
    pass


class CryptoError(KniferError):
    pass


class JSONError(KniferError):
    pass


# ---------------------------------------------------------------------------
# Error construction helpers (mirrors knifer-go errors.go)
# ---------------------------------------------------------------------------


def new_error(code: str, message: str, **context: Any) -> KniferError:
    """Create a new KniferError with the given code and message."""
    return KniferError(message=message, code=code, context=dict(context))


def wrap_error(code: str, message: str, cause: BaseException, **context: Any) -> KniferError:
    """Create a KniferError wrapping an existing cause."""
    err = KniferError(message=message, code=code, context=dict(context))
    err.__cause__ = cause
    return err


def errorf(code: str, message: str, *args: Any, **context: Any) -> KniferError:
    """Create a KniferError with a formatted message."""
    formatted = message % args if args else message
    return KniferError(message=formatted, code=code, context=dict(context))


def code_of(err: BaseException) -> tuple[str, bool]:
    """Extract the error code from an error, if it carries one."""
    while err is not None:
        if hasattr(err, "error_code") and callable(err.error_code):
            return err.error_code(), True
        err = err.__cause__
    return "", False


# ---------------------------------------------------------------------------
# Stack trace support
# ---------------------------------------------------------------------------


class PanicError(KniferError):
    """Wraps a recovered exception with a stack trace."""

    def __init__(
        self,
        value: Any,
        cause: BaseException | None = None,
        *,
        stack_trace: str = "",
    ) -> None:
        super().__init__(
            message=f"panic: {value}",
            code="knifer.panic",
            context={"value": repr(value)},
        )
        self.value = value
        self.cause = cause
        if stack_trace:
            self.stack_trace = stack_trace
        elif isinstance(value, BaseException):
            self.stack_trace = "".join(
                traceback.format_exception(type(value), value, value.__traceback__)
            )
        elif cause is not None and isinstance(cause, BaseException):
            self.stack_trace = "".join(
                traceback.format_exception(type(cause), cause, cause.__traceback__)
            )
        else:
            self.stack_trace = "".join(traceback.format_stack())

    def __str__(self) -> str:
        return f"{self.message}\n{self.stack_trace}"

    def error_code(self) -> str:
        return self.code

    def unwrap(self) -> BaseException | None:
        return self.cause


def get_stack(skip: int = 2) -> str:
    """Capture the current call stack as a string."""
    return "".join(traceback.format_stack(limit=10)[:-skip] if skip else traceback.format_stack(limit=10))


def get_stack_trace(skip: int = 2, depth: int = 50) -> list[str]:
    """Capture the current call stack as a list of frame strings."""
    return traceback.format_stack(limit=depth)[:-skip] if skip else traceback.format_stack(limit=depth)


def format_stack_frame(frame_summary: traceback.FrameSummary) -> str:
    """Format a single frame summary as a string."""
    return f'  File "{frame_summary.filename}", line {frame_summary.lineno}, in {frame_summary.name}\n    {frame_summary.line or ""}\n'


# ---------------------------------------------------------------------------
# Recovery wrapper
# ---------------------------------------------------------------------------


LogFunc = Callable[[str, str, str], None]
"""Error log entry writer: (level, message, stack_trace) -> None."""


def _builtin_log_func(level: str, message: str, stack: str) -> None:
    log_level = getattr(logging, level.upper(), logging.ERROR)
    _logger.log(log_level, "%s\n%s", message, stack)


class Wrapper:
    """Executes a function with panic recovery and optional logging."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        self._fn = fn
        self._log_func: LogFunc = _get_default_log_func
        self._info_format: str = ""
        self._warn_format: str = ""
        self._error_format: str = ""

    def with_infof(self, fmt: str, *args: Any) -> Wrapper:
        self._info_format = fmt % args if args else fmt
        return self

    def with_warnf(self, fmt: str, *args: Any) -> Wrapper:
        self._warn_format = fmt % args if args else fmt
        return self

    def with_errorf(self, fmt: str, *args: Any) -> Wrapper:
        self._error_format = fmt % args if args else fmt
        return self

    def with_log_func(self, log_func: LogFunc) -> Wrapper:
        self._log_func = log_func
        return self

    def exec(self) -> Any:
        try:
            if self._info_format:
                _logger.info(self._info_format)
            result = self._fn()
            if self._warn_format and result is not None:
                _logger.warning(self._warn_format)
            return result
        except Exception as exc:
            stack = self._error_format or get_stack(3)
            self._log_func("error", str(exc), stack)
            raise


def recover(fn: Callable[[], Any], error_format: str = "", *args: Any) -> Any:
    """Execute fn, catching exceptions and logging them."""
    return Wrapper(fn).with_errorf(error_format, *args).exec()


def recover_without_error(fn: Callable[[], None], error_format: str = "", *args: Any) -> None:
    """Execute fn, catching exceptions silently."""
    try:
        fn()
    except Exception as exc:
        if error_format:
            _logger.error(error_format % args if args else error_format, exc_info=True)


# ---------------------------------------------------------------------------
# Collector — aggregates concurrent errors
# ---------------------------------------------------------------------------


class Collector:
    """Aggregates errors from concurrent goroutines (threads).

    Port of knifer-go's Collector: runs functions in background threads,
    recovers panics, logs failures, and aggregates errors.
    """

    def __init__(self) -> None:
        self._errors: list[BaseException] = []
        self._lock = threading.Lock()
        self._log_func: LogFunc = _get_default_log_func
        self._runner: Callable[[Callable[[], None]], None] | None = None

    def with_log_func(self, log_func: LogFunc) -> Collector:
        self._log_func = log_func
        return self

    def with_runner(self, runner: Callable[[Callable[[], None]], None]) -> Collector:
        self._runner = runner
        return self

    def collect(self, err: BaseException) -> None:
        with self._lock:
            self._errors.append(err)

    def error(self) -> BaseException | None:
        with self._lock:
            if not self._errors:
                return None
            if len(self._errors) == 1:
                return self._errors[0]
            msgs = "; ".join(str(e) for e in self._errors)
            return KniferError(message=msgs, code="knifer.collector.errors")

    def go_run(self, fn: Callable[[], Any], error_format: str = "", *args: Any) -> None:
        """Run fn in a background thread, collecting errors."""
        def _run() -> None:
            try:
                fn()
            except Exception as exc:
                stack = get_stack(3)
                msg = error_format % args if args else str(exc)
                self._log_func("error", msg, stack)
                self.collect(exc)

        if self._runner:
            self._runner(_run)
        else:
            t = threading.Thread(target=_run, daemon=True)
            t.start()

    def recover(self, fn: Callable[[], Any], error_format: str = "", *args: Any) -> Any:
        """Execute fn synchronously, collecting errors on failure."""
        try:
            return fn()
        except Exception as exc:
            stack = get_stack(3)
            msg = error_format % args if args else str(exc)
            self._log_func("error", msg, stack)
            self.collect(exc)
            return None

    def wait_until(self, duration: float) -> tuple[bool, BaseException | None]:
        """Wait for a duration, checking if errors occurred."""
        import time
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            err = self.error()
            if err is not None:
                return False, err
            time.sleep(0.1)
        err = self.error()
        return err is None, err

    def wait_until_with_options(
        self,
        duration: float,
        *,
        ctx: Any = None,
        timer_factory: TimerFactory | None = None,
    ) -> tuple[bool, BaseException | None]:
        """Wait for a duration with options, checking if errors occurred."""
        return self.wait_until(duration)

    def collect_error(self, fn: Callable[[], Any], error_format: str = "", *args: Any) -> BaseException | None:
        """Execute fn, collect errors, return the error."""
        try:
            fn()
            return None
        except Exception as exc:
            stack = get_stack(3)
            msg = error_format % args if args else str(exc)
            self._log_func("error", msg, stack)
            self.collect(exc)
            return exc


def new_collector() -> Collector:
    return Collector()


# ---------------------------------------------------------------------------
# Sentry integration (optional, requires sentry-sdk)
# ---------------------------------------------------------------------------


def init_sentry(dsn: str, **kwargs: Any) -> None:
    """Initialize Sentry with the given DSN."""
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=dsn, **kwargs)
    except ImportError:
        _logger.warning("sentry-sdk not installed; skipping Sentry initialization")


def capture_exception(error: BaseException | None = None) -> str | None:
    """Capture an exception to Sentry."""
    try:
        import sentry_sdk
        return sentry_sdk.capture_exception(error)
    except ImportError:
        return None


def error_is(err: BaseException, target: type[BaseException] | str) -> bool:
    """Check if err is or contains an instance of target, or matches a code."""
    if isinstance(target, str):
        code, found = code_of(err)
        return found and code == target
    if isinstance(err, target):
        return True
    if isinstance(err, PanicError):
        return isinstance(err.cause, target) if err.cause else False
    return False


# ---------------------------------------------------------------------------
# MustExit — log and exit on error (mirrors knifer-go MustExit)
# ---------------------------------------------------------------------------


def must_exit(err: BaseException | None) -> None:
    """Log the error and exit the process with code 1 if err is not None."""
    if err is None:
        return
    log_func = _get_default_log_func()
    log_func("error", str(err), get_stack(3))
    sys.exit(1)


def must_exit_with_code(err: BaseException | None, exit_code: int = 1) -> None:
    """Log the error and exit with ``exit_code`` if err is not None."""
    if err is None:
        return
    log_func = _get_default_log_func()
    log_func("error", str(err), get_stack(3))
    sys.exit(exit_code)


# ── StackTrace / Frame types (Go compat) ─────────────────────────────────────


@runtime_checkable
class WithStack(Protocol):
    """Protocol for errors that carry a stack trace string."""

    def stack(self) -> str: ...


@runtime_checkable
class WithStackTrace(Protocol):
    """Protocol for errors that carry a typed stack trace."""

    def stack_trace(self) -> list[str]: ...


# Timer / TimerFactory for Collector
Timer = Protocol


class TimerFactory:
    """Creates a timer for the Collector wait loop."""

    __slots__ = ("_duration",)

    def __init__(self, duration: float) -> None:
        self._duration = duration

    def create(self) -> Callable[[], bool]:
        deadline = time.monotonic() + self._duration
        def _done() -> bool:
            return time.monotonic() >= deadline
        return _done


# ── Collector advanced features ──────────────────────────────────────────────


def new_collector_with_options(
    *,
    log_func: LogFunc | None = None,
    runner: Callable[[Callable[[], None]], None] | None = None,
    timer_factory: TimerFactory | None = None,
) -> Collector:
    """Create a Collector with optional configuration."""
    c = Collector()
    if log_func is not None:
        c.with_log_func(log_func)
    if runner is not None:
        c.with_runner(runner)
    if timer_factory is not None:
        c._timer_factory = timer_factory
    return c


def get_stack_with_skip(skip: int = 2) -> str:
    """Capture the current call stack with a configurable skip."""
    return get_stack(skip)


def get_stack_trace_with_options(
    *,
    skip: int = 2,
    depth: int = 50,
) -> list[str]:
    """Capture the current call stack as a list of frame strings."""
    return get_stack_trace(skip=skip, depth=depth)


def must_exit_with_log(err: BaseException | None, log_func: LogFunc | None = None) -> None:
    """Log the error with a custom log function and exit with code 1."""
    if err is None:
        return
    lf = log_func or _get_default_log_func()
    lf("error", str(err), get_stack(3))
    sys.exit(1)


def must_exit_with_panic(err: BaseException | None) -> None:
    """Log the error and raise a PanicError instead of exiting."""
    if err is None:
        return
    log_func = _get_default_log_func()
    log_func("error", str(err), get_stack(3))
    raise PanicError(str(err), cause=err if isinstance(err, BaseException) else None)