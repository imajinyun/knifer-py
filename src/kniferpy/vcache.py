from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from kniferpy.internal import cachex
from kniferpy.internal.cachex import (
    CacheListener,
    CacheListenerFunc,
    FIFOCache,
    LFUCache,
    Listener,
    LRUCache,
    NoCache,
    Supplier,
    SupplierE,
    TickerFactory,
    TimedCache,
    WeakCache,
)

K = TypeVar("K")
V = TypeVar("V")

__all__ = [
    # Types
    "Cache",
    "CacheListener",
    "CacheListenerFunc",
    "CacheObj",
    "FIFOCache",
    "LFUCache",
    "LRUCache",
    "Listener",
    "NoCache",
    "Option",
    "Supplier",
    "SupplierE",
    "TickerFactory",
    "TimedCache",
    "WeakCache",
    # Option builders
    "with_capacity",
    "with_timeout",
    "with_listener",
    "with_clock",
    "with_ticker_factory",
    "with_runner",
    # Constructors
    "new_fifo",
    "new_fifo_with_options",
    "new_fifo_with_timeout",
    "new_lfu",
    "new_lfu_with_options",
    "new_lfu_with_timeout",
    "new_lru",
    "new_lru_with_options",
    "new_lru_with_timeout",
    "new_no",
    "new_no_cache",
    "new_timed",
    "new_timed_scheduled",
    "new_timed_scheduled_with_options",
    "new_timed_with_options",
    "new_weak",
    "new_weak_with_options",
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


def new_timed_scheduled(
    timeout: float,
    schedule_prune_delay: float,
    *,
    listener: Callable[[K, V], None] | None = None,
    clock: Callable[[], float] | None = None,
    ticker_factory: TickerFactory | None = None,
    runner: Callable[[Callable[[], None]], None] | None = None,
) -> TimedCache[K, V]:
    return cachex.new_timed_scheduled(
        timeout,
        schedule_prune_delay,
        listener=listener,
        clock=clock,
        ticker_factory=ticker_factory,
        runner=runner,
    )


def new_no() -> NoCache[K, V]:
    return cachex.new_no()


# Re-export types
Cache = cachex.Cache
CacheObj = cachex.CacheObj
Option = cachex.Option
CacheListener = cachex.CacheListener
CacheListenerFunc = cachex.CacheListenerFunc

# Option builders
with_capacity = cachex.with_capacity
with_timeout = cachex.with_timeout
with_listener = cachex.with_listener
with_clock = cachex.with_clock
with_ticker_factory = cachex.with_ticker_factory
with_runner = cachex.with_runner

# Constructor variants
new_fifo_with_options = cachex.new_fifo_with_options
new_fifo_with_timeout = cachex.new_fifo_with_timeout
new_lru_with_options = cachex.new_lru_with_options
new_lru_with_timeout = cachex.new_lru_with_timeout
new_lfu_with_options = cachex.new_lfu_with_options
new_lfu_with_timeout = cachex.new_lfu_with_timeout
new_timed_with_options = cachex.new_timed_with_options
new_weak_with_options = cachex.new_weak_with_options
new_timed_scheduled_with_options = cachex.new_timed_scheduled_with_options