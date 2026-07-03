from __future__ import annotations

from collections.abc import Callable, Mapping
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


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------


def New() -> dict[K, V]:
    return mapsx.new()


def NewWithCap(hint: int) -> dict[K, V]:
    return mapsx.new_with_cap(hint)


def Of(*kvs: Any) -> dict[Any, Any]:
    return mapsx.of(*kvs)


def OfE(*kvs: Any) -> tuple[dict[Any, Any], str | None]:
    return mapsx.of_e(*kvs)


def FromPairs(*pairs: Pair[K, V]) -> dict[K, V]:
    return mapsx.from_pairs(*pairs)


def FromEntries(entries: list[Pair[K, V]]) -> dict[K, V]:
    return mapsx.from_entries(entries)


def OrEmpty(m: dict[K, V] | None) -> dict[K, V]:
    return mapsx.or_empty(m)


# ---------------------------------------------------------------------------
# predicates
# ---------------------------------------------------------------------------


def is_empty(value: Mapping[K, V]) -> bool:
    return mapsx.is_empty(value)


def IsEmpty(m: dict[K, V]) -> bool:
    return mapsx.is_empty(m)


def IsNotEmpty(m: dict[K, V]) -> bool:
    return mapsx.is_not_empty(m)


def contains_key(value: Mapping[K, V], key: K) -> bool:
    return mapsx.contains_key(value, key)


def ContainsKey(m: dict[K, V], key: K) -> bool:
    return mapsx.contains_key(m, key)


def contains_value(value: Mapping[K, V], item: V) -> bool:
    return mapsx.contains_value(value, item)


def ContainsValue(m: dict[K, V], value: V) -> bool:
    return mapsx.contains_value(m, value)


def Some(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    return mapsx.some(m, pred)


def Every(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    return mapsx.every(m, pred)


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------


def get_or(value: Mapping[K, V], key: K, default: V) -> V:
    return mapsx.get_or(value, key, default)


def Get(m: dict[K, V], key: K) -> V | None:
    return mapsx.get(m, key)


def GetOr(m: dict[K, V], key: K, fallback: V) -> V:
    return mapsx.get_or(m, key, fallback)


def GetAny(m: dict[K, V], *keys: K) -> tuple[V | None, bool]:
    return mapsx.get_any(m, *keys)


def Find(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[K | None, V | None, bool]:
    return mapsx.find(m, pred)


def FindKey(m: dict[K, V], pred: Callable[[V], bool]) -> tuple[K | None, bool]:
    return mapsx.find_key(m, pred)


# ---------------------------------------------------------------------------
# collection views
# ---------------------------------------------------------------------------


def keys(value: Mapping[K, V]) -> list[K]:
    return mapsx.keys(value)


def Keys(m: dict[K, V]) -> list[K]:
    return mapsx.keys(m)


def values(value: Mapping[K, V]) -> list[V]:
    return mapsx.values(value)


def Values(m: dict[K, V]) -> list[V]:
    return mapsx.values(m)


def sorted_keys(value: Mapping[Any, V]) -> list[Any]:
    return mapsx.sorted_keys(value)


def SortedKeys(m: dict[K, V]) -> list[K]:
    return mapsx.sorted_keys(m)


def SortedKeysFunc(m: dict[K, V], less: Callable[[K, K], bool]) -> list[K]:
    return mapsx.sorted_keys_func(m, less)


def SortedValues(m: dict[K, V]) -> list[V]:
    return mapsx.sorted_values(m)


def KeysOf(m: dict[K, V], target: V) -> list[K]:
    return mapsx.keys_of(m, target)


def Entries(m: dict[K, V]) -> list[Pair[K, V]]:
    return mapsx.entries_pairs(m)


# ---------------------------------------------------------------------------
# transformation
# ---------------------------------------------------------------------------


def map_values(value: Mapping[K, V], fn: Callable[[K, V], R]) -> dict[K, R]:
    return mapsx.map_values(value, fn)


def Map(m: dict[K1, V1], transform: Callable[[K1, V1], tuple[K2, V2]]) -> dict[K2, V2]:
    return mapsx.map_pairs(m, transform)


def MapErr(m: dict[K1, V1], transform: Callable[[K1, V1], tuple[K2, V2, str | None]]) -> tuple[dict[K2, V2], str | None]:
    return mapsx.map_pairs_err(m, transform)


def MapKeys(m: dict[K1, V], transform: Callable[[K1, V], K2]) -> dict[K2, V]:
    return mapsx.map_keys(m, transform)


def MapKeysErr(m: dict[K1, V], transform: Callable[[K1, V], tuple[K2, str | None]]) -> tuple[dict[K2, V], str | None]:
    return mapsx.map_keys_err(m, transform)


def MapValues(m: dict[K, V1], transform: Callable[[K, V1], V2]) -> dict[K, V2]:
    return mapsx.map_values(m, transform)


def MapValuesErr(m: dict[K, V1], transform: Callable[[K, V1], tuple[V2, str | None]]) -> tuple[dict[K, V2], str | None]:
    return mapsx.map_values_err(m, transform)


def ToSlice(m: dict[K, V], transform: Callable[[K, V], R]) -> list[R]:
    return mapsx.to_slice(m, transform)


# ---------------------------------------------------------------------------
# filtering
# ---------------------------------------------------------------------------


def filter_items(value: Mapping[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.filter_items(value, pred)


def Filter(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.filter_items(m, pred)


def FilterErr(m: dict[K, V], pred: Callable[[K, V], tuple[bool, str | None]]) -> tuple[dict[K, V], str | None]:
    return mapsx.filter_err(m, pred)


def Reject(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.reject(m, pred)


def FilterKeys(m: dict[K, V], pred: Callable[[K], bool]) -> dict[K, V]:
    return mapsx.filter_keys(m, pred)


def FilterValues(m: dict[K, V], pred: Callable[[V], bool]) -> dict[K, V]:
    return mapsx.filter_values(m, pred)


def PickBy(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.pick_by(m, pred)


def OmitBy(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return mapsx.omit_by(m, pred)


def Partition(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[dict[K, V], dict[K, V]]:
    return mapsx.partition(m, pred)


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def ForEach(m: dict[K, V], fn: Callable[[K, V], None]) -> None:
    return mapsx.for_each(m, fn)


def Reduce(m: dict[K, V], initial: R, fn: Callable[[R, K, V], R]) -> R:
    return mapsx.reduce(m, initial, fn)


def ReduceErr(m: dict[K, V], initial: R, fn: Callable[[R, K, V], tuple[R, str | None]]) -> tuple[R, str | None]:
    return mapsx.reduce_err(m, initial, fn)


def GroupBy(items: list[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    return mapsx.group_by(items, key_fn)


def CountBy(items: list[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    return mapsx.count_by(items, key_fn)


# ---------------------------------------------------------------------------
# set algebra
# ---------------------------------------------------------------------------


def invert(value: Mapping[K, V]) -> dict[V, K]:
    return mapsx.invert(value)


def Inverse(m: dict[K, V]) -> dict[V, K]:
    return mapsx.inverse(m)


def Invert(m: dict[K, V]) -> dict[V, K]:
    return mapsx.invert(m)


def merge(*values: Mapping[K, V]) -> dict[K, V]:
    return mapsx.merge(*values)


def Merge(*maps: dict[K, V]) -> dict[K, V]:
    return mapsx.merge(*maps)


def Assign(*maps: dict[K, V]) -> dict[K, V]:
    return mapsx.assign(*maps)


def MergeWithOverwrite(dst: dict[K, V], *src_maps: dict[K, V]) -> None:
    return mapsx.merge_with_overwrite(dst, *src_maps)


def MergeWithoutOverwrite(dst: dict[K, V], *src_maps: dict[K, V]) -> None:
    return mapsx.merge_without_overwrite(dst, *src_maps)


def MergeFunc(resolve: Callable[[V, V], V], *maps: dict[K, V]) -> dict[K, V]:
    return mapsx.merge_func(resolve, *maps)


def Intersect(*maps: dict[K, V]) -> dict[K, V]:
    return mapsx.intersect(*maps)


def Diff(a: dict[K, V], *others: dict[K, V]) -> dict[K, V]:
    return mapsx.diff(a, *others)


def SymmetricDiff(a: dict[K, V], b: dict[K, V]) -> dict[K, V]:
    return mapsx.symmetric_diff(a, b)


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------


def pick(value: Mapping[K, V], selected: set[K]) -> dict[K, V]:
    return mapsx.pick(value, *selected)


def Pick(m: dict[K, V], *keys: K) -> dict[K, V]:
    return mapsx.pick(m, *keys)


def omit(value: Mapping[K, V], excluded: set[K]) -> dict[K, V]:
    return mapsx.omit(value, *excluded)


def Omit(m: dict[K, V], *keys: K) -> dict[K, V]:
    return mapsx.omit(m, *keys)


# ---------------------------------------------------------------------------
# mutation
# ---------------------------------------------------------------------------


def Clear(m: dict[K, V]) -> None:
    return mapsx.clear(m)


def Update(dst: dict[K, V], src: dict[K, V]) -> dict[K, V]:
    return mapsx.update(dst, src)


def clone(value: Mapping[K, V]) -> dict[K, V]:
    return mapsx.clone(value)


def Clone(m: dict[K, V]) -> dict[K, V]:
    return mapsx.clone(m)


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


def Equal(a: dict[K, V], b: dict[K, V]) -> bool:
    return mapsx.equal(a, b)


def EqualFunc(a: dict[K, V1], b: dict[K, V2], eq: Callable[[V1, V2], bool]) -> bool:
    return mapsx.equal_by(a, b, eq)