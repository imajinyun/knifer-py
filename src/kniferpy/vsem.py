from __future__ import annotations

from kniferpy.internal import semx
from kniferpy.internal.semx import Semaphore

__all__ = ["Semaphore", "new"]


def new(cap: int) -> Semaphore:
    return semx.new(cap)
