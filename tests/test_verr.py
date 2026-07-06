import pytest

from kniferpy.verr import (
    KniferError,
    ValidationError,
    SecurityError,
    DecodeError,
    CryptoError,
    JSONError,
    PanicError,
    Wrapper,
    Collector,
    TimerFactory,
    WithStack,
    WithStackTrace,
    EmptyFormatter,
    SentryDSN,
    LogFunc,
    ERR_CODE_INVALID_INPUT,
    ERR_CODE_NOT_FOUND,
    ERR_CODE_UNSUPPORTED,
    ERR_CODE_UNSAFE_RESOURCE,
    ERR_CODE_TIMEOUT,
    ERR_CODE_PROVIDER_FAILURE,
    ERR_CODE_INTERNAL,
    code_of,
    err_code_name,
    error_is,
    get_stack,
    get_stack_from_error,
    get_stack_trace,
    get_stack_with_skip,
    get_stack_trace_with_options,
    init_sentry,
    capture_exception,
    must_exit,
    must_exit_with_code,
    must_exit_with_log,
    must_exit_with_panic,
    new_collector,
    new_collector_with_options,
    new_error,
    recover,
    recover_without_error,
    reset_stack_frame_cache,
    reset_default_log_func,
    configure_default_log_func,
    wrap_error,
    errorf,
    Init,
    Wrap,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Error codes and constants
# ═══════════════════════════════════════════════════════════════════════════════


def test_error_code_constants() -> None:
    assert ERR_CODE_INVALID_INPUT == "knifer.invalid_input"
    assert ERR_CODE_NOT_FOUND == "knifer.not_found"
    assert ERR_CODE_UNSUPPORTED == "knifer.unsupported"
    assert ERR_CODE_UNSAFE_RESOURCE == "knifer.unsafe_resource"
    assert ERR_CODE_TIMEOUT == "knifer.timeout"
    assert ERR_CODE_PROVIDER_FAILURE == "knifer.provider_failure"
    assert ERR_CODE_INTERNAL == "knifer.internal"


def test_err_code_name() -> None:
    assert err_code_name(ERR_CODE_INVALID_INPUT) == "ERR_CODE_INVALID_INPUT"
    assert err_code_name(ERR_CODE_NOT_FOUND) == "ERR_CODE_NOT_FOUND"
    assert err_code_name("unknown") == "unknown"


def test_sentry_dsn() -> None:
    assert SentryDSN == "SENTRY_DSN"


def test_empty_formatter() -> None:
    assert EmptyFormatter is not None


def test_reset_stack_frame_cache() -> None:
    assert reset_stack_frame_cache() is None


# ═══════════════════════════════════════════════════════════════════════════════
# KniferError and subclasses
# ═══════════════════════════════════════════════════════════════════════════════


def test_validation_error_keeps_code_and_context() -> None:
    err = ValidationError("invalid URL", code="url.invalid", context={"url": "ftp://x"})

    assert isinstance(err, KniferError)
    assert str(err) == "invalid URL"
    assert err.code == "url.invalid"
    assert err.context == {"url": "ftp://x"}


def test_knifer_error_defaults() -> None:
    err = KniferError("something went wrong")
    assert str(err) == "something went wrong"
    assert err.code == "knifer.error"
    assert err.context == {}
    assert err.cause is None
    assert err.multierror is None


def test_knifer_error_error_code() -> None:
    err = KniferError("msg", code="custom.code")
    assert err.error_code() == "custom.code"


def test_knifer_error_unwrap() -> None:
    inner = ValueError("inner")
    err = KniferError("outer", cause=inner)
    assert err.unwrap() is inner


def test_knifer_error_add() -> None:
    err = KniferError("main")
    sub = ValueError("sub")
    err.add(sub)
    assert err.multierror == [sub]
    err.add(KeyError("sub2"))
    assert len(err.multierror) == 2


def test_validation_error_subclass() -> None:
    assert issubclass(ValidationError, KniferError)


def test_security_error_subclass() -> None:
    assert issubclass(SecurityError, KniferError)


def test_decode_error_subclass() -> None:
    assert issubclass(DecodeError, KniferError)


def test_crypto_error_subclass() -> None:
    assert issubclass(CryptoError, KniferError)


def test_json_error_subclass() -> None:
    assert issubclass(JSONError, KniferError)


# ═══════════════════════════════════════════════════════════════════════════════
# Error construction helpers
# ═══════════════════════════════════════════════════════════════════════════════


def test_new_error() -> None:
    err = new_error("test.code", "test message", key="value")
    assert err.code == "test.code"
    assert str(err) == "test message"
    assert err.context == {"key": "value"}


def test_wrap_error() -> None:
    cause = ValueError("original")
    err = wrap_error("test.code", "wrapped", cause, extra="data")
    assert err.code == "test.code"
    assert str(err) == "wrapped"
    assert err.context == {"extra": "data"}
    assert err.__cause__ is cause


def test_errorf() -> None:
    err = errorf("test.code", "formatted %s %d", "hello", 42)
    assert err.code == "test.code"
    assert str(err) == "formatted hello 42"


def test_errorf_no_args() -> None:
    err = errorf("test.code", "plain message")
    assert str(err) == "plain message"


def test_code_of() -> None:
    err = KniferError("msg", code="test.code")
    found_code, ok = code_of(err)
    assert ok is True
    assert found_code == "test.code"


def test_code_of_not_found() -> None:
    found_code, ok = code_of(ValueError("plain"))
    assert ok is False
    assert found_code == ""


def test_code_of_chained() -> None:
    inner = KniferError("inner", code="inner.code")
    outer = ValueError("outer")
    outer.__cause__ = inner
    found_code, ok = code_of(outer)
    assert ok is True
    assert found_code == "inner.code"


# ═══════════════════════════════════════════════════════════════════════════════
# PanicError
# ═══════════════════════════════════════════════════════════════════════════════


def test_panic_error_from_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        panic = PanicError(exc)

    assert isinstance(panic, KniferError)
    assert panic.code == "knifer.panic"
    assert "boom" in str(panic)
    assert "panic" in panic.message
    assert panic.error_code() == "knifer.panic"


def test_panic_error_stack() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        panic = PanicError(exc)

    stack = panic.stack()
    assert "ValueError" in stack
    assert "boom" in stack


def test_panic_error_with_cause() -> None:
    cause = ValueError("cause")
    panic = PanicError("something", cause=cause)
    assert panic.unwrap() is cause


def test_panic_error_with_stack_trace() -> None:
    panic = PanicError("something", stack_trace="custom stack")
    assert panic.stack_trace == "custom stack"
    assert panic.stack() == "custom stack"


def test_panic_error_from_raw_value() -> None:
    panic = PanicError("just a string")
    assert "panic" in panic.message
    assert panic.error_code() == "knifer.panic"


# ═══════════════════════════════════════════════════════════════════════════════
# Stack trace functions
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_stack() -> None:
    stack = get_stack()
    assert isinstance(stack, str)
    assert len(stack) > 0


def test_get_stack_with_skip() -> None:
    stack = get_stack_with_skip(2)
    assert isinstance(stack, str)
    assert len(stack) > 0


def test_get_stack_trace() -> None:
    trace = get_stack_trace()
    assert isinstance(trace, list)
    assert len(trace) > 0
    assert all(isinstance(f, str) for f in trace)


def test_get_stack_trace_with_options() -> None:
    trace = get_stack_trace_with_options(skip=2, depth=10)
    assert isinstance(trace, list)
    assert len(trace) > 0


def test_get_stack_from_error_with_panic() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        panic = PanicError(exc)
    stack = get_stack_from_error(panic)
    assert "ValueError" in stack


def test_get_stack_from_error_with_withstack() -> None:
    class MyError(Exception, WithStack):
        def stack(self) -> str:
            return "my custom stack"
    err = MyError("test")
    stack = get_stack_from_error(err)
    assert stack == "my custom stack"


def test_get_stack_from_plain_error_falls_back() -> None:
    stack = get_stack_from_error(ValueError("plain"))
    assert isinstance(stack, str)


def test_format_stack_frame() -> None:
    from kniferpy.internal.errx import format_stack_frame
    import traceback
    frames = traceback.extract_stack()
    if frames:
        result = format_stack_frame(frames[0])
        assert isinstance(result, str)
        assert "File" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Wrapper
# ═══════════════════════════════════════════════════════════════════════════════


def test_wrapper_exec_success() -> None:
    w = Wrapper(lambda: 42)
    result = w.exec()
    assert result == 42


def test_wrapper_exec_with_info() -> None:
    w = Wrapper(lambda: 42).with_infof("starting")
    result = w.exec()
    assert result == 42


def test_wrapper_exec_with_warn() -> None:
    w = Wrapper(lambda: 42).with_warnf("completed")
    result = w.exec()
    assert result == 42


def test_wrapper_exec_raises() -> None:
    def failing() -> None:
        raise ValueError("failed")
    w = Wrapper(failing).with_errorf("error: %s", "ValueError")
    with pytest.raises(ValueError):
        w.exec()


def test_wrapper_with_custom_log_func() -> None:
    log_calls = []
    def custom_log(level: str, message: str, stack: str) -> None:
        log_calls.append((level, message))

    def failing() -> None:
        raise ValueError("failed")

    w = Wrapper(failing).with_log_func(custom_log).with_errorf("error occurred")
    with pytest.raises(ValueError):
        w.exec()
    assert len(log_calls) == 1
    assert log_calls[0][0] == "error"


def test_recover() -> None:
    with pytest.raises(ValueError):
        recover(lambda: (_ for _ in ()).throw(ValueError("boom")), "error: %s", "ValueError")


def test_recover_without_error() -> None:
    # Should not raise
    recover_without_error(lambda: (_ for _ in ()).throw(ValueError("boom")), "error: %s", "ValueError")


def test_recover_without_error_success() -> None:
    called = []
    def fn() -> None:
        called.append(True)
    recover_without_error(fn)
    assert called == [True]


# ═══════════════════════════════════════════════════════════════════════════════
# Collector
# ═══════════════════════════════════════════════════════════════════════════════


def test_new_collector() -> None:
    c = new_collector()
    assert isinstance(c, Collector)
    assert c.error() is None


def test_collector_collect_single_error() -> None:
    c = new_collector()
    c.collect(ValueError("boom"))
    err = c.error()
    assert isinstance(err, ValueError)


def test_collector_collect_multiple_errors() -> None:
    c = new_collector()
    c.collect(ValueError("boom"))
    c.collect(KeyError("missing"))
    err = c.error()
    assert isinstance(err, KniferError)
    assert "boom" in str(err)
    assert "missing" in str(err)


def test_collector_recover_success() -> None:
    c = new_collector()
    result = c.recover(lambda: 42)
    assert result == 42
    assert c.error() is None


def test_collector_recover_failure() -> None:
    c = new_collector()
    result = c.recover(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert result is None
    err = c.error()
    assert isinstance(err, ValueError)


def test_collector_collect_error() -> None:
    c = new_collector()
    err = c.collect_error(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert isinstance(err, ValueError)


def test_collector_collect_error_success() -> None:
    c = new_collector()
    err = c.collect_error(lambda: 42)
    assert err is None


def test_collector_with_log_func() -> None:
    log_calls = []
    def custom_log(level: str, message: str, stack: str) -> None:
        log_calls.append((level, message))

    c = new_collector().with_log_func(custom_log)
    c.recover(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert len(log_calls) == 1


def test_collector_with_runner() -> None:
    runs = []
    c = new_collector().with_runner(lambda fn: runs.append(fn) or fn())
    def task() -> None:
        raise ValueError("boom")
    c.go_run(task)
    assert len(runs) == 1


def test_collector_default_runner_collects_background_error() -> None:
    c = new_collector()
    c.go_run(lambda: (_ for _ in ()).throw(ValueError("boom")), "background %s", "job")
    ok, err = c.wait_until(1.0)
    assert ok is False
    assert isinstance(err, ValueError)


def test_collector_wait_until_no_error() -> None:
    c = new_collector()
    ok, err = c.wait_until(0.1)
    assert ok is True
    assert err is None


def test_collector_wait_until_with_error() -> None:
    c = new_collector()
    c.collect(ValueError("boom"))
    ok, err = c.wait_until(0.5)
    assert ok is False
    assert isinstance(err, ValueError)


def test_collector_wait_until_with_options() -> None:
    c = new_collector()
    ok, err = c.wait_until_with_options(0.1)
    assert ok is True


def test_new_collector_with_options() -> None:
    log_calls = []
    def custom_log(level: str, message: str, stack: str) -> None:
        log_calls.append((level, message))

    c = new_collector_with_options(log_func=custom_log)
    c.recover(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert len(log_calls) == 1


def test_new_collector_with_options_runner() -> None:
    runs = []
    c = new_collector_with_options(runner=lambda fn: runs.append(fn) or fn())
    c.go_run(lambda: None)
    assert len(runs) == 1


def test_new_collector_with_options_timer_factory_field() -> None:
    timer = TimerFactory(0.01)
    c = new_collector_with_options(timer_factory=timer)
    assert getattr(c, "_timer_factory") is timer


# ═══════════════════════════════════════════════════════════════════════════════
# TimerFactory
# ═══════════════════════════════════════════════════════════════════════════════


def test_timer_factory() -> None:
    tf = TimerFactory(0.1)
    done = tf.create()
    assert not done()
    import time
    time.sleep(0.15)
    assert done()


# ═══════════════════════════════════════════════════════════════════════════════
# Log function configuration
# ═══════════════════════════════════════════════════════════════════════════════


def test_configure_and_reset_default_log_func() -> None:
    log_calls = []
    def custom_log(level: str, message: str, stack: str) -> None:
        log_calls.append((level, message))

    configure_default_log_func(custom_log)
    try:
        c = new_collector()
        c.recover(lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert len(log_calls) == 1
    finally:
        reset_default_log_func()


# ═══════════════════════════════════════════════════════════════════════════════
# error_is
# ═══════════════════════════════════════════════════════════════════════════════


def test_error_is_by_type() -> None:
    err = ValueError("boom")
    assert error_is(err, ValueError) is True
    assert error_is(err, KeyError) is False


def test_error_is_by_code() -> None:
    err = KniferError("msg", code="test.code")
    assert error_is(err, "test.code") is True
    assert error_is(err, "other.code") is False


def test_error_is_chained_type() -> None:
    inner = ValueError("inner")
    outer = KniferError("outer", cause=inner)
    assert error_is(outer, ValueError) is True


def test_error_is_multierror() -> None:
    err = KniferError("main")
    sub = KniferError("sub", code="sub.code")
    err.add(sub)
    assert error_is(err, "sub.code") is True
    assert error_is(err, KniferError) is True
    assert not error_is(err, KeyError)


def test_error_is_panic_error() -> None:
    panic = PanicError("value", cause=ValueError("inner"))
    assert error_is(panic, ValueError) is True
    assert not error_is(PanicError("value"), ValueError)


# ═══════════════════════════════════════════════════════════════════════════════
# Sentry integration
# ═══════════════════════════════════════════════════════════════════════════════


def test_init_sentry_no_sdk() -> None:
    # Should not raise, just log a warning
    init_sentry("https://example.com/1")


def test_capture_exception_no_sdk() -> None:
    result = capture_exception(ValueError("test"))
    assert result is None


def test_Init_alias() -> None:
    Init("https://example.com/1")


# ═══════════════════════════════════════════════════════════════════════════════
# Wrap alias
# ═══════════════════════════════════════════════════════════════════════════════


def test_Wrap_alias() -> None:
    cause = ValueError("original")
    err = Wrap(cause, code="test.code", message="wrapped")
    assert err.code == "test.code"
    assert str(err) == "wrapped"


def test_Wrap_alias_defaults() -> None:
    cause = ValueError("original")
    err = Wrap(cause)
    assert err.code == "knifer.error"
    assert str(err) == "original"


# ═══════════════════════════════════════════════════════════════════════════════
# must_exit and variants
# ═══════════════════════════════════════════════════════════════════════════════


def test_must_exit_no_error() -> None:
    must_exit(None)  # should not exit


def test_must_exit_with_code_no_error() -> None:
    must_exit_with_code(None)  # should not exit


def test_must_exit_with_log_no_error() -> None:
    must_exit_with_log(None)  # should not exit


def test_must_exit_with_panic_no_error() -> None:
    must_exit_with_panic(None)  # should not exit


def test_must_exit_variants_exit_and_log() -> None:
    calls: list[tuple[str, str]] = []

    def log_func(level: str, message: str, stack: str) -> None:
        calls.append((level, message))

    configure_default_log_func(log_func)
    try:
        with pytest.raises(SystemExit) as exit_one:
            must_exit(ValueError("boom"))
        with pytest.raises(SystemExit) as exit_code:
            must_exit_with_code(ValueError("bad"), 7)
        with pytest.raises(SystemExit) as exit_log:
            must_exit_with_log(ValueError("custom"), log_func)
    finally:
        reset_default_log_func()

    assert exit_one.value.code == 1
    assert exit_code.value.code == 7
    assert exit_log.value.code == 1
    assert calls == [("error", "boom"), ("error", "bad"), ("error", "custom")]


def test_must_exit_with_panic_with_error() -> None:
    with pytest.raises(PanicError):
        must_exit_with_panic(ValueError("boom"))


# ═══════════════════════════════════════════════════════════════════════════════
# WithStack and WithStackTrace protocols
# ═══════════════════════════════════════════════════════════════════════════════


def test_withstack_protocol() -> None:
    class MyError(WithStack):
        def stack(self) -> str:
            return "stack"

    assert isinstance(MyError(), WithStack)


def test_withstacktrace_protocol() -> None:
    class MyError(WithStackTrace):
        def stack_trace(self) -> list[str]:
            return ["frame1", "frame2"]

    assert isinstance(MyError(), WithStackTrace)


def test_panic_error_satisfies_withstack() -> None:
    panic = PanicError("test")
    assert isinstance(panic, WithStack)
