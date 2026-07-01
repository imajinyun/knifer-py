from __future__ import annotations

from datetime import timedelta
from typing import Any

from kniferpy.internal import jwtx


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
