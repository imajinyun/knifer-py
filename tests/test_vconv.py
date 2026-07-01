import pytest

from kniferpy import vconv
from kniferpy.verr import ValidationError


def test_to_str() -> None:
    assert vconv.to_str(None) == ""
    assert vconv.to_str(True) == "true"
    assert vconv.to_str(False) == "false"
    assert vconv.to_str(42) == "42"
    assert vconv.to_str(b"hi") == "hi"


def test_to_int() -> None:
    assert vconv.to_int("42") == 42
    assert vconv.to_int("3.9") == 3
    assert vconv.to_int(True) == 1
    assert vconv.to_int("bad", default=7) == 7
    with pytest.raises(ValidationError):
        vconv.to_int_e("bad")


def test_to_float() -> None:
    assert vconv.to_float("3.14") == pytest.approx(3.14)
    assert vconv.to_float(True) == pytest.approx(1.0)
    assert vconv.to_float("bad", default=1.5) == pytest.approx(1.5)
    with pytest.raises(ValidationError):
        vconv.to_float_e("bad")


def test_to_bool() -> None:
    assert vconv.to_bool("yes") is True
    assert vconv.to_bool("off") is False
    assert vconv.to_bool(0) is False
    assert vconv.to_bool("maybe", default=True) is True
    with pytest.raises(ValidationError):
        vconv.to_bool_e("maybe")


def test_to_bytes() -> None:
    assert vconv.to_bytes(None) == b""
    assert vconv.to_bytes("hi") == b"hi"
    assert vconv.to_bytes(b"raw") == b"raw"
    assert vconv.to_bytes(42) == b"42"
