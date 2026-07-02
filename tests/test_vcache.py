from __future__ import annotations

from kniferpy import vcache


class _Clock:
    """A manually advanced monotonic clock for deterministic TTL tests."""

    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_put_and_get() -> None:
    c: vcache.LRUCache[str, int] = vcache.new_lru(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("missing") is None
    assert c.get("missing", default=-1) == -1
    assert c.size() == 1
    assert c.is_empty() is False


def test_hit_miss_counts() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(4)
    c.put("a", 1)
    c.get("a")
    c.get("a")
    c.get("b")
    assert c.hit_count() == 2
    assert c.miss_count() == 1


def test_capacity_and_is_full() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.is_full() is True
    assert c.capacity() == 2


def test_fifo_eviction() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a" (first in)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_lru_eviction_by_access() -> None:
    c: vcache.LRUCache[str, int] = vcache.new_lru(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # "a" becomes most recently used
    c.put("c", 3)  # evicts "b" (least recently used)
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_lfu_eviction_by_frequency() -> None:
    c: vcache.LFUCache[str, int] = vcache.new_lfu(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.get("a")
    c.get("b")
    c.put("c", 3)  # "b" has the lowest frequency and is evicted
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_ttl_expiration() -> None:
    clock = _Clock()
    c: vcache.LRUCache[str, int] = vcache.new_lru(4, timeout=10.0, clock=clock)
    c.put("a", 1)
    assert c.get("a") == 1
    clock.advance(11.0)
    assert c.get("a") is None
    assert c.size() == 0


def test_put_with_custom_timeout() -> None:
    clock = _Clock()
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(4, clock=clock)
    c.put_with_timeout("a", 1, 5.0)
    clock.advance(3.0)
    # A non-refreshing read keeps the original last-access baseline.
    assert c.get_with_update("a", False) == 1
    clock.advance(3.0)  # total 6s since insert, TTL 5s -> expired
    assert c.get("a") is None


def test_contains_key_prunes_expired() -> None:
    clock = _Clock()
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(4, timeout=5.0, clock=clock)
    c.put("a", 1)
    assert c.contains_key("a") is True
    clock.advance(6.0)
    assert c.contains_key("a") is False
    assert c.size() == 0


def test_get_or_load() -> None:
    c: vcache.LRUCache[str, int] = vcache.new_lru(4)
    calls: list[str] = []

    def supplier() -> int:
        calls.append("x")
        return 42

    assert c.get_or_load("x", supplier) == 42
    assert c.get_or_load("x", supplier) == 42  # cached, supplier not called again
    assert calls == ["x"]


def test_get_or_load_none_supplier() -> None:
    c: vcache.LRUCache[str, int] = vcache.new_lru(4)
    assert c.get_or_load("missing", None) is None


def test_remove_and_clear() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(4)
    c.put("a", 1)
    c.put("b", 2)
    c.remove("a")
    assert c.get("a") is None
    assert c.size() == 1
    c.clear()
    assert c.is_empty() is True


def test_keys_and_values_order() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(4)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.keys() == ["a", "b", "c"]
    assert c.values() == [1, 2, 3]


def test_removal_listener() -> None:
    removed: list[tuple[str, int]] = []
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(
        2, listener=lambda k, v: removed.append((k, v))
    )
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a"
    assert ("a", 1) in removed


def test_set_listener_chaining() -> None:
    removed: list[str] = []
    c: vcache.LRUCache[str, int] = vcache.new_lru(4)
    assert c.set_listener(lambda k, v: removed.append(k)) is c
    c.put("a", 1)
    c.remove("a")
    assert removed == ["a"]


def test_replace_does_not_evict() -> None:
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # replacing must not evict "b"
    assert c.get("a") == 10
    assert c.get("b") == 2


def test_prune_returns_count() -> None:
    clock = _Clock()
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(10, timeout=5.0, clock=clock)
    c.put("a", 1)
    c.put("b", 2)
    clock.advance(6.0)
    assert c.prune() == 2
    assert c.size() == 0


def test_no_cache() -> None:
    c: vcache.NoCache[str, int] = vcache.new_no_cache()
    c.put("a", 1)
    assert c.get("a") is None
    assert c.size() == 0
    assert c.is_empty() is True
