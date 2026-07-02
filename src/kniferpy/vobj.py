from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from kniferpy.internal import objx

T = TypeVar("T")
R = TypeVar("R")

__all__ = [
    "equal",
    "not_equal",
    "length",
    "contains",
    "is_none",
    "is_not_none",
    "is_empty",
    "is_not_empty",
    "default_if_none",
    "default_if_none_func",
    "default_if_none_apply",
    "apply",
    "accept",
    "is_basic_type",
    "is_valid_if_number",
    "compare",
    "compare_none",
    "type_of",
    "type_name",
    "to_string",
    "empty_count",
    "has_none",
    "has_empty",
    "is_all_empty",
    "is_all_not_empty",
]


def equal(a: object, b: object) -> bool:
    return objx.equal(a, b)


def not_equal(a: object, b: object) -> bool:
    return objx.not_equal(a, b)


def length(v: object) -> int:
    return objx.length(v)


def contains(obj: object, element: object) -> bool:
    return objx.contains(obj, element)


def is_none(v: object) -> bool:
    return objx.is_none(v)


def is_not_none(v: object) -> bool:
    return objx.is_not_none(v)


def is_empty(v: object) -> bool:
    return objx.is_empty(v)


def is_not_empty(v: object) -> bool:
    return objx.is_not_empty(v)


def default_if_none(value: T | None, default: T) -> T:
    return objx.default_if_none(value, default)


def default_if_none_func(value: T | None, supplier: Callable[[], T]) -> T:
    return objx.default_if_none_func(value, supplier)


def default_if_none_apply(source: T | None, handle: Callable[[T], R], default: R) -> R:
    return objx.default_if_none_apply(source, handle, default)


def apply(source: T | None, handle: Callable[[T], R]) -> R | None:
    return objx.apply(source, handle)


def accept(source: T | None, consumer: Callable[[T], None]) -> None:
    objx.accept(source, consumer)


def is_basic_type(obj: object) -> bool:
    return objx.is_basic_type(obj)


def is_valid_if_number(obj: object) -> bool:
    return objx.is_valid_if_number(obj)


def compare(a: object, b: object) -> int:
    return objx.compare(a, b)


def compare_none(a: object, b: object, none_greater: bool) -> int:
    return objx.compare_none(a, b, none_greater)


def type_of(obj: object) -> type | None:
    return objx.type_of(obj)


def type_name(obj: object) -> str:
    return objx.type_name(obj)


def to_string(obj: object) -> str:
    return objx.to_string(obj)


def empty_count(*values: object) -> int:
    return objx.empty_count(*values)


def has_none(*values: object) -> bool:
    return objx.has_none(*values)


def has_empty(*values: object) -> bool:
    return objx.has_empty(*values)


def is_all_empty(*values: object) -> bool:
    return objx.is_all_empty(*values)


def is_all_not_empty(*values: object) -> bool:
    return objx.is_all_not_empty(*values)
