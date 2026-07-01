from __future__ import annotations

from collections.abc import Iterable


def negate(value: bool) -> bool:
    return not value


def to_int(value: bool) -> int:
    return 1 if value else 0


def all_true(values: Iterable[bool]) -> bool:
    return all(values)


def any_true(values: Iterable[bool]) -> bool:
    return any(values)
