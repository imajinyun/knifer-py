import pytest
from datetime import timedelta

from kniferpy import vjwt
from kniferpy.verr import CryptoError

SECRET = "0123456789abcdef0123456789abcdef"


def test_sign_and_verify_hs256() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.verify_hs256(token, SECRET)["sub"] == "user-1"


def test_sign_hs256_with_timedelta_expiry() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET, expires_in=timedelta(hours=1))
    payload = vjwt.verify_hs256(token, SECRET)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_hs256_without_expiry() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    payload = vjwt.verify_hs256(token, SECRET)
    assert "exp" not in payload


def test_verify_hs256_wraps_jwt_errors() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256("not-a-token", SECRET)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_hs256_expired_token() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET, expires_in=-1)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256(token, SECRET)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_hs256_tampered_token() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256(token + "x", SECRET)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_hs256_wrong_secret() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256(token, "x" * 32)
    assert exc_info.value.code == "jwt.verify_failed"


def test_sign_hs256_rejects_weak_secret() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.sign_hs256({"sub": "user-1"}, "short")
    assert exc_info.value.code == "jwt.weak_secret"


def test_verify_hs256_rejects_weak_secret() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256("any.token.here", "short")
    assert exc_info.value.code == "jwt.weak_secret"


def test_hs256_supports_expiry_issuer_and_audience() -> None:
    token = vjwt.sign_hs256(
        {"sub": "user-1", "iss": "kniferpy", "aud": "api"},
        SECRET,
        expires_in=60,
    )
    payload = vjwt.verify_hs256(token, SECRET, issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_hs256_wraps_issuer_mismatch() -> None:
    token = vjwt.sign_hs256({"sub": "user-1", "iss": "kniferpy"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256(token, SECRET, issuer="other")
    assert exc_info.value.code == "jwt.verify_failed"


def test_hs256_wraps_audience_mismatch() -> None:
    token = vjwt.sign_hs256({"sub": "user-1", "aud": "api"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs256(token, SECRET, audience="other")
    assert exc_info.value.code == "jwt.verify_failed"


def test_hs256_empty_payload() -> None:
    token = vjwt.sign_hs256({}, SECRET)
    payload = vjwt.verify_hs256(token, SECRET)
    assert payload == {}


def test_hs256_complex_payload() -> None:
    payload = {
        "sub": "user-1",
        "roles": ["admin", "dev"],
        "meta": {"org": "kniferpy"},
        "iat": 1234567890,
    }
    token = vjwt.sign_hs256(payload, SECRET)
    verified = vjwt.verify_hs256(token, SECRET)
    assert verified["sub"] == "user-1"
    assert verified["roles"] == ["admin", "dev"]
    assert verified["meta"] == {"org": "kniferpy"}


def test_hs256_bytes_secret() -> None:
    secret_bytes = b"0123456789abcdef0123456789abcdef"
    token = vjwt.sign_hs256({"sub": "user-1"}, secret_bytes)
    assert vjwt.verify_hs256(token, secret_bytes)["sub"] == "user-1"