"""Sequence (generic iterable) helpers — delegates to slicex with list coercion."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

from kniferpy.internal import slicex

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R")


def is_empty(values: Iterable[T]) -> bool:
    return slicex.is_empty(list(values))


def contains(values: Iterable[T], item: T) -> bool:
    return slicex.contains(list(values), item)


def index_of(values: list[T], item: T) -> int:
    return slicex.index_of(values, item)


def reverse(values: Iterable[T]) -> list[T]:
    return slicex.reverse(list(values))


def distinct(values: Iterable[T]) -> list[T]:
    return slicex.distinct(list(values))


def map_values(values: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return slicex.map_values(list(values), fn)


def filter_values(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    return slicex.filter_values(list(values), pred)


def reject(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    return slicex.reject(list(values), pred)


def find(values: Iterable[T], pred: Callable[[T], bool]) -> T | None:
    return slicex.find(list(values), pred)


def group_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    return slicex.group_by(list(values), key_fn)


def count_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    return slicex.count_by(list(values), key_fn)


def chunk(values: list[T], size: int) -> list[list[T]]:
    return slicex.chunk(values, size)


def window(values: list[T], size: int) -> list[list[T]]:
    return slicex.window(values, size)


def flatten(values: Iterable[Iterable[T]]) -> list[T]:
    return slicex.flatten([list(v) for v in values])


def page(values: list[T], page_no: int, page_size: int) -> list[T]:
    return slicex.page(values, page_no, page_size)