import pytest

from kniferpy import vrand


def test_secure_bytes_length() -> None:
    assert len(vrand.secure_bytes(32)) == 32


def test_secure_token_urlsafe_length() -> None:
    token = vrand.secure_token_urlsafe(16)
    assert isinstance(token, str)
    assert len(token) >= 16


def test_secure_alnum_length_and_charset() -> None:
    token = vrand.secure_alnum(24)

    assert len(token) == 24
    assert token.isalnum()


def test_secure_bytes_rejects_non_positive_length() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vrand.secure_bytes(0)
