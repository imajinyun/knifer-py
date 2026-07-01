from kniferpy import vjwt
from kniferpy.verr import CryptoError

SECRET = "0123456789abcdef0123456789abcdef"


def test_sign_and_verify_hs256() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)

    assert vjwt.verify_hs256(token, SECRET)["sub"] == "user-1"


def test_verify_hs256_wraps_jwt_errors() -> None:
    try:
        vjwt.verify_hs256("not-a-token", SECRET)
    except CryptoError as err:
        assert err.code == "jwt.verify_failed"
    else:
        raise AssertionError("expected CryptoError")


def test_sign_hs256_rejects_weak_secret() -> None:
    try:
        vjwt.sign_hs256({"sub": "user-1"}, "short")
    except CryptoError as err:
        assert err.code == "jwt.weak_secret"
    else:
        raise AssertionError("expected CryptoError")


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

    try:
        vjwt.verify_hs256(token, SECRET, issuer="other")
    except CryptoError as err:
        assert err.code == "jwt.verify_failed"
    else:
        raise AssertionError("expected CryptoError")
