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
import threading
import traceback
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

_logger = logging.getLogger("kniferpy.errx")

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


def _default_log_func(level: str, message: str, stack: str) -> None:
    log_level = getattr(logging, level.upper(), logging.ERROR)
    _logger.log(log_level, "%s\n%s", message, stack)


class Wrapper:
    """Executes a function with panic recovery and optional logging."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        self._fn = fn
        self._log_func: LogFunc = _default_log_func
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
        self._log_func: LogFunc = _default_log_func
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


def error_is(err: BaseException, target: type[BaseException]) -> bool:
    """Check if err is or contains an instance of target."""
    if isinstance(err, target):
        return True
    if isinstance(err, PanicError):
        return isinstance(err.cause, target) if err.cause else False
    return False