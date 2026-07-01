from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def new(*items: T) -> set[T]:
    return set(items)


def from_iterable(items: Iterable[T]) -> set[T]:
    return set(items)


def contains(items: set[T], item: T) -> bool:
    return item in items


def union(left: set[T], right: set[T]) -> set[T]:
    return left | right


def intersect(left: set[T], right: set[T]) -> set[T]:
    return left & right


def sub(left: set[T], right: set[T]) -> set[T]:
    return left - right


def equal(left: set[T], right: set[T]) -> bool:
    return left == right


def members(items: set[T]) -> list[T]:
    return list(items)
