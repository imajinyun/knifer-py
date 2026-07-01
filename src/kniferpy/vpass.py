from __future__ import annotations

from kniferpy.internal import passx
from kniferpy.internal.passx import Analysis, Strength

__all__ = [
    "Analysis",
    "Strength",
    "analyze",
    "score",
    "strength_of",
    "is_strong",
    "is_weak",
]


def analyze(password: str) -> Analysis:
    return passx.analyze(password)


def score(password: str) -> int:
    return passx.score(password)


def strength_of(password: str) -> Strength:
    return passx.strength_of(password)


def is_strong(password: str) -> bool:
    return passx.is_strong(password)


def is_weak(password: str) -> bool:
    return passx.is_weak(password)
