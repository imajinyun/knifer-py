from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives import hashes

from kniferpy.verr import CryptoError

_MIN_HS256_SECRET_BYTES = 32


# ── HS256 ───────────────────────────────────────────────────────────────────


def sign_hs256(
    payload: dict[str, Any],
    secret: str | bytes,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    _validate_hs256_secret(secret)
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, secret, algorithm="HS256")
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def verify_hs256(
    token: str,
    secret: str | bytes,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    _validate_hs256_secret(secret)
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            audience=audience,
        )
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def _validate_hs256_secret(secret: str | bytes) -> None:
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
    if len(secret_bytes) < _MIN_HS256_SECRET_BYTES:
        raise CryptoError(
            "HS256 secret must be at least 32 bytes",
            code="jwt.weak_secret",
            context={"min_bytes": _MIN_HS256_SECRET_BYTES},
        )


# ── ES256 (ECDSA P-256) ─────────────────────────────────────────────────────


def sign_es256(
    payload: dict[str, Any],
    private_key: ec.EllipticCurvePrivateKey,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm="ES256")
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def verify_es256(
    token: str,
    public_key: ec.EllipticCurvePublicKey,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            issuer=issuer,
            audience=audience,
        )
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


# ── PS256 (RSA-PSS) ─────────────────────────────────────────────────────────


def sign_ps256(
    payload: dict[str, Any],
    private_key: rsa.RSAPrivateKey,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm="PS256")
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def verify_ps256(
    token: str,
    public_key: rsa.RSAPublicKey,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["PS256"],
            issuer=issuer,
            audience=audience,
        )
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


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

    def require_issuer(self, iss: str) -> JWTBuilder:
        self._issuer = iss
        return self

    def require_audience(self, aud: str) -> JWTBuilder:
        self._audience = aud
        return self

    def sign_hs256(self, secret: str | bytes) -> str:
        return sign_hs256(self._claims, secret, expires_in=self._expires_in)

    def sign_es256(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return sign_es256(self._claims, private_key, expires_in=self._expires_in)

    def sign_ps256(self, private_key: rsa.RSAPrivateKey) -> str:
        return sign_ps256(self._claims, private_key, expires_in=self._expires_in)

    def verify_hs256(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs256(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_es256(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es256(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps256(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps256(token, public_key, issuer=self._issuer, audience=self._audience)

    def parse_unverified(self, token: str) -> dict[str, Any]:
        """Decode a JWT without verifying the signature."""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError as exc:
            raise CryptoError(str(exc), code="jwt.decode_failed") from exc


def new_jwt_builder() -> JWTBuilder:
    return JWTBuilder()