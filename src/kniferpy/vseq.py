"""Deprecated: use kniferpy.vslice instead.

This module is kept for backward compatibility. All functions emit
DeprecationWarning pointing to the corresponding function in kniferpy.vslice.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Iterable
from typing import TypeVar

from kniferpy.internal import slicex

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R")


def _deprecated(name: str, replacement: str) -> None:
    warnings.warn(
        f"kniferpy.vseq.{name} is deprecated, use kniferpy.vslice.{replacement} instead",
        DeprecationWarning,
        stacklevel=3,
    )


def is_empty(values: Iterable[T]) -> bool:
    _deprecated("is_empty", "is_empty")
    return slicex.is_empty(list(values))


def contains(values: Iterable[T], item: T) -> bool:
    _deprecated("contains", "contains")
    return slicex.contains(list(values), item)


def index_of(values: list[T], item: T) -> int:
    _deprecated("index_of", "index_of")
    return slicex.index_of(values, item)


def reverse(values: Iterable[T]) -> list[T]:
    _deprecated("reverse", "reverse")
    return slicex.reverse(list(values))


def distinct(values: Iterable[T]) -> list[T]:
    _deprecated("distinct", "distinct")
    return slicex.distinct(list(values))


def map_values(values: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    _deprecated("map_values", "map_values")
    return slicex.map_values(list(values), fn)


def filter_values(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    _deprecated("filter_values", "filter_values")
    return slicex.filter_values(list(values), pred)


def reject(values: Iterable[T], pred: Callable[[T], bool]) -> list[T]:
    _deprecated("reject", "reject")
    return slicex.reject(list(values), pred)


def find(values: Iterable[T], pred: Callable[[T], bool]) -> T | None:
    _deprecated("find", "find")
    return slicex.find(list(values), pred)


def group_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    _deprecated("group_by", "group_by")
    return slicex.group_by(list(values), key_fn)


def count_by(values: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    _deprecated("count_by", "count_by")
    return slicex.count_by(list(values), key_fn)


def chunk(values: list[T], size: int) -> list[list[T]]:
    _deprecated("chunk", "chunk")
    return slicex.chunk(values, size)


def window(values: list[T], size: int) -> list[list[T]]:
    _deprecated("window", "window")
    return slicex.window(values, size)


def flatten(values: Iterable[Iterable[T]]) -> list[T]:
    _deprecated("flatten", "flatten")
    return slicex.flatten([list(v) for v in values])


def page(values: list[T], page_no: int, page_size: int) -> list[T]:
    _deprecated("page", "page")
    return slicex.page(values, page_no, page_size)