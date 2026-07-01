from __future__ import annotations

from kniferpy.internal import cryptox


def secure_bytes(length: int) -> bytes:
    return cryptox.secure_bytes(length)


def secure_token_urlsafe(length: int = 32) -> str:
    return cryptox.secure_token_urlsafe(length)


def secure_alnum(length: int = 32) -> str:
    return cryptox.secure_alnum(length)
