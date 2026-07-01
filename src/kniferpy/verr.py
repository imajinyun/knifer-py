from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KniferError(Exception):
    message: str
    code: str = "knifer.error"
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class ValidationError(KniferError):
    pass


class SecurityError(KniferError):
    pass


class DecodeError(KniferError):
    pass


class CryptoError(KniferError):
    pass
