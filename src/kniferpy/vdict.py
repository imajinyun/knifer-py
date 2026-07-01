from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


def is_empty(value: Mapping[K, V]) -> bool:
    return len(value) == 0


def contains_key(value: Mapping[K, V], key: K) -> bool:
    return key in value


def contains_value(value: Mapping[K, V], item: V) -> bool:
    return item in value.values()


def get_or(value: Mapping[K, V], key: K, default: V) -> V:
    return value.get(key, default)


def keys(value: Mapping[K, V]) -> list[K]:
    return list(value.keys())


def values(value: Mapping[K, V]) -> list[V]:
    return list(value.values())


def sorted_keys(value: Mapping[Any, V]) -> list[Any]:
    return sorted(value.keys())


def map_values(value: Mapping[K, V], fn: Callable[[K, V], R]) -> dict[K, R]:
    return {key: fn(key, item) for key, item in value.items()}


def filter_items(value: Mapping[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return {key: item for key, item in value.items() if pred(key, item)}


def merge(*values: Mapping[K, V]) -> dict[K, V]:
    result: dict[K, V] = {}
    for value in values:
        result.update(value)
    return result


def pick(value: Mapping[K, V], selected: set[K]) -> dict[K, V]:
    return {key: item for key, item in value.items() if key in selected}


def omit(value: Mapping[K, V], excluded: set[K]) -> dict[K, V]:
    return {key: item for key, item in value.items() if key not in excluded}


def invert(value: Mapping[K, V]) -> dict[V, K]:
    return {item: key for key, item in value.items()}


def clone(value: Mapping[K, V]) -> dict[K, V]:
    return dict(value)
