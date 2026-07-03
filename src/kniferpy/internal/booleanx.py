from __future__ import annotations

from collections.abc import Iterable


def negate(b: bool) -> bool:
    return not b


def to_int(b: bool) -> int:
    return 1 if b else 0


def and_all(*bs: bool) -> bool:
    return all(bs)


def or_any(*bs: bool) -> bool:
    return any(bs)