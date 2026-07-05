from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.algorithms import NoneAlgorithm

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives import hashes

from kniferpy.verr import CryptoError

_MIN_HS256_SECRET_BYTES = 32
_MIN_HS384_SECRET_BYTES = 48
_MIN_HS512_SECRET_BYTES = 64


_HMAC_MIN_BYTES: dict[str, int] = {
    "HS256": _MIN_HS256_SECRET_BYTES,
    "HS384": _MIN_HS384_SECRET_BYTES,
    "HS512": _MIN_HS512_SECRET_BYTES,
}


def min_hmac_key_bytes(algorithm: str) -> int:
    """Return the minimum recommended HMAC key length for ``algorithm``."""
    return _HMAC_MIN_BYTES.get(algorithm.upper(), 0)


def algorithm_name(alg: str) -> str:
    """Return the standard cryptographic algorithm name for a JWT algorithm ID."""
    mapping: dict[str, str] = {
        "HS256": "HmacSHA256",
        "HS384": "HmacSHA384",
        "HS512": "HmacSHA512",
        "RS256": "SHA256withRSA",
        "RS384": "SHA384withRSA",
        "RS512": "SHA512withRSA",
        "ES256": "SHA256withECDSA",
        "ES384": "SHA384withECDSA",
        "ES512": "SHA512withECDSA",
        "PS256": "SHA256withRSAandMGF1",
        "PS384": "SHA384withRSAandMGF1",
        "PS512": "SHA512withRSAandMGF1",
    }
    return mapping.get(alg.upper(), alg.upper())


# ── HMAC signing ──────────────────────────────────────────────────────────────


def _sign_hmac(payload: dict[str, Any], secret: str | bytes, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    _validate_hmac_secret(secret, alg)
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, secret, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_hmac(token: str, secret: str | bytes, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    _validate_hmac_secret(secret, alg)
    try:
        payload = jwt.decode(token, secret, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def _validate_hmac_secret(secret: str | bytes, alg: str) -> None:
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
    min_bytes = _HMAC_MIN_BYTES.get(alg.upper(), 0)
    if len(secret_bytes) < min_bytes:
        raise CryptoError(
            f"{alg} secret must be at least {min_bytes} bytes",
            code="jwt.weak_secret",
            context={"min_bytes": min_bytes},
        )


def sign_hs256(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS256", expires_in=expires_in)


def sign_hs384(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS384", expires_in=expires_in)


def sign_hs512(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS512", expires_in=expires_in)


def verify_hs256(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS256", issuer=issuer, audience=audience)


def verify_hs384(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS384", issuer=issuer, audience=audience)


def verify_hs512(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS512", issuer=issuer, audience=audience)


# ── ECDSA signing ─────────────────────────────────────────────────────────────


# ── ECDSA signing ─────────────────────────────────────────────────────────────


def _sign_ec(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_ec(token: str, public_key: ec.EllipticCurvePublicKey, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, public_key, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def sign_es256(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES256", expires_in=expires_in)


def sign_es384(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES384", expires_in=expires_in)


def sign_es512(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES512", expires_in=expires_in)


def verify_es256(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES256", issuer=issuer, audience=audience)


def verify_es384(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES384", issuer=issuer, audience=audience)


def verify_es512(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES512", issuer=issuer, audience=audience)


# ── RSA-PSS signing ───────────────────────────────────────────────────────────


# ── RSA-PSS signing ───────────────────────────────────────────────────────────


def _sign_ps(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_ps(token: str, public_key: rsa.RSAPublicKey, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, public_key, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def sign_ps256(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS256", expires_in=expires_in)


def sign_ps384(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS384", expires_in=expires_in)


def sign_ps512(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS512", expires_in=expires_in)


def verify_ps256(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS256", issuer=issuer, audience=audience)


def verify_ps384(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS384", issuer=issuer, audience=audience)


def verify_ps512(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS512", issuer=issuer, audience=audience)


# ── JWT object parsing ────────────────────────────────────────────────────────


def parse_jwt(token: str) -> dict[str, Any]:
    """Parse a JWT without verifying the signature."""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.decode_failed") from exc


def new_jwt(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new JWT claims object from a payload dict."""
    return dict(payload)


def jwt_of(token: str) -> dict[str, Any]:
    """Parse a JWT and return the claims object (alias for parse_jwt)."""
    return parse_jwt(token)


def _get_header(token: str) -> dict[str, Any]:
    try:
        return jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.decode_failed") from exc


# ── Strict verification ───────────────────────────────────────────────────────


def verify_strict(token: str, secret: str | bytes, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    """Verify a JWT strictly without algorithm fallback.

    The token's ``alg`` header must match ``alg``.
    """
    header = _get_header(token)
    if header.get("alg", "").upper() != alg.upper():
        raise CryptoError(
            f"algorithm mismatch: expected {alg}, got {header.get('alg')}",
            code="jwt.algorithm_mismatch",
        )
    return _verify_hmac(token, secret, alg, issuer=issuer, audience=audience)


def validate_algorithm(token: str, expected_alg: str) -> bool:
    """Check if the token's ``alg`` header matches the expected algorithm."""
    try:
        header = _get_header(token)
    except CryptoError:
        return False
    return header.get("alg", "").upper() == expected_alg.upper()


# ── Date validation ───────────────────────────────────────────────────────────


def validate_jwt_date(token: str, *, leeway: int = 0) -> bool:
    """Validate ``nbf``, ``exp``, and ``iat`` claims in a JWT.

    ``leeway`` is the acceptable clock skew in seconds.
    """
    try:
        claims = parse_jwt(token)
    except CryptoError:
        return False
    return validate_date(claims, leeway=leeway)


def validate_date(claims: dict[str, Any], *, leeway: int = 0) -> bool:
    """Validate ``nbf``, ``exp``, and ``iat`` claims in a claims dict.

    ``leeway`` is the acceptable clock skew in seconds.
    """
    now = datetime.now(timezone.utc)
    delta = timedelta(seconds=leeway)
    nbf = claims.get("nbf")
    if nbf is not None:
        nbf_time = datetime.fromtimestamp(nbf, tz=timezone.utc)
        if now < nbf_time - delta:
            return False
    exp = claims.get("exp")
    if exp is not None:
        exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        if now > exp_time + delta:
            return False
    iat = claims.get("iat")
    if iat is not None:
        iat_time = datetime.fromtimestamp(iat, tz=timezone.utc)
        if now < iat_time - delta:
            return False
    return True


# ── Signer constructor ────────────────────────────────────────────────────────


def create_signer(algorithm_id: str) -> str:
    """Convert a JWT algorithm ID (e.g. ``HS256``) to a signer name."""
    if not algorithm_id:
        raise CryptoError("empty algorithm ID", code="jwt.invalid_algorithm")
    return algorithm_name(algorithm_id)


# ── key generation ──────────────────────────────────────────────────────────


def generate_ec_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


def generate_rsa_key(bits: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


# ── JWT Builder ───────────────────────────────────────────────────────────────


class JWTBuilder:
    """Fluent JWT token builder and validator.

    Usage::

        token = JWTBuilder().set_subject("user1").set_issuer("myapp").sign_hs256(secret)
        claims = JWTBuilder().require_issuer("myapp").verify_hs256(token, secret)
    """

    def __init__(self) -> None:
        self._claims: dict[str, Any] = {}
        self._expires_in: int | timedelta | None = None
        self._issuer: str | None = None
        self._audience: str | None = None
        self._headers: dict[str, Any] | None = None

    def set_subject(self, sub: str) -> JWTBuilder:
        self._claims["sub"] = sub
        return self

    def set_issuer(self, iss: str) -> JWTBuilder:
        self._claims["iss"] = iss
        return self

    def set_audience(self, aud: str) -> JWTBuilder:
        self._claims["aud"] = aud
        return self

    def set_jwt_id(self, jti: str) -> JWTBuilder:
        self._claims["jti"] = jti
        return self

    def set_expires_in(self, expires_in: int | timedelta) -> JWTBuilder:
        self._expires_in = expires_in
        return self

    def set_claim(self, key: str, value: Any) -> JWTBuilder:
        self._claims[key] = value
        return self

    def set_claims(self, claims: dict[str, Any]) -> JWTBuilder:
        self._claims.update(claims)
        return self

    def set_headers(self, headers: dict[str, Any]) -> JWTBuilder:
        self._headers = headers
        return self

    def require_issuer(self, iss: str) -> JWTBuilder:
        self._issuer = iss
        return self

    def require_audience(self, aud: str) -> JWTBuilder:
        self._audience = aud
        return self

    def sign_hs256(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS256", expires_in=self._expires_in, headers=self._headers)

    def sign_hs384(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS384", expires_in=self._expires_in, headers=self._headers)

    def sign_hs512(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS512", expires_in=self._expires_in, headers=self._headers)

    def sign_es256(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES256", expires_in=self._expires_in, headers=self._headers)

    def sign_es384(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES384", expires_in=self._expires_in, headers=self._headers)

    def sign_es512(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES512", expires_in=self._expires_in, headers=self._headers)

    def sign_ps256(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS256", expires_in=self._expires_in, headers=self._headers)

    def sign_ps384(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS384", expires_in=self._expires_in, headers=self._headers)

    def sign_ps512(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS512", expires_in=self._expires_in, headers=self._headers)

    def verify_hs256(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs256(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_hs384(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs384(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_hs512(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs512(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_es256(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es256(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_es384(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es384(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_es512(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es512(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps256(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps256(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps384(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps384(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps512(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps512(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_strict(self, token: str, secret: str | bytes, alg: str) -> dict[str, Any]:
        return verify_strict(token, secret, alg, issuer=self._issuer, audience=self._audience)

    def parse_unverified(self, token: str) -> dict[str, Any]:
        """Decode a JWT without verifying the signature."""
        return parse_jwt(token)


def new_jwt_builder() -> JWTBuilder:
    return JWTBuilder()


# ── Go-compat generic token creation ─────────────────────────────────────────


def create_token(payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token from payload and HMAC key (Go compat)."""
    return sign_hs256(payload, key)


def create_jwt_token(payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token from payload and HMAC key (Go compat alias)."""
    return sign_hs256(payload, key)


def create_token_with_headers(headers: dict[str, Any], payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token with custom headers (Go compat)."""
    return _sign_hmac(payload, key, "HS256", headers=headers)


def create_token_with_algorithm(payload: dict[str, Any], key: str | bytes, algorithm: str) -> str:
    """Create a token with an explicit HMAC algorithm (Go compat)."""
    return _sign_hmac(payload, key, algorithm)


def create_token_with_headers_and_algorithm(
    headers: dict[str, Any], payload: dict[str, Any], key: str | bytes, algorithm: str
) -> str:
    """Create a token with custom headers and HMAC algorithm (Go compat)."""
    return _sign_hmac(payload, key, algorithm, headers=headers)


# ── Go-compat generic verification ───────────────────────────────────────────


def verify(token: str, key: str | bytes) -> bool:
    """Verify a JWT with an HMAC key using the token's header algorithm (Go compat)."""
    try:
        header = _get_header(token)
        alg = header.get("alg", "HS256")
        match alg.upper():
            case "HS256":
                _verify_hmac(token, key, "HS256")
            case "HS384":
                _verify_hmac(token, key, "HS384")
            case "HS512":
                _verify_hmac(token, key, "HS512")
            case _:
                _verify_hmac(token, key, "HS256")
        return True
    except CryptoError:
        return False


def verify_jwt(token: str, key: str | bytes) -> bool:
    """Verify a JWT with an HMAC key (Go compat alias)."""
    return verify(token, key)


def of_validator(token: str) -> dict[str, Any]:
    """Parse a token and return claims for validation (Go compat)."""
    return parse_jwt(token)