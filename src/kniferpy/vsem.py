from __future__ import annotations

from kniferpy.internal import semx
from kniferpy.internal.semx import Semaphore
from kniferpy.verr import ValidationError

# ── Error sentinels ────────────────────────────────────────────────────────────

ErrInvalidCapacity = ValidationError("semaphore: invalid capacity", code="sem.invalid_capacity")
ErrInvalidWeight = ValidationError("semaphore: invalid weight", code="sem.invalid_weight")
ErrReleaseTooMany = ValidationError(
    "semaphore: release more than acquired", code="sem.release_too_many"
)
ErrClosed = ValidationError("semaphore: closed", code="sem.closed")

__all__ = [
    "Semaphore",
    "ErrClosed",
    "ErrInvalidCapacity",
    "ErrInvalidWeight",
    "ErrReleaseTooMany",
    "new",
    "new_e",
]


def new(cap: int) -> Semaphore:
    return semx.new(cap)


def new_e(cap: int) -> tuple[Semaphore | None, ValidationError | None]:
    try:
        return semx.new(cap), None
    except ValidationError as e:
        return None, e
