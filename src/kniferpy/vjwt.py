from __future__ import annotations

from datetime import timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ec, rsa

from kniferpy.internal import jwtx


# ── HS256 ───────────────────────────────────────────────────────────────────


def sign_hs256(
    payload: dict[str, Any],
    secret: str | bytes,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    return jwtx.sign_hs256(payload, secret, expires_in=expires_in)


def verify_hs256(
    token: str,
    secret: str | bytes,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    return jwtx.verify_hs256(token, secret, issuer=issuer, audience=audience)


# ── ES256 (ECDSA) ───────────────────────────────────────────────────────────


def sign_es256(
    payload: dict[str, Any],
    private_key: ec.EllipticCurvePrivateKey,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    return jwtx.sign_es256(payload, private_key, expires_in=expires_in)


def verify_es256(
    token: str,
    public_key: ec.EllipticCurvePublicKey,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    return jwtx.verify_es256(token, public_key, issuer=issuer, audience=audience)


# ── PS256 (RSA-PSS) ─────────────────────────────────────────────────────────


def sign_ps256(
    payload: dict[str, Any],
    private_key: rsa.RSAPrivateKey,
    *,
    expires_in: int | timedelta | None = None,
) -> str:
    return jwtx.sign_ps256(payload, private_key, expires_in=expires_in)


def verify_ps256(
    token: str,
    public_key: rsa.RSAPublicKey,
    *,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    return jwtx.verify_ps256(token, public_key, issuer=issuer, audience=audience)


# ── key generation ──────────────────────────────────────────────────────────


def generate_ec_key() -> ec.EllipticCurvePrivateKey:
    return jwtx.generate_ec_key()


def generate_rsa_key(bits: int = 2048) -> rsa.RSAPrivateKey:
    return jwtx.generate_rsa_key(bits)