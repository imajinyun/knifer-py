from __future__ import annotations

import math
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")

_SIZED = (str, bytes, bytearray, list, tuple, dict, set, frozenset, range)
_CONTAINERS = (list, tuple, set, frozenset)
_BASIC_TYPES = (bool, int, float, complex, str)


def equal(a: object, b: object) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(a == b)


def not_equal(a: object, b: object) -> bool:
    return not equal(a, b)


def length(v: object) -> int:
    if v is None:
        return 0
    try:
        return len(v)  # type: ignore[arg-type]
    except TypeError:
        return -1


def contains(obj: object, element: object) -> bool:
    if obj is None:
        return False
    if isinstance(obj, str):
        if element is None:
            return False
        return str(element) in obj
    if isinstance(obj, dict):
        return any(equal(value, element) for value in obj.values())
    if isinstance(obj, _CONTAINERS):
        return any(equal(item, element) for item in obj)
    return False


def is_none(v: object) -> bool:
    return v is None


def is_not_none(v: object) -> bool:
    return v is not None


def is_empty(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, _SIZED):
        return len(v) == 0
    try:
        return len(v) == 0  # type: ignore[arg-type]
    except TypeError:
        return False


def is_not_empty(v: object) -> bool:
    return not is_empty(v)


def default_if_none(value: T | None, default: T) -> T:
    return value if value is not None else default


def default_if_none_func(value: T | None, supplier: Callable[[], T]) -> T:
    return value if value is not None else supplier()


def default_if_none_apply(source: T | None, handle: Callable[[T], R], default: R) -> R:
    return handle(source) if source is not None else default


def apply(source: T | None, handle: Callable[[T], R]) -> R | None:
    return handle(source) if source is not None else None


def accept(source: T | None, consumer: Callable[[T], None]) -> None:
    if source is not None:
        consumer(source)


def is_basic_type(obj: object) -> bool:
    return isinstance(obj, _BASIC_TYPES)


def is_valid_if_number(obj: object) -> bool:
    if isinstance(obj, bool):
        return True
    if isinstance(obj, float):
        return not (math.isnan(obj) or math.isinf(obj))
    return True


def compare(a: object, b: object) -> int:
    return compare_none(a, b, True)


def compare_none(a: object, b: object, none_greater: bool) -> int:
    if a is None and b is None:
        return 0
    if a is None:
        return 1 if none_greater else -1
    if b is None:
        return -1 if none_greater else 1
    if a < b:  # type: ignore[operator]
        return -1
    if a > b:  # type: ignore[operator]
        return 1
    return 0


def type_of(obj: object) -> type | None:
    return None if obj is None else type(obj)


def type_name(obj: object) -> str:
    return "" if obj is None else type(obj).__name__


def to_string(obj: object) -> str:
    return "null" if obj is None else str(obj)


def empty_count(*values: object) -> int:
    return sum(1 for value in values if is_empty(value))


def has_none(*values: object) -> bool:
    return any(value is None for value in values)


def has_empty(*values: object) -> bool:
    return any(is_empty(value) for value in values)


def is_all_empty(*values: object) -> bool:
    return all(is_empty(value) for value in values)


def is_all_not_empty(*values: object) -> bool:
    return all(is_not_empty(value) for value in values)
