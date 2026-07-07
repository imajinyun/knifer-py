import base64
import time
from datetime import timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from kniferpy import vjwt
from kniferpy.verr import CryptoError

SECRET = "0123456789abcdef0123456789abcdef"  # 32 bytes
SECRET_HS384 = "0123456789abcdef0123456789abcdef0123456789abcdef"  # 48 bytes
SECRET_HS512 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # 64 bytes


# ═══════════════════════════════════════════════════════════════════════════════
# HS256 (existing tests)
# ═══════════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════════
# HS384 sign/verify
# ═══════════════════════════════════════════════════════════════════════════════


def test_sign_and_verify_hs384() -> None:
    token = vjwt.sign_hs384({"sub": "user-1"}, SECRET_HS384)
    assert vjwt.verify_hs384(token, SECRET_HS384)["sub"] == "user-1"


def test_sign_hs384_with_expiry() -> None:
    token = vjwt.sign_hs384({"sub": "user-1"}, SECRET_HS384, expires_in=3600)
    payload = vjwt.verify_hs384(token, SECRET_HS384)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_hs384_with_timedelta_expiry() -> None:
    token = vjwt.sign_hs384({"sub": "user-1"}, SECRET_HS384, expires_in=timedelta(hours=1))
    payload = vjwt.verify_hs384(token, SECRET_HS384)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_verify_hs384_wraps_jwt_errors() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs384("not-a-token", SECRET_HS384)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_hs384_expired_token() -> None:
    token = vjwt.sign_hs384({"sub": "user-1"}, SECRET_HS384, expires_in=-1)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs384(token, SECRET_HS384)
    assert exc_info.value.code == "jwt.verify_failed"


def test_sign_hs384_rejects_weak_secret() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.sign_hs384({"sub": "user-1"}, "short")
    assert exc_info.value.code == "jwt.weak_secret"


def test_hs384_issuer_and_audience() -> None:
    token = vjwt.sign_hs384({"sub": "user-1", "iss": "kniferpy", "aud": "api"}, SECRET_HS384)
    payload = vjwt.verify_hs384(token, SECRET_HS384, issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_hs384_issuer_mismatch() -> None:
    token = vjwt.sign_hs384({"sub": "user-1", "iss": "kniferpy"}, SECRET_HS384)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs384(token, SECRET_HS384, issuer="other")
    assert exc_info.value.code == "jwt.verify_failed"


def test_hs384_audience_mismatch() -> None:
    token = vjwt.sign_hs384({"sub": "user-1", "aud": "api"}, SECRET_HS384)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs384(token, SECRET_HS384, audience="other")
    assert exc_info.value.code == "jwt.verify_failed"


def test_hs384_bytes_secret() -> None:
    secret_bytes = SECRET_HS384.encode("utf-8")
    token = vjwt.sign_hs384({"sub": "user-1"}, secret_bytes)
    assert vjwt.verify_hs384(token, secret_bytes)["sub"] == "user-1"


# ═══════════════════════════════════════════════════════════════════════════════
# HS512 sign/verify
# ═══════════════════════════════════════════════════════════════════════════════


def test_sign_and_verify_hs512() -> None:
    token = vjwt.sign_hs512({"sub": "user-1"}, SECRET_HS512)
    assert vjwt.verify_hs512(token, SECRET_HS512)["sub"] == "user-1"


def test_sign_hs512_with_expiry() -> None:
    token = vjwt.sign_hs512({"sub": "user-1"}, SECRET_HS512, expires_in=3600)
    payload = vjwt.verify_hs512(token, SECRET_HS512)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_hs512_with_timedelta_expiry() -> None:
    token = vjwt.sign_hs512({"sub": "user-1"}, SECRET_HS512, expires_in=timedelta(hours=1))
    payload = vjwt.verify_hs512(token, SECRET_HS512)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_verify_hs512_wraps_jwt_errors() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs512("not-a-token", SECRET_HS512)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_hs512_expired_token() -> None:
    token = vjwt.sign_hs512({"sub": "user-1"}, SECRET_HS512, expires_in=-1)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_hs512(token, SECRET_HS512)
    assert exc_info.value.code == "jwt.verify_failed"


def test_sign_hs512_rejects_weak_secret() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.sign_hs512({"sub": "user-1"}, "short")
    assert exc_info.value.code == "jwt.weak_secret"


def test_hs512_issuer_and_audience() -> None:
    token = vjwt.sign_hs512({"sub": "user-1", "iss": "kniferpy", "aud": "api"}, SECRET_HS512)
    payload = vjwt.verify_hs512(token, SECRET_HS512, issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_hs512_bytes_secret() -> None:
    secret_bytes = SECRET_HS512.encode("utf-8")
    token = vjwt.sign_hs512({"sub": "user-1"}, secret_bytes)
    assert vjwt.verify_hs512(token, secret_bytes)["sub"] == "user-1"


# ═══════════════════════════════════════════════════════════════════════════════
# Utility functions
# ═══════════════════════════════════════════════════════════════════════════════


def test_min_hmac_key_bytes() -> None:
    assert vjwt.min_hmac_key_bytes("HS256") == 32
    assert vjwt.min_hmac_key_bytes("HS384") == 48
    assert vjwt.min_hmac_key_bytes("HS512") == 64
    assert vjwt.min_hmac_key_bytes("unknown") == 0
    assert vjwt.min_hmac_key_bytes("hs256") == 32


def test_algorithm_name() -> None:
    assert vjwt.algorithm_name("HS256") == "HmacSHA256"
    assert vjwt.algorithm_name("HS384") == "HmacSHA384"
    assert vjwt.algorithm_name("HS512") == "HmacSHA512"
    assert vjwt.algorithm_name("RS256") == "SHA256withRSA"
    assert vjwt.algorithm_name("ES256") == "SHA256withECDSA"
    assert vjwt.algorithm_name("PS256") == "SHA256withRSAandMGF1"
    assert vjwt.algorithm_name("PS384") == "SHA384withRSAandMGF1"
    assert vjwt.algorithm_name("PS512") == "SHA512withRSAandMGF1"
    assert vjwt.algorithm_name("unknown") == "UNKNOWN"


def test_create_signer() -> None:
    assert vjwt.create_signer("HS256") == "HmacSHA256"
    assert vjwt.create_signer("HS384") == "HmacSHA384"


def test_create_signer_rejects_empty() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.create_signer("")
    assert exc_info.value.code == "jwt.invalid_algorithm"


# ═══════════════════════════════════════════════════════════════════════════════
# JWT parsing (parse_jwt, new_jwt, jwt_of)
# ═══════════════════════════════════════════════════════════════════════════════


def test_parse_jwt() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    claims = vjwt.parse_jwt(token)
    assert claims["sub"] == "user-1"


def test_parse_jwt_invalid_token() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.parse_jwt("not-a-token")
    assert exc_info.value.code == "jwt.decode_failed"


def test_new_jwt() -> None:
    payload = {"sub": "user-1"}
    claims = vjwt.new_jwt(payload)
    assert claims["sub"] == "user-1"
    assert claims is not payload  # returns a copy


def test_jwt_of() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    claims = vjwt.jwt_of(token)
    assert claims["sub"] == "user-1"


def test_new_jwt_builder() -> None:
    builder = vjwt.new_jwt_builder()
    assert isinstance(builder, vjwt.JWTBuilder)


# ═══════════════════════════════════════════════════════════════════════════════
# Strict verification and validate_algorithm
# ═══════════════════════════════════════════════════════════════════════════════


def test_verify_strict_hs256() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    payload = vjwt.verify_strict(token, SECRET, "HS256")
    assert payload["sub"] == "user-1"


def test_verify_strict_algorithm_mismatch() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_strict(token, SECRET, "HS384")
    assert exc_info.value.code == "jwt.algorithm_mismatch"


def test_verify_strict_with_issuer_audience() -> None:
    token = vjwt.sign_hs256({"sub": "user-1", "iss": "kniferpy", "aud": "api"}, SECRET)
    payload = vjwt.verify_strict(token, SECRET, "HS256", issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_validate_algorithm_match() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.validate_algorithm(token, "HS256") is True


def test_validate_algorithm_mismatch() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.validate_algorithm(token, "HS384") is False


def test_validate_algorithm_invalid_token() -> None:
    assert vjwt.validate_algorithm("not-a-token", "HS256") is False


# ═══════════════════════════════════════════════════════════════════════════════
# Date validation
# ═══════════════════════════════════════════════════════════════════════════════


def test_validate_date_valid() -> None:
    now = int(time.time())
    claims = {"iat": now - 60, "exp": now + 3600}
    assert vjwt.validate_date(claims) is True


def test_validate_date_expired() -> None:
    claims = {"exp": int(time.time()) - 3600}
    assert vjwt.validate_date(claims) is False


def test_validate_date_not_before() -> None:
    claims = {"nbf": int(time.time()) + 3600}
    assert vjwt.validate_date(claims) is False


def test_validate_date_iat_future() -> None:
    claims = {"iat": int(time.time()) + 3600}
    assert vjwt.validate_date(claims) is False


def test_validate_date_with_leeway() -> None:
    now = int(time.time())
    claims = {"exp": now - 30, "nbf": now + 30}
    assert vjwt.validate_date(claims, leeway=60) is True


def test_validate_date_empty() -> None:
    assert vjwt.validate_date({}) is True


def test_validate_jwt_date() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET, expires_in=3600)
    assert vjwt.validate_jwt_date(token) is True


def test_validate_jwt_date_expired() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET, expires_in=-1)
    assert vjwt.validate_jwt_date(token) is False


def test_validate_jwt_date_invalid_token() -> None:
    assert vjwt.validate_jwt_date("not-a-token") is False


# ═══════════════════════════════════════════════════════════════════════════════
# Key generation
# ═══════════════════════════════════════════════════════════════════════════════


def test_generate_ec_key() -> None:
    key = vjwt.generate_ec_key()
    assert isinstance(key, ec.EllipticCurvePrivateKey)


def test_generate_rsa_key() -> None:
    key = vjwt.generate_rsa_key()
    assert isinstance(key, rsa.RSAPrivateKey)
    assert key.key_size == 2048


def test_generate_rsa_key_4096() -> None:
    key = vjwt.generate_rsa_key(bits=4096)
    assert key.key_size == 4096


# ═══════════════════════════════════════════════════════════════════════════════
# ECDSA sign/verify
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def ec_key_p256() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def ec_key_p384() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP384R1())


@pytest.fixture(scope="module")
def ec_key_p521() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP521R1())


def test_sign_and_verify_es256(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    token = vjwt.sign_es256({"sub": "user-1"}, ec_key_p256)
    assert vjwt.verify_es256(token, pub)["sub"] == "user-1"


def test_sign_es256_with_expiry(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    token = vjwt.sign_es256({"sub": "user-1"}, ec_key_p256, expires_in=3600)
    payload = vjwt.verify_es256(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_es256_with_timedelta_expiry(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    token = vjwt.sign_es256({"sub": "user-1"}, ec_key_p256, expires_in=timedelta(hours=1))
    payload = vjwt.verify_es256(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_verify_es256_wraps_errors(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_es256("not-a-token", pub)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_es256_wrong_key(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    other_key = ec.generate_private_key(ec.SECP256R1())
    pub = ec_key_p256.public_key()
    token = vjwt.sign_es256({"sub": "user-1"}, other_key)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_es256(token, pub)
    assert exc_info.value.code == "jwt.verify_failed"


def test_es256_issuer_and_audience(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    token = vjwt.sign_es256({"sub": "user-1", "iss": "kniferpy", "aud": "api"}, ec_key_p256)
    payload = vjwt.verify_es256(token, pub, issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_sign_and_verify_es384(ec_key_p384: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p384.public_key()
    token = vjwt.sign_es384({"sub": "user-1"}, ec_key_p384)
    assert vjwt.verify_es384(token, pub)["sub"] == "user-1"


def test_sign_es384_with_expiry(ec_key_p384: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p384.public_key()
    token = vjwt.sign_es384({"sub": "user-1"}, ec_key_p384, expires_in=3600)
    payload = vjwt.verify_es384(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_and_verify_es512(ec_key_p521: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p521.public_key()
    token = vjwt.sign_es512({"sub": "user-1"}, ec_key_p521)
    assert vjwt.verify_es512(token, pub)["sub"] == "user-1"


def test_sign_es512_with_expiry(ec_key_p521: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p521.public_key()
    token = vjwt.sign_es512({"sub": "user-1"}, ec_key_p521, expires_in=3600)
    payload = vjwt.verify_es512(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


# ═══════════════════════════════════════════════════════════════════════════════
# RSA-PSS sign/verify
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return vjwt.generate_rsa_key()


def test_sign_and_verify_ps256(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps256({"sub": "user-1"}, rsa_key)
    assert vjwt.verify_ps256(token, pub)["sub"] == "user-1"


def test_sign_ps256_with_expiry(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps256({"sub": "user-1"}, rsa_key, expires_in=3600)
    payload = vjwt.verify_ps256(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_ps256_with_timedelta_expiry(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps256({"sub": "user-1"}, rsa_key, expires_in=timedelta(hours=1))
    payload = vjwt.verify_ps256(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_verify_ps256_wraps_errors(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_ps256("not-a-token", pub)
    assert exc_info.value.code == "jwt.verify_failed"


def test_verify_ps256_wrong_key(rsa_key: rsa.RSAPrivateKey) -> None:
    other_key = vjwt.generate_rsa_key()
    pub = rsa_key.public_key()
    token = vjwt.sign_ps256({"sub": "user-1"}, other_key)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.verify_ps256(token, pub)
    assert exc_info.value.code == "jwt.verify_failed"


def test_ps256_issuer_and_audience(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps256({"sub": "user-1", "iss": "kniferpy", "aud": "api"}, rsa_key)
    payload = vjwt.verify_ps256(token, pub, issuer="kniferpy", audience="api")
    assert payload["sub"] == "user-1"


def test_sign_and_verify_ps384(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps384({"sub": "user-1"}, rsa_key)
    assert vjwt.verify_ps384(token, pub)["sub"] == "user-1"


def test_sign_ps384_with_expiry(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps384({"sub": "user-1"}, rsa_key, expires_in=3600)
    payload = vjwt.verify_ps384(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_sign_and_verify_ps512(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps512({"sub": "user-1"}, rsa_key)
    assert vjwt.verify_ps512(token, pub)["sub"] == "user-1"


def test_sign_ps512_with_expiry(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.sign_ps512({"sub": "user-1"}, rsa_key, expires_in=3600)
    payload = vjwt.verify_ps512(token, pub)
    assert payload["sub"] == "user-1"
    assert "exp" in payload


# ═══════════════════════════════════════════════════════════════════════════════
# JWTBuilder
# ═══════════════════════════════════════════════════════════════════════════════


def test_builder_sign_verify_hs256() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_issuer("kniferpy").sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().require_issuer("kniferpy").verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_hs384() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").sign_hs384(SECRET_HS384)
    claims = vjwt.JWTBuilder().verify_hs384(token, SECRET_HS384)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_hs512() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").sign_hs512(SECRET_HS512)
    claims = vjwt.JWTBuilder().verify_hs512(token, SECRET_HS512)
    assert claims["sub"] == "user-1"


def test_builder_with_expires_in() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_expires_in(3600).sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert "exp" in claims


def test_builder_with_timedelta_expires_in() -> None:
    token = (
        vjwt.JWTBuilder()
        .set_subject("user-1")
        .set_expires_in(timedelta(hours=2))
        .sign_hs256(SECRET)
    )
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert "exp" in claims


def test_builder_set_jwt_id() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_jwt_id("jti-123").sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert claims["jti"] == "jti-123"


def test_builder_set_claim() -> None:
    token = vjwt.JWTBuilder().set_claim("role", "admin").sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert claims["role"] == "admin"


def test_builder_set_claims() -> None:
    token = vjwt.JWTBuilder().set_claims({"role": "admin", "org": "kniferpy"}).sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert claims["role"] == "admin"
    assert claims["org"] == "kniferpy"


def test_builder_set_headers() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_headers({"kid": "key-1"}).sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_builder_require_audience() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_audience("api").sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().require_audience("api").verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_builder_audience_mismatch() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").set_audience("api").sign_hs256(SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.JWTBuilder().require_audience("other").verify_hs256(token, SECRET)
    assert exc_info.value.code == "jwt.verify_failed"


def test_builder_sign_verify_es256(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_es256(ec_key_p256)
    claims = vjwt.JWTBuilder().verify_es256(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_es384(ec_key_p384: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p384.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_es384(ec_key_p384)
    claims = vjwt.JWTBuilder().verify_es384(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_es512(ec_key_p521: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p521.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_es512(ec_key_p521)
    claims = vjwt.JWTBuilder().verify_es512(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_ps256(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_ps256(rsa_key)
    claims = vjwt.JWTBuilder().verify_ps256(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_ps384(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_ps384(rsa_key)
    claims = vjwt.JWTBuilder().verify_ps384(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_sign_verify_ps512(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    token = vjwt.JWTBuilder().set_subject("user-1").sign_ps512(rsa_key)
    claims = vjwt.JWTBuilder().verify_ps512(token, pub)
    assert claims["sub"] == "user-1"


def test_builder_verify_strict() -> None:
    token = vjwt.JWTBuilder().set_subject("user-1").sign_hs256(SECRET)
    claims = vjwt.JWTBuilder().verify_strict(token, SECRET, "HS256")
    assert claims["sub"] == "user-1"


def test_builder_parse_unverified() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    claims = vjwt.JWTBuilder().parse_unverified(token)
    assert claims["sub"] == "user-1"


# ═══════════════════════════════════════════════════════════════════════════════
# JWTSigner - HMAC
# ═══════════════════════════════════════════════════════════════════════════════


def test_new_hmac_signer_hs256() -> None:
    signer = vjwt.new_hmac_signer("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_new_hmac_signer_hs384() -> None:
    signer = vjwt.new_hmac_signer("HS384", SECRET_HS384.encode())
    assert signer.algorithm() == "HS384"


def test_new_hmac_signer_hs512() -> None:
    signer = vjwt.new_hmac_signer("HS512", SECRET_HS512.encode())
    assert signer.algorithm() == "HS512"


def test_new_hmac_signer_with_str_key() -> None:
    signer = vjwt.new_hmac_signer("HS256", SECRET)
    assert signer.algorithm() == "HS256"


def test_new_hmac_signer_unsupported_algorithm() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.new_hmac_signer("INVALID", SECRET.encode())
    assert exc_info.value.code == "jwt.unsupported_algorithm"


def test_hmac_signer_sign_and_verify() -> None:
    signer = vjwt.new_hmac_signer("HS256", SECRET.encode())
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert signer.verify(header_b64, payload_b64, sig)


def test_hmac_signer_verify_tampered() -> None:
    signer = vjwt.new_hmac_signer("HS256", SECRET.encode())
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert not signer.verify(header_b64, "tampered", sig)


def test_new_hmac_signer_strict() -> None:
    signer = vjwt.new_hmac_signer_strict("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_new_hmac_signer_strict_weak_key() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.new_hmac_signer_strict("HS256", b"short")
    assert exc_info.value.code == "jwt.weak_secret"


def test_must_hmac_signer() -> None:
    signer = vjwt.must_hmac_signer("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_must_hmac_signer_invalid() -> None:
    with pytest.raises(CryptoError):
        vjwt.must_hmac_signer("INVALID", SECRET.encode())


def test_create_signer_from_key() -> None:
    signer = vjwt.create_signer_from_key("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_create_signer_from_key_none_rejected() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.create_signer_from_key("NONE", SECRET.encode())
    assert exc_info.value.code == "jwt.unsupported_algorithm"


def test_create_signer_from_key_strict() -> None:
    signer = vjwt.create_signer_from_key_strict("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_create_signer_from_key_strict_none_rejected() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vjwt.create_signer_from_key_strict("NONE", SECRET.encode())
    assert exc_info.value.code == "jwt.unsupported_algorithm"


# ═══════════════════════════════════════════════════════════════════════════════
# JWTSigner - RSA-PSS
# ═══════════════════════════════════════════════════════════════════════════════


def test_new_rsa_pss_signer_ps256(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    signer = vjwt.new_rsa_pss_signer("PS256", rsa_key, pub)
    assert signer.algorithm() == "PS256"


def test_new_rsa_pss_signer_ps384(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    signer = vjwt.new_rsa_pss_signer("PS384", rsa_key, pub)
    assert signer.algorithm() == "PS384"


def test_new_rsa_pss_signer_ps512(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    signer = vjwt.new_rsa_pss_signer("PS512", rsa_key, pub)
    assert signer.algorithm() == "PS512"


def test_new_rsa_pss_signer_unsupported() -> None:
    key = vjwt.generate_rsa_key()
    pub = key.public_key()
    with pytest.raises(CryptoError) as exc_info:
        vjwt.new_rsa_pss_signer("INVALID", key, pub)
    assert exc_info.value.code == "jwt.unsupported_algorithm"


def test_rsa_pss_signer_sign_and_verify(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    signer = vjwt.new_rsa_pss_signer("PS256", rsa_key, pub)
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"PS256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert signer.verify(header_b64, payload_b64, sig)


def test_rsa_pss_signer_verify_tampered(rsa_key: rsa.RSAPrivateKey) -> None:
    pub = rsa_key.public_key()
    signer = vjwt.new_rsa_pss_signer("PS256", rsa_key, pub)
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"PS256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert not signer.verify(header_b64, "tampered", sig)


# ═══════════════════════════════════════════════════════════════════════════════
# JWTSigner - ECDSA
# ═══════════════════════════════════════════════════════════════════════════════


def test_new_ecdsa_signer_es256(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    signer = vjwt.new_ecdsa_signer("ES256", ec_key_p256, pub)
    assert signer.algorithm() == "ES256"


def test_new_ecdsa_signer_es384(ec_key_p384: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p384.public_key()
    signer = vjwt.new_ecdsa_signer("ES384", ec_key_p384, pub)
    assert signer.algorithm() == "ES384"


def test_new_ecdsa_signer_es512(ec_key_p521: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p521.public_key()
    signer = vjwt.new_ecdsa_signer("ES512", ec_key_p521, pub)
    assert signer.algorithm() == "ES512"


def test_new_ecdsa_signer_unsupported(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    with pytest.raises(CryptoError) as exc_info:
        vjwt.new_ecdsa_signer("INVALID", ec_key_p256, pub)
    assert exc_info.value.code == "jwt.unsupported_algorithm"


def test_ecdsa_signer_sign_and_verify(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    signer = vjwt.new_ecdsa_signer("ES256", ec_key_p256, pub)
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"ES256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert signer.verify(header_b64, payload_b64, sig)


def test_ecdsa_signer_verify_tampered(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    pub = ec_key_p256.public_key()
    signer = vjwt.new_ecdsa_signer("ES256", ec_key_p256, pub)
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"ES256"}').rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(b'{"sub":"user-1"}').rstrip(b"=").decode()
    sig = signer.sign(header_b64, payload_b64)
    assert not signer.verify(header_b64, "tampered", sig)


# ═══════════════════════════════════════════════════════════════════════════════
# Go-compat signer constructors
# ═══════════════════════════════════════════════════════════════════════════════


def test_HS256() -> None:
    signer = vjwt.HS256(SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_HS384() -> None:
    signer = vjwt.HS384(SECRET_HS384.encode())
    assert signer.algorithm() == "HS384"


def test_HS512() -> None:
    signer = vjwt.HS512(SECRET_HS512.encode())
    assert signer.algorithm() == "HS512"


def test_PS256(rsa_key: rsa.RSAPrivateKey) -> None:
    signer = vjwt.PS256(rsa_key, rsa_key.public_key())
    assert signer.algorithm() == "PS256"


def test_PS384(rsa_key: rsa.RSAPrivateKey) -> None:
    signer = vjwt.PS384(rsa_key, rsa_key.public_key())
    assert signer.algorithm() == "PS384"


def test_PS512(rsa_key: rsa.RSAPrivateKey) -> None:
    signer = vjwt.PS512(rsa_key, rsa_key.public_key())
    assert signer.algorithm() == "PS512"


def test_ES256(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.ES256(ec_key_p256, ec_key_p256.public_key())
    assert signer.algorithm() == "ES256"


def test_ES384(ec_key_p384: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.ES384(ec_key_p384, ec_key_p384.public_key())
    assert signer.algorithm() == "ES384"


def test_ES512(ec_key_p521: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.ES512(ec_key_p521, ec_key_p521.public_key())
    assert signer.algorithm() == "ES512"


# ═══════════════════════════════════════════════════════════════════════════════
# Go-compat jwtsigner_* wrappers
# ═══════════════════════════════════════════════════════════════════════════════


def test_jwtsigner_hmac() -> None:
    signer = vjwt.jwtsigner_hmac("HS256", SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_jwtsigner_hs256() -> None:
    signer = vjwt.jwtsigner_hs256(SECRET.encode())
    assert signer.algorithm() == "HS256"


def test_jwtsigner_ecdsa(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.jwtsigner_ecdsa("ES256", ec_key_p256, ec_key_p256.public_key())
    assert signer.algorithm() == "ES256"


def test_jwtsigner_es256(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.jwtsigner_es256(ec_key_p256, ec_key_p256.public_key())
    assert signer.algorithm() == "ES256"


# ═══════════════════════════════════════════════════════════════════════════════
# Go-compat token creation / verification
# ═══════════════════════════════════════════════════════════════════════════════


def test_create_token() -> None:
    token = vjwt.create_token({"sub": "user-1"}, SECRET)
    claims = vjwt.verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_create_jwt_token() -> None:
    token = vjwt.create_jwt_token({"sub": "user-1"}, SECRET)
    claims = vjwt.verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_create_token_with_headers() -> None:
    token = vjwt.create_token_with_headers({"kid": "key-1"}, {"sub": "user-1"}, SECRET)
    claims = vjwt.verify_hs256(token, SECRET)
    assert claims["sub"] == "user-1"


def test_create_token_with_algorithm_hs384() -> None:
    token = vjwt.create_token_with_algorithm({"sub": "user-1"}, SECRET_HS384, "HS384")
    claims = vjwt.verify_hs384(token, SECRET_HS384)
    assert claims["sub"] == "user-1"


def test_create_token_with_algorithm_hs512() -> None:
    token = vjwt.create_token_with_algorithm({"sub": "user-1"}, SECRET_HS512, "HS512")
    claims = vjwt.verify_hs512(token, SECRET_HS512)
    assert claims["sub"] == "user-1"


def test_create_token_with_headers_and_algorithm() -> None:
    token = vjwt.create_token_with_headers_and_algorithm(
        {"kid": "key-1"}, {"sub": "user-1"}, SECRET_HS384, "HS384"
    )
    claims = vjwt.verify_hs384(token, SECRET_HS384)
    assert claims["sub"] == "user-1"


def test_verify() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.verify(token, SECRET) is True


def test_verify_invalid_token() -> None:
    assert vjwt.verify("not-a-token", SECRET) is False


def test_verify_wrong_secret() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.verify(token, "x" * 32) is False


def test_verify_jwt() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    assert vjwt.verify_jwt(token, SECRET) is True


def test_verify_jwt_invalid() -> None:
    assert vjwt.verify_jwt("not-a-token", SECRET) is False


def test_of_validator() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    claims = vjwt.of_validator(token)
    assert claims["sub"] == "user-1"


# ═══════════════════════════════════════════════════════════════════════════════
# Go-compat create_token_with_signer / verify_with_signer
# ═══════════════════════════════════════════════════════════════════════════════


def test_create_token_with_signer_hs256() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_with_signer(token, signer) is True


def test_create_token_with_signer_rsa(rsa_key: rsa.RSAPrivateKey) -> None:
    signer = vjwt.PS256(rsa_key, rsa_key.public_key())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_with_signer(token, signer) is True


def test_create_token_with_signer_ecdsa(ec_key_p256: ec.EllipticCurvePrivateKey) -> None:
    signer = vjwt.ES256(ec_key_p256, ec_key_p256.public_key())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_with_signer(token, signer) is True


def test_create_token_with_headers_and_signer() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_headers_and_signer({"kid": "key-1"}, {"sub": "user-1"}, signer)
    assert vjwt.verify_with_signer(token, signer) is True


def test_create_jwt_token_with_signer() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_jwt_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_with_signer(token, signer) is True


def test_verify_with_signer_invalid_format() -> None:
    signer = vjwt.HS256(SECRET.encode())
    assert vjwt.verify_with_signer("not-a-token", signer) is False


def test_verify_with_signer_tampered() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    parts = token.split(".")
    tampered = f"{parts[0]}.tampered.{parts[2]}"
    assert vjwt.verify_with_signer(tampered, signer) is False


def test_verify_jwt_with_signer() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_jwt_with_signer(token, signer) is True


def test_verify_strict_signer() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    assert vjwt.verify_strict_signer(token, signer) is True


def test_verify_strict_signer_algorithm_mismatch() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    other_signer = vjwt.HS384(SECRET_HS384.encode())
    assert vjwt.verify_strict_signer(token, other_signer) is False


def test_verify_strict_signer_invalid_format() -> None:
    signer = vjwt.HS256(SECRET.encode())
    assert vjwt.verify_strict_signer("not-a-token", signer) is False


def test_verify_strict_signer_invalid_header() -> None:
    signer = vjwt.HS256(SECRET.encode())
    assert vjwt.verify_strict_signer("!!!.!!!.!!!", signer) is False


def test_validate_algorithm_with_signer() -> None:
    signer = vjwt.HS256(SECRET.encode())
    token = vjwt.create_token_with_signer({"sub": "user-1"}, signer)
    vjwt.validate_algorithm_with_signer(token, signer)  # should not raise


def test_validate_algorithm_with_signer_mismatch() -> None:
    signer = vjwt.HS384(SECRET_HS384.encode())
    token = vjwt.sign_hs256({"sub": "user-1"}, SECRET)
    with pytest.raises(CryptoError) as exc_info:
        vjwt.validate_algorithm_with_signer(token, signer)
    assert exc_info.value.code == "jwt.algorithm_mismatch"


def test_validate_algorithm_with_signer_invalid_format() -> None:
    signer = vjwt.HS256(SECRET.encode())
    with pytest.raises(CryptoError) as exc_info:
        vjwt.validate_algorithm_with_signer("not-a-token", signer)
    assert exc_info.value.code == "jwt.invalid_token"


def test_validate_algorithm_with_signer_invalid_header() -> None:
    signer = vjwt.HS256(SECRET.encode())
    with pytest.raises(CryptoError) as exc_info:
        vjwt.validate_algorithm_with_signer("!!!.!!!.!!!", signer)
    assert exc_info.value.code == "jwt.invalid_token"
