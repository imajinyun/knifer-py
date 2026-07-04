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
    TickerFactory,
    TimedCache,
    WeakCache,
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
    "TickerFactory",
    "TimedCache",
    "WeakCache",
    "new_fifo",
    "new_lfu",
    "new_lru",
    "new_no_cache",
    "new_timed",
    "new_weak",
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


def new_timed(
    timeout: float,
    *,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
    ticker_factory: TickerFactory | None = None,
    runner: Callable[[Callable[[], None]], None] | None = None,
) -> TimedCache[K, V]:
    return cachex.new_timed(
        timeout,
        listener=listener,
        clock=clock,
        ticker_factory=ticker_factory,
        runner=runner,
    )


def new_weak(
    timeout: float,
    *,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> WeakCache[K, V]:
    return cachex.new_weak(timeout, listener=listener, clock=clock)