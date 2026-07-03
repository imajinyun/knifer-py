from __future__ import annotations

from collections.abc import Iterable

from kniferpy.internal import booleanx


def negate(value: bool) -> bool:
    return booleanx.negate(value)


def to_int(value: bool) -> int:
    return booleanx.to_int(value)


def And(*values: bool) -> bool:
    return booleanx.and_all(*values)


def Or(*values: bool) -> bool:
    return booleanx.or_any(*values)


# Backward compatibility
def all_true(values: Iterable[bool]) -> bool:
    return all(values)


def any_true(values: Iterable[bool]) -> bool:
    return any(values)