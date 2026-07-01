from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import chain
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R")


def is_empty(values: Iterable[T]) -> bool:
    return not any(True for _ in values)


def contains(values: Iterable[T], item: T) -> bool:
    return item in values


def index_of(values: list[T], item: T) -> int:
    try:
        return values.index(item)
    except ValueError:
        return -1


def reverse(values: Iterable[T]) -> list[T]:
    return list(reversed(list(values)))


def distinct(values: Iterable[T]) -> list[T]:
    result: list[T] = []
    seen: set[T] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def map_values(values: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(value) for value in values]


def filter_values(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    return [value for value in values if pred(value)]


def reject(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    return [value for value in values if not pred(value)]


def find(values: Iterable[T], pred: Callable[[T], bool]) -> T | None:
    return next((value for value in values if pred(value)), None)


def group_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    grouped: dict[K, list[T]] = {}
    for value in values:
        grouped.setdefault(key_fn(value), []).append(value)
    return grouped


def count_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    counted: dict[K, int] = {}
    for value in values:
        key = key_fn(value)
        counted[key] = counted.get(key, 0) + 1
    return counted


def chunk(values: list[T], size: int) -> list[list[T]]:
    if size <= 0:
        raise ValueError("size must be positive")
    return [values[index : index + size] for index in range(0, len(values), size)]


def window(values: list[T], size: int) -> list[list[T]]:
    if size <= 0:
        raise ValueError("size must be positive")
    if size > len(values):
        return []
    return [values[index : index + size] for index in range(0, len(values) - size + 1)]


def flatten(values: Iterable[Iterable[T]]) -> list[T]:
    return list(chain.from_iterable(values))


def page(values: list[T], page_no: int, page_size: int) -> list[T]:
    if page_no <= 0 or page_size <= 0:
        return []
    start = (page_no - 1) * page_size
    return values[start : start + page_size]
