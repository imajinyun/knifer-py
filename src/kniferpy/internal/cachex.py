from __future__ import annotations

import threading
import time
import weakref
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from kniferpy.verr import ValidationError

K = TypeVar("K")
V = TypeVar("V")

# A removal listener receives (key, value) when an entry leaves the cache.
Listener = Callable[[K, V], None]
# A supplier produces a value on a GetOrLoad miss.
Supplier = Callable[[], V]
# A supplier that may fail.
SupplierE = Callable[[], tuple[V, Exception | None]]
# A ticker factory creates a ticker channel and stopper for scheduled pruning.
TickerFactory = Callable[[float], tuple["_Ticker", Callable[[], None]]]


class Cache(Protocol[K, V]):
    """Protocol for any cache type (FIFO, LRU, LFU, Timed, Weak, No)."""

    def capacity(self) -> int: ...
    def timeout(self) -> float: ...
    def put(self, key: K, value: V) -> None: ...
    def put_with_timeout(self, key: K, value: V, timeout: float) -> None: ...
    def get(self, key: K, default: V | None = None) -> V | None: ...
    def get_with_update(self, key: K, update_last_access: bool, default: V | None = None) -> V | None: ...
    def get_or_load(self, key: K, supplier: Supplier[V] | None) -> V | None: ...
    def get_or_load_with(self, key: K, supplier: Supplier[V] | None, update_last_access: bool, timeout: float) -> V | None: ...
    def remove(self, key: K) -> None: ...
    def contains_key(self, key: K) -> bool: ...
    def size(self) -> int: ...
    def is_empty(self) -> bool: ...
    def is_full(self) -> bool: ...
    def prune(self) -> int: ...
    def clear(self) -> None: ...
    def keys(self) -> list[K]: ...
    def values(self) -> list[V]: ...
    def set_listener(self, listener: Listener[K, V] | None) -> "Cache[K, V]": ...
    def hit_count(self) -> int: ...
    def miss_count(self) -> int: ...


class _CacheObj(Generic[K, V]):
    """One cached entry with its access metadata. TTL is in seconds; 0 = never."""

    __slots__ = ("access_count", "key", "last_access", "ttl", "value")

    def __init__(self, key: K, value: V, ttl: float, now: float) -> None:
        self.key = key
        self.value = value
        self.ttl = ttl
        self.last_access = now
        self.access_count = 0

    def is_expired(self, now: float) -> bool:
        if self.ttl <= 0:
            return False
        return now - self.last_access > self.ttl

    def touch(self, update_last_access: bool, now: float) -> V:
        if update_last_access:
            self.last_access = now
        self.access_count += 1
        return self.value

    def expired_time(self) -> float | None:
        if self.ttl <= 0:
            return None
        return self.last_access + self.ttl


class _LoadLock:
    __slots__ = ("lock", "refs")

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.refs = 0


class _AbstractCache(Generic[K, V]):
    """Shared cache implementation for the FIFO/LRU/LFU strategies.

    A single re-entrant lock guards the ordered map and metadata. Reads take
    the lock too, because a hit may refresh last-access time, bump the entry's
    access count, and (for LRU) move the node to the tail.
    """

    _move_to_back_on_get = False

    def __init__(
        self,
        capacity: int,
        timeout: float,
        *,
        listener: Listener[K, V] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if capacity < 0:
            raise ValidationError(
                f"vcache: capacity must be >= 0: {capacity}", code="cache.invalid_capacity"
            )
        self._capacity = capacity
        self._timeout = timeout if timeout and timeout > 0 else 0.0
        self._map: OrderedDict[K, _CacheObj[K, V]] = OrderedDict()
        self._mu = threading.RLock()
        self._listener = listener
        self._clock = clock if clock is not None else time.monotonic
        self._hit_count = 0
        self._miss_count = 0
        self._exist_custom_timeout = False
        self._key_locks: dict[K, _LoadLock] = {}
        self._guard = threading.Lock()
        # Removal notifications collected under the lock and delivered after
        # unlocking, so listeners may safely re-enter the same cache.
        self._pending: list[tuple[K, V]] = []

    # ----- prune strategy (overridden by subclasses) ------------------------

    def _prune_locked(self) -> int:
        raise NotImplementedError

    # ----- introspection ----------------------------------------------------

    def capacity(self) -> int:
        return self._capacity

    def timeout(self) -> float:
        return self._timeout

    def hit_count(self) -> int:
        with self._mu:
            return self._hit_count

    def miss_count(self) -> int:
        with self._mu:
            return self._miss_count

    def size(self) -> int:
        with self._mu:
            return len(self._map)

    def is_empty(self) -> bool:
        with self._mu:
            return len(self._map) == 0

    def is_full(self) -> bool:
        with self._mu:
            return self._is_full_locked()

    def _is_full_locked(self) -> bool:
        return self._capacity > 0 and len(self._map) >= self._capacity

    def _prune_expired_active(self) -> bool:
        return self._timeout > 0 or self._exist_custom_timeout

    def _now(self) -> float:
        return self._clock()

    # ----- writes -----------------------------------------------------------

    def put(self, key: K, value: V) -> None:
        self.put_with_timeout(key, value, self._timeout)

    def put_with_timeout(self, key: K, value: V, timeout: float) -> None:
        with self._mu:
            self._put_locked(key, value, timeout)
            events = self._drain_events_locked()
        self._notify(events)

    def _put_locked(self, key: K, value: V, timeout: float) -> None:
        ttl = timeout if timeout and timeout > 0 else 0.0
        obj = _CacheObj(key, value, ttl, self._now())
        if ttl > 0 and ttl != self._timeout:
            self._exist_custom_timeout = True
        old = self._map.get(key)
        if old is not None:
            # Replacing an existing entry keeps its order and does not evict.
            self._map[key] = obj
            self._collect(old.key, old.value)
            return
        if self._is_full_locked():
            self._prune_locked()
        self._map[key] = obj

    # ----- reads ------------------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        return self.get_with_update(key, True, default)

    def get_with_update(
        self, key: K, update_last_access: bool, default: V | None = None
    ) -> V | None:
        with self._mu:
            value, ok = self._get_locked(key, update_last_access)
            events = self._drain_events_locked()
        self._notify(events)
        return value if ok else default

    def _get_locked(self, key: K, update_last_access: bool) -> tuple[V | None, bool]:
        obj = self._map.get(key)
        if obj is None:
            self._miss_count += 1
            return None, False
        if obj.is_expired(self._now()):
            del self._map[key]
            self._collect(obj.key, obj.value)
            self._miss_count += 1
            return None, False
        value = obj.touch(update_last_access, self._now())
        self._hit_count += 1
        if self._move_to_back_on_get:
            self._map.move_to_end(key, last=True)
        return value, True

    def contains_key(self, key: K) -> bool:
        with self._mu:
            obj = self._map.get(key)
            if obj is None:
                return False
            if obj.is_expired(self._now()):
                del self._map[key]
                self._collect(obj.key, obj.value)
                events = self._drain_events_locked()
                notify = True
            else:
                events = []
                notify = False
        if notify:
            self._notify(events)
        return not notify

    def get_or_load(self, key: K, supplier: Supplier[V] | None) -> V | None:
        return self.get_or_load_with(key, supplier, True, self._timeout)

    def get_or_load_e(self, key: K, supplier: SupplierE[V] | None) -> tuple[V | None, Exception | None]:
        return self.get_or_load_with_e(key, supplier, True, self._timeout)

    def get_or_load_with(
        self,
        key: K,
        supplier: Supplier[V] | None,
        update_last_access: bool,
        timeout: float,
    ) -> V | None:
        value, ok = self._try_get(key, update_last_access)
        if ok:
            return value
        if supplier is None:
            return None
        # Serialize concurrent loads of the same key, then double-check.
        lock = self._acquire_load_lock(key)
        try:
            value, ok = self._try_get(key, update_last_access)
            if ok:
                return value
            loaded = supplier()
            self.put_with_timeout(key, loaded, timeout)
            return loaded
        finally:
            self._release_load_lock(key, lock)

    def get_or_load_with_e(
        self,
        key: K,
        supplier: SupplierE[V] | None,
        update_last_access: bool,
        timeout: float,
    ) -> tuple[V | None, Exception | None]:
        value, ok = self._try_get(key, update_last_access)
        if ok:
            return value, None
        if supplier is None:
            return None, None
        lock = self._acquire_load_lock(key)
        try:
            value, ok = self._try_get(key, update_last_access)
            if ok:
                return value, None
            loaded, err = supplier()
            if err is not None:
                return None, err
            self.put_with_timeout(key, loaded, timeout)
            return loaded, None
        finally:
            self._release_load_lock(key, lock)

    def _try_get(self, key: K, update_last_access: bool) -> tuple[V | None, bool]:
        with self._mu:
            value, ok = self._get_locked(key, update_last_access)
            events = self._drain_events_locked()
        self._notify(events)
        return value, ok

    def _acquire_load_lock(self, key: K) -> _LoadLock:
        with self._guard:
            entry = self._key_locks.get(key)
            if entry is None:
                entry = _LoadLock()
                self._key_locks[key] = entry
            entry.refs += 1
        entry.lock.acquire()
        return entry

    def _release_load_lock(self, key: K, entry: _LoadLock) -> None:
        entry.lock.release()
        with self._guard:
            entry.refs -= 1
            if entry.refs == 0 and self._key_locks.get(key) is entry:
                del self._key_locks[key]

    # ----- removal / maintenance --------------------------------------------

    def remove(self, key: K) -> None:
        with self._mu:
            old = self._map.pop(key, None)
            if old is not None:
                self._collect(old.key, old.value)
            events = self._drain_events_locked()
        self._notify(events)

    def clear(self) -> None:
        with self._mu:
            for obj in self._map.values():
                self._collect(obj.key, obj.value)
            self._map.clear()
            events = self._drain_events_locked()
        self._notify(events)

    def prune(self) -> int:
        with self._mu:
            count = self._prune_locked()
            events = self._drain_events_locked()
        self._notify(events)
        return count

    def keys(self) -> list[K]:
        with self._mu:
            return list(self._map.keys())

    def values(self) -> list[V]:
        with self._mu:
            now = self._now()
            return [obj.value for obj in self._map.values() if not obj.is_expired(now)]

    def set_listener(self, listener: Listener[K, V] | None) -> _AbstractCache[K, V]:
        with self._mu:
            self._listener = listener
        return self

    # ----- listener event buffering -----------------------------------------

    def _collect(self, key: K, value: V) -> None:
        if self._listener is not None:
            self._pending.append((key, value))

    def _drain_events_locked(self) -> list[tuple[K, V]]:
        if not self._pending or self._listener is None:
            self._pending = []
            return []
        events = self._pending
        self._pending = []
        return events

    def _notify(self, events: list[tuple[K, V]]) -> None:
        listener = self._listener
        if listener is None:
            return
        for key, value in events:
            listener(key, value)

    def _remove_without_notify_locked(self, key: K) -> None:
        old = self._map.pop(key, None)
        if old is not None:
            self._collect(old.key, old.value)


class FIFOCache(_AbstractCache[K, V]):
    """Evicts entries in first-in-first-out order."""

    def _prune_locked(self) -> int:
        count = 0
        first: _CacheObj[K, V] | None = None
        if self._prune_expired_active():
            now = self._now()
            for key in list(self._map.keys()):
                obj = self._map.get(key)
                if obj is None:
                    continue
                if obj.is_expired(now):
                    self._remove_without_notify_locked(key)
                    count += 1
                    continue
                if first is None:
                    first = obj
        elif self._map:
            first = next(iter(self._map.values()))
        if self._is_full_locked() and first is not None:
            self._remove_without_notify_locked(first.key)
            count += 1
        return count


class LRUCache(_AbstractCache[K, V]):
    """Evicts the least recently used entry when capacity is exceeded."""

    _move_to_back_on_get = True

    def _prune_locked(self) -> int:
        count = 0
        if self._prune_expired_active():
            now = self._now()
            for key in list(self._map.keys()):
                obj = self._map.get(key)
                if obj is not None and obj.is_expired(now):
                    self._remove_without_notify_locked(key)
                    count += 1
        while self._capacity > 0 and len(self._map) >= self._capacity:
            try:
                first_key = next(iter(self._map))
            except StopIteration:
                break
            self._remove_without_notify_locked(first_key)
            count += 1
        return count


class LFUCache(_AbstractCache[K, V]):
    """Evicts entries with the lowest access frequency."""

    def _prune_locked(self) -> int:
        count = 0
        now = self._now()
        min_obj: _CacheObj[K, V] | None = None
        for key in list(self._map.keys()):
            obj = self._map.get(key)
            if obj is None:
                continue
            if obj.is_expired(now):
                self._remove_without_notify_locked(key)
                count += 1
                continue
            if min_obj is None or obj.access_count < min_obj.access_count:
                min_obj = obj
        if self._is_full_locked() and min_obj is not None:
            min_access = min_obj.access_count
            for key in list(self._map.keys()):
                obj = self._map.get(key)
                if obj is None:
                    continue
                obj.access_count -= min_access
                if obj.access_count <= 0:
                    self._remove_without_notify_locked(key)
                    count += 1
        return count


class NoCache(_AbstractCache[K, V]):
    """A cache that stores nothing; every lookup misses."""

    def __init__(self) -> None:
        super().__init__(0, 0.0)

    def _put_locked(self, key: K, value: V, timeout: float) -> None:
        return

    def _prune_locked(self) -> int:
        return 0


# ----- factory helpers ------------------------------------------------------


def _normalize_timeout(timeout: float | None) -> float:
    return timeout if timeout and timeout > 0 else 0.0


def new_fifo(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
) -> FIFOCache[K, V]:
    return FIFOCache(capacity, _normalize_timeout(timeout), listener=listener, clock=clock)


def new_lru(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
) -> LRUCache[K, V]:
    return LRUCache(capacity, _normalize_timeout(timeout), listener=listener, clock=clock)


def new_lfu(
    capacity: int,
    *,
    timeout: float | None = None,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
) -> LFUCache[K, V]:
    return LFUCache(capacity, _normalize_timeout(timeout), listener=listener, clock=clock)


def new_no_cache() -> NoCache[K, V]:
    return NoCache()


# ----- TimedCache (expiration-only, no capacity limit) -----------------------


class _Ticker:
    __slots__ = ("_timer", "_fn")

    def __init__(self, interval: float, fn: Callable[[], None]) -> None:
        self._fn = fn
        self._timer: threading.Timer | None = None
        self._start(interval)

    def _start(self, interval: float) -> None:
        self._timer = threading.Timer(interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        self._fn()

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None


def _default_ticker_factory(delay: float) -> tuple[_Ticker, Callable[[], None]]:
    t = _Ticker(delay, lambda: None)
    return t, t.stop


def _default_runner(fn: Callable[[], None]) -> None:
    t = threading.Thread(target=fn, daemon=True)
    t.start()


class TimedCache(Generic[K, V]):
    """An expiration-only cache with no capacity limit.

    Entries are removed only when they expire and are observed by a lookup,
    explicit prune call, or scheduled prune task.
    """

    __slots__ = (
        "_mu",
        "_entries",
        "_timeout",
        "_listener",
        "_hits",
        "_misses",
        "_clock",
        "_ticker_factory",
        "_runner",
        "_prune_mu",
        "_prune_stop",
        "_prune_wg",
        "_pending",
    )

    def __init__(
        self,
        timeout: float,
        *,
        listener: Listener[K, V] | None = None,
        clock: Callable[[], float] | None = None,
        ticker_factory: TickerFactory | None = None,
        runner: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._timeout = timeout if timeout and timeout > 0 else 0.0
        self._mu = threading.RLock()
        self._entries: dict[K, tuple[V, float, float]] = {}  # key -> (value, last_access, ttl)
        self._listener = listener
        self._hits = 0
        self._misses = 0
        self._clock = clock if clock is not None else time.monotonic
        self._ticker_factory = ticker_factory if ticker_factory is not None else _default_ticker_factory
        self._runner = runner if runner is not None else _default_runner
        self._prune_mu = threading.Lock()
        self._prune_stop: threading.Event | None = None
        self._pending: list[tuple[K, V]] = []

    def _now(self) -> float:
        return self._clock()

    def _collect(self, key: K, value: V) -> None:
        if self._listener is not None:
            self._pending.append((key, value))

    def _drain_events(self) -> list[tuple[K, V]]:
        if not self._pending or self._listener is None:
            self._pending = []
            return []
        events = self._pending
        self._pending = []
        return events

    def _notify(self, events: list[tuple[K, V]]) -> None:
        listener = self._listener
        if listener is None:
            return
        for key, value in events:
            listener(key, value)

    def put(self, key: K, value: V) -> None:
        self.put_with_timeout(key, value, self._timeout)

    def put_with_timeout(self, key: K, value: V, timeout: float) -> None:
        ttl = timeout if timeout and timeout > 0 else 0.0
        with self._mu:
            old = self._entries.get(key)
            if old is not None:
                self._collect(key, old[0])
            self._entries[key] = (value, self._now(), ttl)
            events = self._drain_events()
        self._notify(events)

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._mu:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return default
            now = self._now()
            _, last_access, ttl = entry
            if ttl > 0 and now - last_access > ttl:
                del self._entries[key]
                self._collect(key, entry[0])
                self._misses += 1
                events = self._drain_events()
                self._notify(events)
                return default
            self._entries[key] = (entry[0], now, ttl)
            self._hits += 1
            return entry[0]

    def contains_key(self, key: K) -> bool:
        with self._mu:
            entry = self._entries.get(key)
            if entry is None:
                return False
            now = self._now()
            _, last_access, ttl = entry
            if ttl > 0 and now - last_access > ttl:
                del self._entries[key]
                self._collect(key, entry[0])
                events = self._drain_events()
                self._notify(events)
                return False
            return True

    def remove(self, key: K) -> None:
        with self._mu:
            old = self._entries.pop(key, None)
            if old is not None:
                self._collect(key, old[0])
            events = self._drain_events()
        self._notify(events)

    def clear(self) -> None:
        with self._mu:
            for key, entry in self._entries.items():
                self._collect(key, entry[0])
            self._entries.clear()
            events = self._drain_events()
        self._notify(events)

    def prune(self) -> int:
        with self._mu:
            count = 0
            now = self._now()
            expired_keys: list[K] = []
            for key, entry in self._entries.items():
                _, last_access, ttl = entry
                if ttl > 0 and now - last_access > ttl:
                    expired_keys.append(key)
            for key in expired_keys:
                entry = self._entries.pop(key)
                self._collect(key, entry[0])
                count += 1
            events = self._drain_events()
        self._notify(events)
        return count

    def size(self) -> int:
        with self._mu:
            return len(self._entries)

    def is_empty(self) -> bool:
        with self._mu:
            return len(self._entries) == 0

    def hit_count(self) -> int:
        with self._mu:
            return self._hits

    def miss_count(self) -> int:
        with self._mu:
            return self._misses

    def keys(self) -> list[K]:
        with self._mu:
            return list(self._entries.keys())

    def values(self) -> list[V]:
        with self._mu:
            now = self._now()
            result: list[V] = []
            for entry in self._entries.values():
                v, last_access, ttl = entry
                if ttl <= 0 or now - last_access <= ttl:
                    result.append(v)
            return result

    def set_listener(self, listener: Listener[K, V] | None) -> TimedCache[K, V]:
        with self._mu:
            self._listener = listener
        return self

    def get_or_load(self, key: K, supplier: Supplier[V] | None) -> V | None:
        return self._get_or_load_with(key, supplier, self._timeout)

    def get_or_load_e(self, key: K, supplier: SupplierE[V] | None) -> tuple[V | None, Exception | None]:
        return self._get_or_load_with_e(key, supplier, self._timeout)

    def _get_or_load_with(self, key: K, supplier: Supplier[V] | None, timeout: float) -> V | None:
        value = self.get(key)
        if value is not None:
            return value
        if supplier is None:
            return None
        loaded = supplier()
        self.put_with_timeout(key, loaded, timeout)
        return loaded

    def _get_or_load_with_e(self, key: K, supplier: SupplierE[V] | None, timeout: float) -> tuple[V | None, Exception | None]:
        value = self.get(key)
        if value is not None:
            return value, None
        if supplier is None:
            return None, None
        loaded, err = supplier()
        if err is not None:
            return None, err
        self.put_with_timeout(key, loaded, timeout)
        return loaded, None

    def schedule_prune(self, delay: float) -> None:
        if delay <= 0:
            return
        with self._prune_mu:
            if self._prune_stop is not None:
                return
            self._prune_stop = threading.Event()

        def _prune_loop() -> None:
            stop = self._prune_stop
            if stop is None:
                return
            ticks, ticker_stop = self._ticker_factory(delay)
            try:
                while not stop.is_set():
                    stop.wait(delay)
                    if stop.is_set():
                        break
                    self.prune()
            finally:
                ticker_stop()

        self._runner(_prune_loop)

    def cancel_prune_schedule(self) -> None:
        with self._prune_mu:
            if self._prune_stop is None:
                return
            self._prune_stop.set()
            self._prune_stop = None


# ----- WeakCache (pointer-value timed cache with best-effort finalizer) ------


class WeakCache(Generic[K, V]):
    """A pointer-value cache with TTL and best-effort finalizer cleanup.

    Python's weakref provides similar semantics. Entries are removed when
    the referenced object is garbage-collected or when TTL expires.
    """

    __slots__ = ("_mu", "_entries", "_timeout", "_listener", "_hits", "_misses", "_clock", "_pending")

    def __init__(
        self,
        timeout: float,
        *,
        listener: Listener[K, V] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._timeout = timeout if timeout and timeout > 0 else 0.0
        self._mu = threading.Lock()
        self._entries: dict[K, tuple[weakref.ReferenceType[V], float, float]] = {}  # key -> (ref, last_access, ttl)
        self._listener = listener
        self._hits = 0
        self._misses = 0
        self._clock = clock if clock is not None else time.monotonic
        self._pending: list[tuple[K, V]] = []

    def _now(self) -> float:
        return self._clock()

    def _collect(self, key: K, value: V) -> None:
        if self._listener is not None:
            self._pending.append((key, value))

    def _drain_events(self) -> list[tuple[K, V]]:
        if not self._pending or self._listener is None:
            self._pending = []
            return []
        events = self._pending
        self._pending = []
        return events

    def _notify(self, events: list[tuple[K, V]]) -> None:
        listener = self._listener
        if listener is None:
            return
        for key, value in events:
            listener(key, value)

    def put(self, key: K, value: V) -> None:
        self.put_with_timeout(key, value, self._timeout)

    def put_with_timeout(self, key: K, value: V, timeout: float) -> None:
        ttl = timeout if timeout and timeout > 0 else 0.0
        ref = weakref.ref(value, lambda r, k=key: self._on_finalize(k, value))
        with self._mu:
            old = self._entries.get(key)
            if old is not None:
                old_val = old[0]()
                if old_val is not None:
                    self._collect(key, old_val)
            self._entries[key] = (ref, self._now(), ttl)
            events = self._drain_events()
        self._notify(events)

    def _on_finalize(self, key: K, value: V) -> None:
        with self._mu:
            entry = self._entries.get(key)
            if entry is not None:
                ref = entry[0]()
                if ref is None or ref is value:
                    del self._entries[key]
                    self._collect(key, value)
            events = self._drain_events()
        self._notify(events)

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._mu:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return default
            ref, last_access, ttl = entry
            value = ref()
            if value is None:
                del self._entries[key]
                self._misses += 1
                return default
            now = self._now()
            if ttl > 0 and now - last_access > ttl:
                del self._entries[key]
                self._collect(key, value)
                self._misses += 1
                events = self._drain_events()
                self._notify(events)
                return default
            self._entries[key] = (ref, now, ttl)
            self._hits += 1
            return value

    def contains_key(self, key: K) -> bool:
        with self._mu:
            entry = self._entries.get(key)
            if entry is None:
                return False
            ref, last_access, ttl = entry
            value = ref()
            if value is None:
                del self._entries[key]
                return False
            now = self._now()
            if ttl > 0 and now - last_access > ttl:
                del self._entries[key]
                self._collect(key, value)
                events = self._drain_events()
                self._notify(events)
                return False
            return True

    def remove(self, key: K) -> None:
        with self._mu:
            old = self._entries.pop(key, None)
            if old is not None:
                old_val = old[0]()
                if old_val is not None:
                    self._collect(key, old_val)
            events = self._drain_events()
        self._notify(events)

    def clear(self) -> None:
        with self._mu:
            for key, entry in self._entries.items():
                ref = entry[0]
                value = ref()
                if value is not None:
                    self._collect(key, value)
            self._entries.clear()
            events = self._drain_events()
        self._notify(events)

    def prune(self) -> int:
        with self._mu:
            count = 0
            now = self._now()
            expired_keys: list[K] = []
            for key, entry in self._entries.items():
                ref, last_access, ttl = entry
                value = ref()
                if value is None:
                    expired_keys.append(key)
                    continue
                if ttl > 0 and now - last_access > ttl:
                    expired_keys.append(key)
            for key in expired_keys:
                entry = self._entries.pop(key, None)
                if entry is not None:
                    value = entry[0]()
                    if value is not None:
                        self._collect(key, value)
                    count += 1
            events = self._drain_events()
        self._notify(events)
        return count

    def size(self) -> int:
        with self._mu:
            return len(self._entries)

    def is_empty(self) -> bool:
        with self._mu:
            return len(self._entries) == 0

    def hit_count(self) -> int:
        with self._mu:
            return self._hits

    def miss_count(self) -> int:
        with self._mu:
            return self._misses

    def keys(self) -> list[K]:
        with self._mu:
            return list(self._entries.keys())

    def set_listener(self, listener: Listener[K, V] | None) -> WeakCache[K, V]:
        with self._mu:
            self._listener = listener
        return self

    def get_or_load(self, key: K, supplier: Supplier[V] | None) -> V | None:
        return self._get_or_load_with(key, supplier, self._timeout)

    def get_or_load_e(self, key: K, supplier: SupplierE[V] | None) -> tuple[V | None, Exception | None]:
        return self._get_or_load_with_e(key, supplier, self._timeout)

    def _get_or_load_with(self, key: K, supplier: Supplier[V] | None, timeout: float) -> V | None:
        value = self.get(key)
        if value is not None:
            return value
        if supplier is None:
            return None
        loaded = supplier()
        self.put_with_timeout(key, loaded, timeout)
        return loaded

    def _get_or_load_with_e(self, key: K, supplier: SupplierE[V] | None, timeout: float) -> tuple[V | None, Exception | None]:
        value = self.get(key)
        if value is not None:
            return value, None
        if supplier is None:
            return None, None
        loaded, err = supplier()
        if err is not None:
            return None, err
        self.put_with_timeout(key, loaded, timeout)
        return loaded, None


# ----- factory helpers for timed/weak ----------------------------------------


def new_timed(
    timeout: float,
    *,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
    ticker_factory: TickerFactory | None = None,
    runner: Callable[[Callable[[], None]], None] | None = None,
) -> TimedCache[K, V]:
    return TimedCache(
        timeout,
        listener=listener,
        clock=clock,
        ticker_factory=ticker_factory,
        runner=runner,
    )


def new_weak(
    timeout: float,
    *,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
) -> WeakCache[K, V]:
    return WeakCache(timeout, listener=listener, clock=clock)


# ── CacheObj introspection type ──────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CacheObj(Generic[K, V]):
    """Introspection wrapper for a cache entry (Go CacheObj equivalent)."""

    key: K
    value: V
    ttl: float
    last_access: float
    access_count: int

    def expired_time(self) -> float | None:
        if self.ttl <= 0:
            return None
        return self.last_access + self.ttl


def new_timed_scheduled(
    timeout: float,
    schedule_prune_delay: float,
    *,
    listener: Listener[K, V] | None = None,
    clock: Callable[[], float] | None = None,
    ticker_factory: TickerFactory | None = None,
    runner: Callable[[Callable[[], None]], None] | None = None,
) -> TimedCache[K, V]:
    """Create a timed cache and start scheduled pruning."""
    c = new_timed(
        timeout,
        listener=listener,
        clock=clock,
        ticker_factory=ticker_factory,
        runner=runner,
    )
    c.schedule_prune(schedule_prune_delay)
    return c


def new_no() -> NoCache[K, V]:
    """Alias for new_no_cache (Go compat)."""
    return NoCache()


# ── Option builders (Go-style functional options) ────────────────────────────

Option = Callable[["_AbstractCache[K, V]"], None]  # type: ignore[misc]


class CacheListener(Protocol[K, V]):
    """Listener for cache eviction events (Go CacheListener equivalent)."""

    def on_remove(self, key: K, value: V) -> None: ...


class CacheListenerFunc(Generic[K, V]):
    """Adapt a plain function to CacheListener."""

    def __init__(self, fn: Callable[[K, V], None]) -> None:
        self._fn = fn

    def on_remove(self, key: K, value: V) -> None:
        self._fn(key, value)


def with_capacity(capacity: int) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c._capacity = capacity
    return _apply


def with_timeout(timeout: float) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c._timeout = timeout
    return _apply


def with_listener(listener: CacheListener[K, V]) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c.set_listener(listener.on_remove)
    return _apply


def with_clock(clock: Callable[[], float]) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c._clock = clock
    return _apply


def with_ticker_factory(factory: TickerFactory) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c._ticker_factory = factory  # type: ignore[attr-defined]
    return _apply


def with_runner(runner: Callable[[Callable[[], None]], None]) -> Option[K, V]:
    def _apply(c: _AbstractCache[K, V]) -> None:
        c._runner = runner  # type: ignore[attr-defined]
    return _apply


# ── Constructor variants with Options (Go style) ─────────────────────────────


def new_fifo_with_options(opts: list[Option[K, V]] | None = None) -> FIFOCache[K, V]:
    c = FIFOCache(0)
    for opt in (opts or []):
        opt(c)
    return c


def new_fifo_with_timeout(capacity: int, timeout: float) -> FIFOCache[K, V]:
    return new_fifo(capacity, timeout=timeout)


def new_lru_with_options(opts: list[Option[K, V]] | None = None) -> LRUCache[K, V]:
    c = LRUCache(0)
    for opt in (opts or []):
        opt(c)
    return c


def new_lru_with_timeout(capacity: int, timeout: float) -> LRUCache[K, V]:
    return new_lru(capacity, timeout=timeout)


def new_lfu_with_options(opts: list[Option[K, V]] | None = None) -> LFUCache[K, V]:
    c = LFUCache(0)
    for opt in (opts or []):
        opt(c)
    return c


def new_lfu_with_timeout(capacity: int, timeout: float) -> LFUCache[K, V]:
    return new_lfu(capacity, timeout=timeout)


def new_timed_with_options(opts: list[Option[K, V]] | None = None) -> TimedCache[K, V]:
    c = TimedCache(0.0)
    for opt in (opts or []):
        opt(c)  # type: ignore[arg-type]
    return c


def new_weak_with_options(opts: list[Option[K, V]] | None = None) -> WeakCache[K, V]:
    c = WeakCache(0.0)
    for opt in (opts or []):
        opt(c)  # type: ignore[arg-type]
    return c


def new_timed_scheduled_with_options(
    timeout: float,
    schedule_prune_delay: float,
    opts: list[Option[K, V]] | None = None,
) -> TimedCache[K, V]:
    c = new_timed_with_options(opts)
    c.set_timeout(timeout)  # type: ignore[attr-defined]
    c.schedule_prune(schedule_prune_delay)
    return c
