"""Deprecated: use kniferpy.vmap instead.

This module is kept for backward compatibility. All PascalCase functions now
emit DeprecationWarning pointing to the corresponding snake_case function in
kniferpy.vmap. The snake_case functions continue to work as before.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from kniferpy.internal import mapsx
from kniferpy.internal.mapsx import Pair

K = TypeVar("K")
V = TypeVar("V")
K1 = TypeVar("K1")
K2 = TypeVar("K2")
V1 = TypeVar("V1")
V2 = TypeVar("V2")
R = TypeVar("R")
T = TypeVar("T")


def _deprecated(name: str, replacement: str) -> None:
    warnings.warn(
        f"kniferpy.vdict.{name} is deprecated, use kniferpy.vmap.{replacement} instead",
        DeprecationWarning,
        stacklevel=3,
    )


# ── construction ─────────────────────────────────────────────────────────────


def New() -> dict[K, V]:
    _deprecated("New", "new")
    return mapsx.new()


def NewWithCap(hint: int) -> dict[K, V]:
    _deprecated("NewWithCap", "new_with_cap")
    return mapsx.new_with_cap(hint)


def Of(*kvs: Any) -> dict[Any, Any]:
    _deprecated("Of", "of")
    return mapsx.of(*kvs)


def OfE(*kvs: Any) -> tuple[dict[Any, Any], Exception | None]:
    _deprecated("OfE", "of_e")
    return mapsx.of_e(*kvs)


def FromPairs(*pairs: Pair[K, V]) -> dict[K, V]:
    _deprecated("FromPairs", "from_pairs")
    return mapsx.from_pairs(*pairs)


def FromEntries(entries: Sequence[Pair[K, V]]) -> dict[K, V]:
    _deprecated("FromEntries", "from_entries")
    return mapsx.from_entries(entries)  # type: ignore[arg-type]


def OrEmpty(m: dict[K, V] | None) -> dict[K, V]:
    _deprecated("OrEmpty", "or_empty")
    return mapsx.or_empty(m)


# ── predicates ───────────────────────────────────────────────────────────────


def is_empty(value: Mapping[K, V]) -> bool:
    return mapsx.is_empty(dict(value))


def IsEmpty(m: dict[K, V]) -> bool:
    _deprecated("IsEmpty", "is_empty")
    return mapsx.is_empty(m)


def IsNotEmpty(m: dict[K, V]) -> bool:
    _deprecated("IsNotEmpty", "is_not_empty")
    return mapsx.is_not_empty(m)


def contains_key(value: Mapping[K, V], key: K) -> bool:
    return mapsx.contains_key(dict(value), key)


def ContainsKey(m: dict[K, V], key: K) -> bool:
    _deprecated("ContainsKey", "contains_key")
    return mapsx.contains_key(m, key)


def contains_value(value: Mapping[K, V], item: V) -> bool:
    return mapsx.contains_value(dict(value), item)


def ContainsValue(m: dict[K, V], value: V) -> bool:
    _deprecated("ContainsValue", "contains_value")
    return mapsx.contains_value(m, value)


def Some(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    _deprecated("Some", "some")
    return mapsx.some(m, pred)


def Every(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    _deprecated("Every", "every")
    return mapsx.every(m, pred)


# ── lookup ───────────────────────────────────────────────────────────────────


def get_or(value: Mapping[K, V], key: K, default: V) -> V:
    return mapsx.get_or(dict(value), key, default)


def Get(m: dict[K, V], key: K) -> V | None:
    _deprecated("Get", "get")
    return mapsx.get(m, key)


def GetOr(m: dict[K, V], key: K, fallback: V) -> V:
    _deprecated("GetOr", "get_or")
    return mapsx.get_or(m, key, fallback)


def GetAny(m: dict[K, V], *keys: K) -> tuple[V | None, bool]:
    _deprecated("GetAny", "get_any")
    return mapsx.get_any(m, *keys)


def Find(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[K, V] | None:
    _deprecated("Find", "find")
    return mapsx.find(m, pred)


def FindKey(m: dict[K, V], pred: Callable[[V], bool]) -> tuple[K, bool]:
    _deprecated("FindKey", "find_key")
    return mapsx.find_key(m, pred)


# ── collection views ─────────────────────────────────────────────────────────


def keys(value: Mapping[K, V]) -> list[K]:
    return mapsx.keys(dict(value))


def Keys(m: dict[K, V]) -> list[K]:
    _deprecated("Keys", "keys")
    return mapsx.keys(m)


def values(value: Mapping[K, V]) -> list[V]:
    return mapsx.values(dict(value))


def Values(m: dict[K, V]) -> list[V]:
    _deprecated("Values", "values")
    return mapsx.values(m)


def sorted_keys(value: Mapping[Any, V]) -> list[Any]:
    return mapsx.sorted_keys(dict(value))


def SortedKeys(m: dict[K, V]) -> list[K]:
    _deprecated("SortedKeys", "sorted_keys")
    return mapsx.sorted_keys(m)


def SortedKeysFunc(m: dict[K, V], less: Callable[[K, K], bool]) -> list[K]:
    _deprecated("SortedKeysFunc", "sorted_keys_by")
    return mapsx.sorted_keys_by(m, less)  # type: ignore[arg-type]


def SortedValues(m: dict[K, V]) -> list[V]:
    _deprecated("SortedValues", "sorted_values")
    return mapsx.sorted_values(m)


def KeysOf(m: dict[K, V], target: V) -> list[K]:
    _deprecated("KeysOf", "keys_of")
    return mapsx.keys_of(m, target)


def Entries(m: dict[K, V]) -> list[Pair[K, V]]:
    _deprecated("Entries", "entries")
    return mapsx.entries_pairs(m)


# ── transformation ───────────────────────────────────────────────────────────


def map_values(value: Mapping[K, V], fn: Callable[[K, V], R]) -> dict[K, R]:
    return mapsx.map_values(dict(value), fn)


def Map(m: dict[K1, V1], transform: Callable[[K1, V1], tuple[K2, V2]]) -> dict[K2, V2]:
    _deprecated("Map", "map_items")
    return mapsx.map_items(m, transform)


def MapErr(m: dict[K1, V1], transform: Callable[[K1, V1], tuple[K2, V2, Exception | None]]) -> tuple[dict[K2, V2], Exception | None]:
    _deprecated("MapErr", "map_err")
    return mapsx.map_err(m, transform)  # type: ignore[arg-type,return-value]


def MapKeys(m: dict[K1, V], transform: Callable[[K1, V], K2]) -> dict[K2, V]:
    _deprecated("MapKeys", "map_keys")
    return mapsx.map_keys(m, transform)


def MapKeysErr(m: dict[K1, V], transform: Callable[[K1, V], tuple[K2, Exception | None]]) -> tuple[dict[K2, V], Exception | None]:
    _deprecated("MapKeysErr", "map_keys_err")
    return mapsx.map_keys_err(m, transform)  # type: ignore[arg-type,return-value]


def MapValues(m: dict[K, V1], transform: Callable[[K, V1], V2]) -> dict[K, V2]:
    _deprecated("MapValues", "map_values")
    return mapsx.map_values(m, transform)


def MapValuesErr(m: dict[K, V1], transform: Callable[[K, V1], tuple[V2, Exception | None]]) -> tuple[dict[K, V2], Exception | None]:
    _deprecated("MapValuesErr", "map_values_err")
    return mapsx.map_values_err(m, transform)  # type: ignore[arg-type,return-value]


def ToSlice(m: dict[K, V], transform: Callable[[K, V], R]) -> list[R]:
    _deprecated("ToSlice", "to_slice")
    return mapsx.to_slice(m, transform)


# ── filtering ────────────────────────────────────────────────────────────────


def filter_items(value: Mapping[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.filter_items(dict(value), pred)


def Filter(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    _deprecated("Filter", "filter_items")
    return mapsx.filter_items(m, pred)


def FilterErr(m: dict[K, V], pred: Callable[[K, V], tuple[bool, Exception | None]]) -> tuple[dict[K, V], Exception | None]:
    _deprecated("FilterErr", "filter_err")
    return mapsx.filter_err(m, pred)  # type: ignore[arg-type,return-value]


def Reject(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    _deprecated("Reject", "reject")
    return mapsx.reject(m, pred)


def FilterKeys(m: dict[K, V], pred: Callable[[K], bool]) -> dict[K, V]:
    _deprecated("FilterKeys", "filter_keys")
    return mapsx.filter_keys(m, pred)


def FilterValues(m: dict[K, V], pred: Callable[[V], bool]) -> dict[K, V]:
    _deprecated("FilterValues", "filter_values")
    return mapsx.filter_values(m, pred)


def PickBy(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    _deprecated("PickBy", "pick_by")
    return mapsx.pick_by(m, pred)


def OmitBy(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    _deprecated("OmitBy", "omit_by")
    return mapsx.omit_by(m, pred)


def Partition(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[dict[K, V], dict[K, V]]:
    _deprecated("Partition", "partition")
    return mapsx.partition(m, pred)


# ── aggregation ──────────────────────────────────────────────────────────────


def ForEach(m: dict[K, V], fn: Callable[[K, V], None]) -> None:
    _deprecated("ForEach", "for_each")
    return mapsx.for_each(m, fn)


def Reduce(m: dict[K, V], initial: R, fn: Callable[[R, K, V], R]) -> R:
    _deprecated("Reduce", "reduce")
    return mapsx.reduce(m, initial, fn)


def ReduceErr(m: dict[K, V], initial: R, fn: Callable[[R, K, V], tuple[R, Exception | None]]) -> tuple[R, Exception | None]:
    _deprecated("ReduceErr", "reduce_err")
    return mapsx.reduce_err(m, initial, fn)  # type: ignore[arg-type,return-value]


def GroupBy(items: list[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    _deprecated("GroupBy", "group_by")
    return mapsx.group_by(items, key_fn)


def CountBy(items: list[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    _deprecated("CountBy", "count_by")
    return mapsx.count_by(items, key_fn)


# ── set algebra ──────────────────────────────────────────────────────────────


def invert(value: Mapping[K, V]) -> dict[V, K]:
    return mapsx.invert(dict(value))


def Inverse(m: dict[K, V]) -> dict[V, K]:
    _deprecated("Inverse", "inverse")
    return mapsx.inverse(m)


def Invert(m: dict[K, V]) -> dict[V, K]:
    _deprecated("Invert", "invert")
    return mapsx.invert(m)


def merge(*values: dict[K, V]) -> dict[K, V]:
    return mapsx.merge(*values)


def Merge(*maps: dict[K, V]) -> dict[K, V]:
    _deprecated("Merge", "merge")
    return mapsx.merge(*maps)


def Assign(*maps: dict[K, V]) -> dict[K, V]:
    _deprecated("Assign", "assign")
    return mapsx.assign(*maps)


def MergeWithOverwrite(dst: dict[K, V], *src_maps: dict[K, V]) -> None:
    _deprecated("MergeWithOverwrite", "merge_with_overwrite")
    return mapsx.merge_with_overwrite(dst, *src_maps)


def MergeWithoutOverwrite(dst: dict[K, V], *src_maps: dict[K, V]) -> None:
    _deprecated("MergeWithoutOverwrite", "merge_without_overwrite")
    return mapsx.merge_without_overwrite(dst, *src_maps)


def MergeFunc(resolve: Callable[[V, V], V], *maps: dict[K, V]) -> dict[K, V]:
    _deprecated("MergeFunc", "merge_func")
    return mapsx.merge_func(resolve, *maps)


def Intersect(*maps: dict[K, V]) -> dict[K, V]:
    _deprecated("Intersect", "intersect")
    return mapsx.intersect(*maps)


def Diff(a: dict[K, V], *others: dict[K, V]) -> dict[K, V]:
    _deprecated("Diff", "diff")
    return mapsx.diff(a, *others)


def SymmetricDiff(a: dict[K, V], b: dict[K, V]) -> dict[K, V]:
    _deprecated("SymmetricDiff", "symmetric_diff")
    return mapsx.symmetric_diff(a, b)


# ── selection ────────────────────────────────────────────────────────────────


def pick(value: Mapping[K, V], selected: set[K]) -> dict[K, V]:
    return mapsx.pick(dict(value), *selected)


def Pick(m: dict[K, V], *keys: K) -> dict[K, V]:
    _deprecated("Pick", "pick")
    return mapsx.pick(m, *keys)


def omit(value: Mapping[K, V], excluded: set[K]) -> dict[K, V]:
    return mapsx.omit(dict(value), *excluded)


def Omit(m: dict[K, V], *keys: K) -> dict[K, V]:
    _deprecated("Omit", "omit")
    return mapsx.omit(m, *keys)


# ── mutation ─────────────────────────────────────────────────────────────────


def Clear(m: dict[K, V]) -> None:
    _deprecated("Clear", "clear")
    return mapsx.clear(m)


def Update(dst: dict[K, V], src: dict[K, V]) -> dict[K, V]:
    _deprecated("Update", "update")
    return mapsx.update(dst, src)


def clone(value: Mapping[K, V]) -> dict[K, V]:
    return mapsx.clone(dict(value))


def Clone(m: dict[K, V]) -> dict[K, V]:
    _deprecated("Clone", "clone")
    return mapsx.clone(m)


# ── comparison ───────────────────────────────────────────────────────────────


def Equal(a: dict[K, V], b: dict[K, V]) -> bool:
    _deprecated("Equal", "equal")
    return mapsx.equal(a, b)


def EqualFunc(a: dict[K, V1], b: dict[K, V2], eq: Callable[[V1, V2], bool]) -> bool:
    _deprecated("EqualFunc", "equal_by")
    return mapsx.equal_by(a, b, eq)