"""Error handling with structured errors, stack traces, and recovery.

Thin facade over kniferpy.internal.errx, porting knifer-go's verr surface.

Provides structured error types, panic recovery, stack trace capture,
a concurrent error Collector, and optional Sentry integration.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal.errx import (
    ERR_CODE_INTERNAL,
    ERR_CODE_INVALID_INPUT,
    ERR_CODE_NOT_FOUND,
    ERR_CODE_PROVIDER_FAILURE,
    ERR_CODE_TIMEOUT,
    ERR_CODE_UNSAFE_RESOURCE,
    ERR_CODE_UNSUPPORTED,
    SENTRY_DSN,
    Collector,
    CryptoError,
    DecodeError,
    JSONError,
    KniferError,
    LogFunc,
    PanicError,
    SecurityError,
    SentryDSN,
    TimerFactory,
    ValidationError,
    WithStack,
    WithStackTrace,
    Wrapper,
    capture_exception,
    code_of,
    configure_default_log_func,
    err_code_name,
    error_is,
    errorf,
    get_stack,
    get_stack_trace,
    get_stack_trace_with_options,
    get_stack_with_skip,
    init_sentry,
    must_exit,
    must_exit_with_code,
    must_exit_with_log,
    must_exit_with_panic,
    new_collector,
    new_collector_with_options,
    new_error,
    recover,
    recover_without_error,
    reset_default_log_func,
    wrap_error,
)

# ── Go-compat type aliases: functional option types ──────────────────────────

# Stack trace option types
StackTraceOption = Callable[[Any], None]
"""Functional option for customizing GetStackTraceWithOptions."""

StackOption = Callable[[Any], None]
"""Functional option for customizing fallback stack capture in GetStackWithOptions."""

# Callback types for stack trace customization
CallersFunc = Callable[[int, list[int]], int]
"""Callback for capturing call stack PCs (Go compat: runtime.Callers)."""

FuncForPCFunc = Callable[[int], tuple[str, int, str, bool]]
"""Callback for resolving a PC to file/line/function (Go compat: runtime.FuncForPC)."""

DebugStackFunc = Callable[[], bytes]
"""Callback for capturing a goroutine stack as fallback (Go compat: debug.Stack)."""

# Init / Sentry option types
InitOption = Callable[[Any], None]
"""Functional option for InitWithOptions and NewIsolatedLogrusWithOptions."""

# Exit option types
ExitOption = Callable[[Any], None]
"""Functional option for MustExitWithOptions."""

# Collector option types
CollectorOption = Callable[[Any], None]
"""Functional option for NewCollectorWithOptions."""

WaitOption = Callable[[Any], None]
"""Functional option for WaitUntilWithOptions."""

# Frame / StackTrace type aliases
Frame = str
"""A single stack frame (Go compat: uintptr -> string frame)."""

StackTrace = list[str]
"""A stack of frames from innermost to outermost (Go compat: []Frame)."""

__all__ = [
    # Error codes
    "ERR_CODE_INTERNAL",
    "ERR_CODE_INVALID_INPUT",
    "ERR_CODE_NOT_FOUND",
    "ERR_CODE_PROVIDER_FAILURE",
    "ERR_CODE_TIMEOUT",
    "ERR_CODE_UNSAFE_RESOURCE",
    "ERR_CODE_UNSUPPORTED",
    # Sentry
    "SENTRY_DSN",
    "SentryDSN",
    # Protocols
    "WithStack",
    "WithStackTrace",
    # Error types
    "KniferError",
    "ValidationError",
    "SecurityError",
    "DecodeError",
    "CryptoError",
    "JSONError",
    "PanicError",
    # Error construction
    "new_error",
    "wrap_error",
    "errorf",
    "code_of",
    "err_code_name",
    # Stack trace
    "get_stack",
    "get_stack_trace",
    "get_stack_with_skip",
    "get_stack_trace_with_options",
    # Recovery
    "Wrapper",
    "LogFunc",
    "recover",
    "recover_without_error",
    # Collector
    "Collector",
    "TimerFactory",
    "new_collector",
    "new_collector_with_options",
    # Sentry
    "init_sentry",
    "capture_exception",
    # Utilities
    "error_is",
    "must_exit",
    "must_exit_with_code",
    "must_exit_with_log",
    "must_exit_with_panic",
    "configure_default_log_func",
    "reset_default_log_func",
    # Go-compat type aliases: stack trace
    "StackTraceOption",
    "StackOption",
    "CallersFunc",
    "FuncForPCFunc",
    "DebugStackFunc",
    # Go-compat type aliases: init / exit / collector
    "InitOption",
    "ExitOption",
    "CollectorOption",
    "WaitOption",
    # Go-compat type aliases: frame / stack trace
    "Frame",
    "StackTrace",
]