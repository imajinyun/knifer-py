from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

_MIN_STRONG_SCORE = 70
_MAX_SCORE = 100

_COMMON_WEAK_PASSWORDS = frozenset(
    {
        "000000",
        "111111",
        "123123",
        "123456",
        "12345678",
        "123456789",
        "admin",
        "iloveyou",
        "letmein",
        "password",
        "password1",
        "qwerty",
        "qwerty123",
        "welcome",
        "woaini",
        "zxcvbn",
    }
)


class Strength(IntEnum):
    UNKNOWN = 0
    VERY_WEAK = 1
    WEAK = 2
    MEDIUM = 3
    STRONG = 4
    VERY_STRONG = 5

    def __str__(self) -> str:
        return {
            Strength.VERY_WEAK: "very weak",
            Strength.WEAK: "weak",
            Strength.MEDIUM: "medium",
            Strength.STRONG: "strong",
            Strength.VERY_STRONG: "very strong",
        }.get(self, "unknown")


@dataclass(slots=True, frozen=True)
class Analysis:
    score: int
    strength: Strength
    length: int
    has_lower: bool
    has_upper: bool
    has_digit: bool
    has_symbol: bool
    repeated: bool
    sequential: bool
    common_weak: bool


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _has_repeated(chars: str) -> bool:
    if len(chars) < 3:
        return False
    run_length = 1
    for index in range(1, len(chars)):
        if chars[index] == chars[index - 1]:
            run_length += 1
            if run_length >= 3:
                return True
        else:
            run_length = 1
    return False


def _has_sequential(chars: str) -> bool:
    if len(chars) < 3:
        return False
    normalized = [ord(ch.lower()) for ch in chars]
    for index in range(2, len(normalized)):
        prev2, prev1, cur = normalized[index - 2], normalized[index - 1], normalized[index]
        if prev1 == prev2 + 1 and cur == prev1 + 1:
            return True
        if prev1 == prev2 - 1 and cur == prev1 - 1:
            return True
    return False


def _is_common_weak(password: str) -> bool:
    return password.strip().lower() in _COMMON_WEAK_PASSWORDS


def _category_count(has_lower: bool, has_upper: bool, has_digit: bool, has_symbol: bool) -> int:
    return sum((has_lower, has_upper, has_digit, has_symbol))


def _length_score(length: int) -> int:
    if length < 8:
        return length * 4
    if length < 12:
        return 30
    if length < 16:
        return 45
    return 55


def _strength_from_score(score: int) -> Strength:
    if score >= 85:
        return Strength.VERY_STRONG
    if score >= _MIN_STRONG_SCORE:
        return Strength.STRONG
    if score >= 50:
        return Strength.MEDIUM
    if score >= 25:
        return Strength.WEAK
    return Strength.VERY_WEAK


def analyze(password: str) -> Analysis:
    length = len(password)
    has_lower = any(ch.islower() for ch in password)
    has_upper = any(ch.isupper() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    has_symbol = any(not (ch.islower() or ch.isupper() or ch.isdigit()) for ch in password)
    repeated = _has_repeated(password)
    sequential = _has_sequential(password)
    common_weak = _is_common_weak(password)

    categories = _category_count(has_lower, has_upper, has_digit, has_symbol)
    if length == 0:
        score = 0
    else:
        score = _length_score(length)
        score += categories * 10
        if categories >= 3:
            score += 10
        if length >= 16:
            score += 5
        if repeated:
            score -= 30
        if sequential:
            score -= 15
        if categories == 1 and score > 35:
            score = 35
        if length < 8 and score > 30:
            score = 30
        if common_weak and score > 10:
            score = 10
        score = _clamp(score, 0, _MAX_SCORE)

    return Analysis(
        score=score,
        strength=_strength_from_score(score),
        length=length,
        has_lower=has_lower,
        has_upper=has_upper,
        has_digit=has_digit,
        has_symbol=has_symbol,
        repeated=repeated,
        sequential=sequential,
        common_weak=common_weak,
    )


def score(password: str) -> int:
    return analyze(password).score


def strength_of(password: str) -> Strength:
    return analyze(password).strength


def is_strong(password: str) -> bool:
    return score(password) >= _MIN_STRONG_SCORE


def is_weak(password: str) -> bool:
    return strength_of(password) in (Strength.VERY_WEAK, Strength.WEAK)
