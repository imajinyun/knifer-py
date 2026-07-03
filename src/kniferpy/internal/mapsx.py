"""Map/dict helpers.

Ports knifer-go's internal/maps with Python-idiomatic mappings:

- Go generics [K comparable, V any] -> Python duck typing
- Go iter.Seq2[K, V] -> Python generators via iter_items/iter_keys/iter_values
- Go (V, bool) -> V | None
- Go (K, V, bool) -> (K, V) | None

Errors use kniferpy.verr types with codes knifer.map.<reason>.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from kniferpy.verr import KniferError

K = TypeVar("K")
V = TypeVar("V")
V1 = TypeVar("V1")
V2 = TypeVar("V2")
K1 = TypeVar("K1")
K2 = TypeVar("K2")
T = TypeVar("T")
R = TypeVar("R")


def new() -> dict[K, V]:
    return {}


def new_with_cap(hint: int) -> dict[K, V]:
    return {}


def of(*kvs: Any) -> dict[Any, Any]:
    out: dict[Any, Any] = {}
    it = iter(kvs)
    for k in it:
        try:
            v = next(it)
        except StopIteration:
            break
        out[k] = v
    return out


def of_e(*kvs: Any) -> tuple[dict[Any, Any], Exception | None]:
    out: dict[Any, Any] = {}
    it = iter(kvs)
    for k in it:
        try:
            v = next(it)
        except StopIteration:
            return out, ValueError("odd number of arguments")
        out[k] = v
    return out, None


def from_pairs(*pairs: tuple[K, V]) -> dict[K, V]:
    return dict(pairs)


def from_entries(entries: list[tuple[K, V]]) -> dict[K, V]:
    return dict(entries)


def or_empty(m: dict[K, V] | None) -> dict[K, V]:
    return m if m is not None else {}


def is_empty(m: dict[K, V]) -> bool:
    return len(m) == 0


def is_not_empty(m: dict[K, V]) -> bool:
    return len(m) > 0


def contains_key(m: dict[K, V], key: K) -> bool:
    return key in m


def contains_value(m: dict[K, V], value: V) -> bool:
    return value in m.values()


def some(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    return any(pred(k, v) for k, v in m.items())


def every(m: dict[K, V], pred: Callable[[K, V], bool]) -> bool:
    return all(pred(k, v) for k, v in m.items())


def get(m: dict[K, V], key: K) -> V | None:
    return m.get(key)


def get_or(m: dict[K, V], key: K, fallback: V) -> V:
    return m.get(key, fallback)


def get_any(m: dict[K, V], *keys: K) -> tuple[V | None, bool]:
    for key in keys:
        if key in m:
            return m[key], True
    return None, False


def find(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[K, V] | None:
    for k, v in m.items():
        if pred(k, v):
            return (k, v)
    return None


def find_key(m: dict[K, V], pred: Callable[[V], bool]) -> tuple[K, bool]:
    for k, v in m.items():
        if pred(v):
            return k, True
    return (None, False)  # type: ignore[return-value]


def keys(m: dict[K, V]) -> list[K]:
    return list(m.keys())


def values(m: dict[K, V]) -> list[V]:
    return list(m.values())


def sorted_keys(m: dict[K, V]) -> list[K]:
    return sorted(m.keys())  # type: ignore[type-var]


def sorted_keys_by(m: dict[K, V], key_fn: Callable[[K], Any]) -> list[K]:
    return sorted(m.keys(), key=key_fn)


def sorted_values(m: dict[K, V]) -> list[V]:
    return sorted(m.values())  # type: ignore[type-var]


def keys_of(m: dict[K, V], target: V) -> list[K]:
    return [k for k, v in m.items() if v == target]


def entries(m: dict[K, V]) -> list[tuple[K, V]]:
    return list(m.items())


def iter_items(m: dict[K, V]) -> Iterable[tuple[K, V]]:
    yield from m.items()


def iter_keys(m: dict[K, V]) -> Iterable[K]:
    yield from m.keys()


def iter_values(m: dict[K, V]) -> Iterable[V]:
    yield from m.values()


def map_items(m: dict[K1, V1], transform: Callable[[K1, V1], tuple[K2, V2]]) -> dict[K2, V2]:
    return dict(transform(k, v) for k, v in m.items())


def map_err(
    m: dict[K1, V1],
    transform: Callable[[K1, V1], tuple[K2, V2, None] | tuple[None, None, Exception]],
) -> dict[K2, V2]:
    out: dict[K2, V2] = {}
    for k, v in m.items():
        nk, nv, err = transform(k, v)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.map.map_err")
        out[nk] = nv  # type: ignore[index,assignment]
    return out


def map_keys(m: dict[K1, V], transform: Callable[[K1, V], K2]) -> dict[K2, V]:
    return {transform(k, v): v for k, v in m.items()}


def map_keys_err(
    m: dict[K1, V],
    transform: Callable[[K1, V], tuple[K2, None] | tuple[None, Exception]],
) -> dict[K2, V]:
    out: dict[K2, V] = {}
    for k, v in m.items():
        nk, err = transform(k, v)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.map.map_keys_err")
        out[nk] = v  # type: ignore[index]
    return out


def map_values(m: dict[K, V1], transform: Callable[[K, V1], V2]) -> dict[K, V2]:
    return {k: transform(k, v) for k, v in m.items()}


def map_values_err(
    m: dict[K, V1],
    transform: Callable[[K, V1], tuple[V2, None] | tuple[None, Exception]],
) -> dict[K, V2]:
    out: dict[K, V2] = {}
    for k, v in m.items():
        nv, err = transform(k, v)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.map.map_values_err")
        out[k] = nv  # type: ignore[assignment]
    return out


def to_slice(m: dict[K, V], transform: Callable[[K, V], R]) -> list[R]:
    return [transform(k, v) for k, v in m.items()]


def filter_items(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return {k: v for k, v in m.items() if pred(k, v)}


def filter_err(
    m: dict[K, V],
    pred: Callable[[K, V], tuple[bool, None] | tuple[None, Exception]],
) -> dict[K, V]:
    out: dict[K, V] = {}
    for k, v in m.items():
        ok, err = pred(k, v)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.map.filter_err")
        if ok:
            out[k] = v
    return out


def reject(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return {k: v for k, v in m.items() if not pred(k, v)}


def filter_keys(m: dict[K, V], pred: Callable[[K], bool]) -> dict[K, V]:
    return {k: v for k, v in m.items() if pred(k)}


def filter_values(m: dict[K, V], pred: Callable[[V], bool]) -> dict[K, V]:
    return {k: v for k, v in m.items() if pred(v)}


def pick_by(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return filter_items(m, pred)


def omit_by(m: dict[K, V], pred: Callable[[K, V], bool]) -> dict[K, V]:
    return reject(m, pred)


def partition(m: dict[K, V], pred: Callable[[K, V], bool]) -> tuple[dict[K, V], dict[K, V]]:
    matched: dict[K, V] = {}
    rejected: dict[K, V] = {}
    for k, v in m.items():
        if pred(k, v):
            matched[k] = v
        else:
            rejected[k] = v
    return matched, rejected


def for_each(m: dict[K, V], fn: Callable[[K, V], None]) -> None:
    for k, v in m.items():
        fn(k, v)


def reduce(m: dict[K, V], initial: R, fn: Callable[[R, K, V], R]) -> R:
    acc = initial
    for k, v in m.items():
        acc = fn(acc, k, v)
    return acc


def reduce_err(
    m: dict[K, V],
    initial: R,
    fn: Callable[[R, K, V], tuple[R, None] | tuple[None, Exception]],
) -> R:
    acc = initial
    for k, v in m.items():
        result, err = fn(acc, k, v)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.map.reduce_err")
        acc = result  # type: ignore[assignment]
    return acc


def group_by(items: list[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    out: dict[K, list[T]] = {}
    for item in items:
        k = key_fn(item)
        out.setdefault(k, []).append(item)
    return out


def count_by(items: list[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    out: dict[K, int] = {}
    for item in items:
        k = key_fn(item)
        out[k] = out.get(k, 0) + 1
    return out


def inverse(m: dict[K, V]) -> dict[V, K]:
    return {v: k for k, v in m.items()}


def invert(m: dict[K, V]) -> dict[V, K]:
    return inverse(m)


def merge(*maps: dict[K, V]) -> dict[K, V]:
    out: dict[K, V] = {}
    for m in maps:
        out.update(m)
    return out


def assign(*maps: dict[K, V]) -> dict[K, V]:
    return merge(*maps)


def merge_with_overwrite(dst: dict[K, V], *srcs: dict[K, V]) -> None:
    for src in srcs:
        dst.update(src)


def merge_without_overwrite(dst: dict[K, V], *srcs: dict[K, V]) -> None:
    for src in srcs:
        for k, v in src.items():
            if k not in dst:
                dst[k] = v


def merge_func(resolve: Callable[[V, V], V], *maps: dict[K, V]) -> dict[K, V]:
    out: dict[K, V] = {}
    for m in maps:
        for k, v in m.items():
            if k in out:
                out[k] = resolve(out[k], v)
            else:
                out[k] = v
    return out


def intersect(*maps: dict[K, V]) -> dict[K, V]:
    if not maps:
        return {}
    common = set(maps[0].keys())
    for m in maps[1:]:
        common &= set(m.keys())
    return {k: maps[0][k] for k in common}


def diff(m: dict[K, V], *others: dict[K, V]) -> dict[K, V]:
    excluded: set[K] = set()
    for other in others:
        excluded.update(other.keys())
    return {k: v for k, v in m.items() if k not in excluded}


def symmetric_diff(a: dict[K, V], b: dict[K, V]) -> dict[K, V]:
    a_keys = set(a.keys())
    b_keys = set(b.keys())
    out: dict[K, V] = {}
    for k in a_keys - b_keys:
        out[k] = a[k]
    for k in b_keys - a_keys:
        out[k] = b[k]
    return out


def pick(m: dict[K, V], *keys: K) -> dict[K, V]:
    return {k: m[k] for k in keys if k in m}


def omit(m: dict[K, V], *keys: K) -> dict[K, V]:
    excluded = set(keys)
    return {k: v for k, v in m.items() if k not in excluded}


def clear(m: dict[K, V]) -> None:
    m.clear()


def update(dst: dict[K, V], src: dict[K, V]) -> dict[K, V]:
    dst.update(src)
    return dst


def clone(m: dict[K, V]) -> dict[K, V]:
    return dict(m)


def equal(a: dict[K, V], b: dict[K, V]) -> bool:
    return a == b


def equal_by(a: dict[K, V1], b: dict[K, V2], eq: Callable[[V1, V2], bool]) -> bool:
    if len(a) != len(b):
        return False
    for k, v1 in a.items():
        if k not in b:
            return False
        if not eq(v1, b[k]):
            return False
    return True
