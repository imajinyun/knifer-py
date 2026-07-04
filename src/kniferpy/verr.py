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
]