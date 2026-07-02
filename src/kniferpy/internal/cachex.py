from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar

from kniferpy.verr import ValidationError

K = TypeVar("K")
V = TypeVar("V")

# A removal listener receives (key, value) when an entry leaves the cache.
Listener = Callable[[K, V], None]
# A supplier produces a value on a GetOrLoad miss.
Supplier = Callable[[], V]


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
