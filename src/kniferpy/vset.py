from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable, TypeVar

from kniferpy.internal.setsx import (
    JSONOption,
    _with_set_marshal_func,
    _with_set_unmarshal_func,
    new_int,
    new_int32,
    new_int64,
    new_string,
    new_uint,
    new_uint32,
    new_uint64,
)
from kniferpy.internal.setsx import Set as _Set

T = TypeVar("T")

# Typed aliases (Go compat)
Int = _Set[int]
Int32 = _Set[int]
Int64 = _Set[int]
Uint = _Set[int]
Uint32 = _Set[int]
Uint64 = _Set[int]
String = _Set[str]

__all__ = [
    # Types
    "Int",
    "Int32",
    "Int64",
    "JSONOption",
    "Set",
    "String",
    "Uint",
    "Uint32",
    "Uint64",
    # Option builders
    "WithSetMarshalFunc",
    "WithSetUnmarshalFunc",
    # Constructors
    "New",
    "NewInt",
    "NewInt32",
    "NewInt64",
    "NewString",
    "NewUint",
    "NewUint32",
    "NewUint64",
    # Plain-set helpers
    "contains",
    "equal",
    "from_iterable",
    "intersect",
    "members",
    "new",
    "sub",
    "union",
]


# ---------------------------------------------------------------------------
# option constructors
# ---------------------------------------------------------------------------


def WithSetMarshalFunc(marshal: Callable[[Any], bytes]) -> JSONOption:
    return _with_set_marshal_func(marshal)


def WithSetUnmarshalFunc(unmarshal: Callable[[bytes], Any]) -> JSONOption:
    return _with_set_unmarshal_func(unmarshal)


# ---------------------------------------------------------------------------
# typed constructors
# ---------------------------------------------------------------------------


def NewInt(*items: int) -> _Set[int]:
    return new_int(*items)


def NewInt32(*items: int) -> _Set[int]:
    return new_int32(*items)


def NewInt64(*items: int) -> _Set[int]:
    return new_int64(*items)


def NewUint(*items: int) -> _Set[int]:
    return new_uint(*items)


def NewUint32(*items: int) -> _Set[int]:
    return new_uint32(*items)


def NewUint64(*items: int) -> _Set[int]:
    return new_uint64(*items)


def NewString(*items: str) -> _Set[str]:
    return new_string(*items)


Set = _Set


def New(*items: T) -> _Set[T]:
    return _Set(*items)


# ---------------------------------------------------------------------------
# backward-compatible plain-set helpers
# ---------------------------------------------------------------------------


def new(*items: T) -> set[T]:
    """Create a plain Python set (backward compatible)."""
    return set(items)


def from_iterable(items: Iterable[T]) -> set[T]:
    """Create a plain Python set from an iterable (backward compatible)."""
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
