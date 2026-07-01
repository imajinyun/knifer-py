from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from kniferpy.verr import CryptoError

_MIN_HS256_SECRET_BYTES = 32


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
