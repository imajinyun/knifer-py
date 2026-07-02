from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from kniferpy.internal import cachex
from kniferpy.internal.cachex import (
    FIFOCache,
    LFUCache,
    Listener,
    LRUCache,
    NoCache,
    Supplier,
)

K = TypeVar("K")
V = TypeVar("V")

__all__ = [
    "FIFOCache",
    "LFUCache",
    "LRUCache",
    "Listener",
    "NoCache",
    "Supplier",
    "new_fifo",
    "new_lfu",
    "new_lru",
    "new_no_cache",
]


def new_fifo(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> FIFOCache[K, V]:
    return cachex.new_fifo(capacity, timeout=timeout, listener=listener, clock=clock)


def new_lru(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> LRUCache[K, V]:
    return cachex.new_lru(capacity, timeout=timeout, listener=listener, clock=clock)


def new_lfu(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> LFUCache[K, V]:
    return cachex.new_lfu(capacity, timeout=timeout, listener=listener, clock=clock)


def new_no_cache() -> NoCache[K, V]:
    return cachex.new_no_cache()
