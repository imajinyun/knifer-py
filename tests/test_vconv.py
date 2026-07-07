import pytest

from kniferpy import vconv
from kniferpy.internal import convx
from kniferpy.verr import ValidationError


def test_to_str() -> None:
    assert vconv.to_str(None) == ""
    assert vconv.to_str(True) == "true"
    assert vconv.to_str(False) == "false"
    assert vconv.to_str(42) == "42"
    assert vconv.to_str(b"hi") == "hi"
    assert vconv.to_str(3.14) == "3.14"
    assert vconv.to_str("hello") == "hello"


def test_to_int() -> None:
    assert vconv.to_int("42") == 42
    assert vconv.to_int("3.9") == 3
    assert vconv.to_int(True) == 1
    assert vconv.to_int("bad", default=7) == 7
    with pytest.raises(ValidationError):
        vconv.to_int_e("bad")


def test_to_int_from_float_str() -> None:
    assert vconv.to_int("0") == 0
    assert vconv.to_int("-5") == -5
    assert vconv.to_int("+10") == 10


def test_to_int_from_none() -> None:
    assert vconv.to_int(None, default=0) == 0


def test_to_int_e_none() -> None:
    with pytest.raises(ValidationError):
        vconv.to_int_e(None)


def test_to_float() -> None:
    assert vconv.to_float("3.14") == pytest.approx(3.14)
    assert vconv.to_float(True) == pytest.approx(1.0)
    assert vconv.to_float("bad", default=1.5) == pytest.approx(1.5)
    with pytest.raises(ValidationError):
        vconv.to_float_e("bad")


def test_to_float_from_int() -> None:
    assert vconv.to_float("42") == pytest.approx(42.0)
    assert vconv.to_float("-3.5") == pytest.approx(-3.5)


def test_to_float_from_none() -> None:
    assert vconv.to_float(None, default=0.0) == pytest.approx(0.0)


def test_to_float_e_none() -> None:
    with pytest.raises(ValidationError):
        vconv.to_float_e(None)


def test_to_bool() -> None:
    assert vconv.to_bool("yes") is True
    assert vconv.to_bool("off") is False
    assert vconv.to_bool(0) is False
    assert vconv.to_bool("maybe", default=True) is True
    with pytest.raises(ValidationError):
        vconv.to_bool_e("maybe")


def test_to_bool_all_truthy() -> None:
    for val in ("true", "yes", "on", "1", "y", "t"):
        assert vconv.to_bool(val) is True, f"{val!r} should be True"


def test_to_bool_all_falsy() -> None:
    for val in ("false", "no", "off", "0", "n", "f"):
        assert vconv.to_bool(val) is False, f"{val!r} should be False"


def test_to_bool_from_int() -> None:
    assert vconv.to_bool(1) is True
    assert vconv.to_bool(0) is False


def test_to_bool_none() -> None:
    assert vconv.to_bool(None, default=False) is False


def test_to_bool_e_none() -> None:
    with pytest.raises(ValidationError):
        vconv.to_bool_e(None)


def test_to_bytes() -> None:
    assert vconv.to_bytes(None) == b""
    assert vconv.to_bytes("hi") == b"hi"
    assert vconv.to_bytes(b"raw") == b"raw"
    assert vconv.to_bytes(42) == b"42"


def test_to_bytes_bool() -> None:
    assert vconv.to_bytes(True) == b"true"
    assert vconv.to_bytes(False) == b"false"


def test_to_bytes_empty() -> None:
    assert vconv.to_bytes("") == b""
    assert vconv.to_bytes(b"") == b""


def test_error_sentinel_and_fail_context() -> None:
    assert vconv.ErrInvalidConversion.code == "knifer.conv.invalid"
    err = convx._fail("x", "int")
    assert err.code == "knifer.conv.invalid"
    assert err.context == {"value": "'x'", "target": "int"}


def test_to_str_default_and_error_tuple() -> None:
    bad = b"\xff"

    assert vconv.to_str_default("ok", "fallback") == "ok"
    assert vconv.to_str_default(bad, "fallback") == "fallback"
    assert vconv.to_str_e("ok") == ("ok", None)
    value, err = vconv.to_str_e(bad)
    assert value == ""
    assert err is not None


def test_to_int_e_float_nan_inf_and_ok_variants() -> None:
    assert vconv.to_int_e(7) == 7
    assert vconv.to_int_e(3.9) == 3
    assert vconv.to_int_default("bad", 8) == 8
    assert vconv.to_int_e_ok("42") == (42, True)
    assert vconv.to_int_e_ok("bad") == (0, False)
    with pytest.raises(ValidationError):
        vconv.to_int_e(float("nan"))
    with pytest.raises(ValidationError):
        vconv.to_int_e(float("inf"))


def test_int64_aliases() -> None:
    assert vconv.to_int64_e("42") == 42
    assert vconv.to_int64("bad", default=9) == 9
    assert vconv.to_int64_default("bad", 10) == 10
    assert vconv.to_int64_e_ok("42") == (42, True)
    assert vconv.to_int64_with_options("bad", default=11) == 11


def test_float_default_ok_and_float64_aliases() -> None:
    assert vconv.to_float_e(3) == pytest.approx(3.0)
    assert vconv.to_float_default("bad", 2.5) == pytest.approx(2.5)
    assert vconv.to_float_e_ok("3.5") == (3.5, True)
    assert vconv.to_float_e_ok("bad") == (0.0, False)
    assert vconv.to_float64_e("3.5") == pytest.approx(3.5)
    assert vconv.to_float64("bad", default=4.5) == pytest.approx(4.5)
    assert vconv.to_float64_default("bad", 5.5) == pytest.approx(5.5)
    assert vconv.to_float64_e_ok("3.5") == (3.5, True)
    assert vconv.to_float64_with_options("bad", default=6.5) == pytest.approx(6.5)


def test_bool_default_ok_and_options() -> None:
    assert vconv.to_bool_e(True) is True
    assert vconv.to_bool_e(2) is True
    assert vconv.to_bool_default("bad", True) is True
    assert vconv.to_bool_e_ok("yes") == (True, True)
    assert vconv.to_bool_e_ok("bad") == (False, False)
    assert vconv.to_bool_with_options("bad", default=True) is True
    with pytest.raises(ValidationError):
        vconv.to_bool_e(object())


def test_bytes_default_ok_options_and_encoding_errors() -> None:
    assert vconv.to_bytes(bytearray(b"raw")) == b"raw"
    assert vconv.to_bytes("hé", encoding="utf-8") == "hé".encode()
    assert vconv.to_bytes_default("hé", b"fallback", encoding="ascii") == b"fallback"
    assert vconv.to_bytes_e_ok("hé", encoding="ascii") == (b"", False)
    assert vconv.to_bytes_e_ok("ok") == (b"ok", True)
    assert vconv.to_bytes_with_options("ok") == b"ok"
