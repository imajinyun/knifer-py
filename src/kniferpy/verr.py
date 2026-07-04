"""Error handling with structured errors, stack traces, and recovery.

Thin facade over kniferpy.internal.errx, porting knifer-go's verr surface.

Provides structured error types, panic recovery, stack trace capture,
a concurrent error Collector, and optional Sentry integration.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal.errx import (
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
    error_is,
    get_stack,
    get_stack_trace,
    init_sentry,
    new_collector,
    recover,
    recover_without_error,
)

__all__ = [
    # Error types
    "KniferError",
    "ValidationError",
    "SecurityError",
    "DecodeError",
    "CryptoError",
    "JSONError",
    "PanicError",
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
]