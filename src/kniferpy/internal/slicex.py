"""Collection (slice) helpers.

Ports knifer-go's internal/slice with Python-idiomatic mappings:

- Go generics [T any] -> Python duck typing
- Go iter.Seq[T] -> Python generators
- Go (T, bool) -> T | None

Errors use kniferpy.verr types with codes knifer.slice.<reason>.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

from kniferpy.verr import KniferError

T = TypeVar("T")
R = TypeVar("R")
K = TypeVar("K")
V = TypeVar("V")
A = TypeVar("A")
B = TypeVar("B")


def is_empty(a: list[T]) -> bool:
    return len(a) == 0


def is_not_empty(a: list[T]) -> bool:
    return len(a) > 0


def contains(a: list[T], v: T) -> bool:
    return v in a


def index_of(a: list[T], v: T) -> int:
    try:
        return a.index(v)
    except ValueError:
        return -1


def last_index_of(a: list[T], v: T) -> int:
    for i in range(len(a) - 1, -1, -1):
        if a[i] == v:
            return i
    return -1


def reverse(a: list[T]) -> list[T]:
    return list(reversed(a))


def distinct(a: list[T]) -> list[T]:
    return list(dict.fromkeys(a))


def uniq(a: list[T]) -> list[T]:
    return distinct(a)


def uniq_by(a: list[T], key_fn: Callable[[T], K]) -> list[T]:
    seen: set[K] = set()
    out: list[T] = []
    for item in a:
        k = key_fn(item)
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


def join(a: list[T], sep: str = "") -> str:
    return sep.join(str(item) for item in a)


def filter_values(a: list[T], pred: Callable[[T], bool]) -> list[T]:
    return [item for item in a if pred(item)]


def reject(a: list[T], pred: Callable[[T], bool]) -> list[T]:
    return [item for item in a if not pred(item)]


def filter_map(a: list[T], fn: Callable[[T], tuple[R, bool]]) -> list[R]:
    out: list[R] = []
    for item in a:
        result, ok = fn(item)
        if ok:
            out.append(result)
    return out


def map_values(a: list[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(item) for item in a]


def map_err(a: list[T], fn: Callable[[T], tuple[R, None] | tuple[None, Exception]]) -> list[R]:
    out: list[R] = []
    for item in a:
        result, err = fn(item)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.slice.map_err")
        out.append(result)  # type: ignore[arg-type]
    return out


def flat_map(a: list[T], fn: Callable[[T], list[R]]) -> list[R]:
    out: list[R] = []
    for item in a:
        out.extend(fn(item))
    return out


def reduce(a: list[T], initial: R, fn: Callable[[R, T], R]) -> R:
    acc = initial
    for item in a:
        acc = fn(acc, item)
    return acc


def filter_err(
    a: list[T], pred: Callable[[T], tuple[bool, None] | tuple[None, Exception]]
) -> list[T]:
    out: list[T] = []
    for item in a:
        ok, err = pred(item)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.slice.filter_err")
        if ok:
            out.append(item)
    return out


def reduce_err(
    a: list[T], initial: R, fn: Callable[[R, T], tuple[R, None] | tuple[None, Exception]]
) -> R:
    acc = initial
    for item in a:
        result, err = fn(acc, item)
        if err is not None:
            raise KniferError(message=str(err), code="knifer.slice.reduce_err")
        acc = result  # type: ignore[assignment]
    return acc


def for_each(a: list[T], fn: Callable[[T], None]) -> None:
    for item in a:
        fn(item)


def find(a: list[T], pred: Callable[[T], bool]) -> T | None:
    for item in a:
        if pred(item):
            return item
    return None


def find_index(a: list[T], pred: Callable[[T], bool]) -> int:
    for i, item in enumerate(a):
        if pred(item):
            return i
    return -1


def iter_items(a: list[T]) -> Iterable[T]:
    yield from a


def iter_indexed(a: list[T]) -> Iterable[tuple[int, T]]:
    yield from enumerate(a)


def group_by(a: list[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    out: dict[K, list[T]] = {}
    for item in a:
        k = key_fn(item)
        out.setdefault(k, []).append(item)
    return out


def count_by(a: list[T], key_fn: Callable[[T], K]) -> dict[K, int]:
    out: dict[K, int] = {}
    for item in a:
        k = key_fn(item)
        out[k] = out.get(k, 0) + 1
    return out


def key_by(a: list[T], key_fn: Callable[[T], K]) -> dict[K, T]:
    out: dict[K, T] = {}
    for item in a:
        out[key_fn(item)] = item
    return out


def associate(a: list[T], transform: Callable[[T], tuple[K, V]]) -> dict[K, V]:
    out: dict[K, V] = {}
    for item in a:
        k, v = transform(item)
        out[k] = v
    return out


def slice_to_map(a: list[T], transform: Callable[[T], tuple[K, V]]) -> dict[K, V]:
    return associate(a, transform)


def chunk(a: list[T], size: int) -> list[list[T]]:
    if size <= 0:
        return []
    return [a[i : i + size] for i in range(0, len(a), size)]


def window(a: list[T], size: int) -> list[list[T]]:
    if size <= 0 or size > len(a):
        return []
    return [a[i : i + size] for i in range(len(a) - size + 1)]


def sliding(a: list[T], size: int, step: int) -> list[list[T]]:
    if size <= 0 or step <= 0:
        return []
    out: list[list[T]] = []
    for i in range(0, len(a) - size + 1, step):
        out.append(a[i : i + size])
    return out


def zip2(a: list[A], b: list[B]) -> list[tuple[A, B]]:
    return list(zip(a, b))


def unzip2(pairs: list[tuple[A, B]]) -> tuple[list[A], list[B]]:
    if not pairs:
        return [], []
    a_list: list[A] = []
    b_list: list[B] = []
    for x, y in pairs:
        a_list.append(x)
        b_list.append(y)
    return a_list, b_list


def flatten(a: list[list[T]]) -> list[T]:
    out: list[T] = []
    for sub in a:
        out.extend(sub)
    return out


def compact(a: list[T]) -> list[T]:
    return [item for item in a if item is not None]


def partition_by(a: list[T], key_fn: Callable[[T], K]) -> list[list[T]]:
    if not a:
        return []
    partitions: list[list[T]] = []
    current: list[T] = [a[0]]
    current_key = key_fn(a[0])
    for item in a[1:]:
        k = key_fn(item)
        if k == current_key:
            current.append(item)
        else:
            partitions.append(current)
            current = [item]
            current_key = k
    partitions.append(current)
    return partitions


def sub(a: list[T], from_index: int, to_index: int) -> list[T]:
    return a[from_index:to_index]


def concat(*slices: list[T]) -> list[T]:
    out: list[T] = []
    for s in slices:
        out.extend(s)
    return out


def union(a: list[T], b: list[T]) -> list[T]:
    return distinct(a + b)


def intersection(a: list[T], b: list[T]) -> list[T]:
    b_set = set(b)
    return [item for item in a if item in b_set]


def subtract(a: list[T], b: list[T]) -> list[T]:
    b_set = set(b)
    return [item for item in a if item not in b_set]


def page(a: list[T], page_no: int, page_size: int) -> list[T]:
    if page_no < 1 or page_size < 1:
        return []
    start = (page_no - 1) * page_size
    return a[start : start + page_size]
