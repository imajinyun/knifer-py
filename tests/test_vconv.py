import pytest

from kniferpy import vconv
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