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
    Collector,
    CryptoError,
    DecodeError,
    JSONError,
    KniferError,
    LogFunc,
    PanicError,
    SecurityError,
    ValidationError,
    Wrapper,
    capture_exception,
    code_of,
    configure_default_log_func,
    err_code_name,
    error_is,
    errorf,
    get_stack,
    get_stack_trace,
    init_sentry,
    must_exit,
    must_exit_with_code,
    new_collector,
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
    # Recovery
    "Wrapper",
    "LogFunc",
    "recover",
    "recover_without_error",
    # Collector
    "Collector",
    "new_collector",
    # Sentry
    "init_sentry",
    "capture_exception",
    # Utilities
    "error_is",
    "must_exit",
    "must_exit_with_code",
    "configure_default_log_func",
    "reset_default_log_func",
]