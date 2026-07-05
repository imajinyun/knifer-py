from __future__ import annotations

from kniferpy.internal import passx
from kniferpy.internal.passx import Analysis, Strength

__all__ = [
    "Analysis",
    "Strength",
    # Go-compat standalone Strength constants
    "StrengthUnknown",
    "StrengthVeryWeak",
    "StrengthWeak",
    "StrengthMedium",
    "StrengthStrong",
    "StrengthVeryStrong",
    "analyze",
    "score",
    "strength_of",
    "is_strong",
    "is_weak",
]

# ── Go-compat standalone Strength constants ────────────────────────────────────

StrengthUnknown = Strength.UNKNOWN
StrengthVeryWeak = Strength.VERY_WEAK
StrengthWeak = Strength.WEAK
StrengthMedium = Strength.MEDIUM
StrengthStrong = Strength.STRONG
StrengthVeryStrong = Strength.VERY_STRONG


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
