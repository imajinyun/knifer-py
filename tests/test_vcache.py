from __future__ import annotations

import pytest

from kniferpy import vcache
from kniferpy.internal import cachex
from kniferpy.verr import ValidationError


class _Clock:
    """A manually advanced monotonic clock for deterministic TTL tests."""

    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class _Box:
    def __init__(self, value: int) -> None:
        self.value = value


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
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(2, listener=lambda k, v: removed.append((k, v)))
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


def test_negative_capacity_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vcache.new_fifo(-1)
    assert exc_info.value.code == "cache.invalid_capacity"


def test_cache_obj_expired_time() -> None:
    assert vcache.CacheObj("a", 1, 0.0, 10.0, 0).expired_time() is None
    assert vcache.CacheObj("a", 1, 5.0, 10.0, 0).expired_time() == 15.0


def test_get_or_load_e_success_error_and_cached_paths() -> None:
    c: vcache.LRUCache[str, int] = vcache.new_lru(4)
    err = RuntimeError("boom")
    calls: list[str] = []

    def supplier() -> tuple[int, Exception | None]:
        calls.append("supplier")
        return 7, None

    def failing() -> tuple[int, Exception | None]:
        return 0, err

    assert c.get_or_load_e("missing", None) == (None, None)
    assert c.get_or_load_e("bad", failing) == (None, err)
    assert c.get_or_load_e("a", supplier) == (7, None)
    assert c.get_or_load_e("a", supplier) == (7, None)
    assert calls == ["supplier"]


def test_get_or_load_with_custom_timeout_and_load_lock_cleanup() -> None:
    clock = _Clock()
    c: cachex.LRUCache[str, int] = vcache.new_lru(4, clock=clock)

    assert c.get_or_load_with("a", lambda: 1, True, 5.0) == 1
    assert c.get_or_load_with("a", lambda: 2, True, 5.0) == 1
    assert c._key_locks == {}
    clock.advance(6.0)
    assert c.get("a") is None


def test_listener_can_be_cache_listener_func_and_reentrant() -> None:
    removed: list[tuple[str, int]] = []
    c: vcache.FIFOCache[str, int] = vcache.new_fifo(2)
    listener = vcache.CacheListenerFunc(lambda key, value: removed.append((key, value)))

    vcache.with_listener(listener)(c)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    c.remove("b")

    assert removed == [("a", 1), ("b", 2)]


def test_option_constructors_build_fifo_lru_lfu_and_timeout_variants() -> None:
    clock = _Clock()
    removed: list[tuple[str, int]] = []
    listener = vcache.CacheListenerFunc(lambda key, value: removed.append((key, value)))

    fifo: cachex.FIFOCache[str, int] = cachex.FIFOCache(0, 0.0)
    for option in (
        vcache.with_capacity(2),
        vcache.with_timeout(5.0),
        vcache.with_clock(clock),
        vcache.with_listener(listener),
    ):
        option(fifo)
    lru: cachex.LRUCache[str, int] = cachex.LRUCache(0, 0.0)
    vcache.with_capacity(1)(lru)
    lfu: cachex.LFUCache[str, int] = cachex.LFUCache(0, 0.0)
    vcache.with_capacity(1)(lfu)
    fifo_timeout = vcache.new_fifo_with_timeout(2, 3.0)
    lru_timeout = vcache.new_lru_with_timeout(2, 3.0)
    lfu_timeout = vcache.new_lfu_with_timeout(2, 3.0)

    fifo.put("a", 1)
    fifo.put("b", 2)
    fifo.put("c", 3)
    lru.put("a", 1)
    lru.put("b", 2)
    lfu.put("a", 1)
    lfu.put("b", 2)

    assert fifo.capacity() == 2
    assert fifo.timeout() == 5.0
    assert removed == [("a", 1)]
    assert lru.get("a") is None
    assert lfu.get("a") is None
    assert fifo_timeout.timeout() == 3.0
    assert lru_timeout.timeout() == 3.0
    assert lfu_timeout.timeout() == 3.0
    with pytest.raises(TypeError):
        vcache.new_fifo_with_options([])
    with pytest.raises(TypeError):
        vcache.new_lru_with_options([])
    with pytest.raises(TypeError):
        vcache.new_lfu_with_options([])


def test_timed_cache_core_behaviour_and_listener() -> None:
    clock = _Clock()
    removed: list[tuple[str, int]] = []
    c: vcache.TimedCache[str, int] = vcache.new_timed(
        5.0,
        listener=lambda key, value: removed.append((key, value)),
        clock=clock,
    )

    c.put("a", 1)
    c.put_with_timeout("b", 2, 10.0)
    assert c.get("a") == 1
    assert c.get("missing", default=-1) == -1
    assert c.contains_key("b")
    assert c.keys() == ["a", "b"]
    assert c.values() == [1, 2]
    assert c.hit_count() == 1
    assert c.miss_count() == 1
    clock.advance(6.0)
    assert c.get("a") is None
    assert c.contains_key("b")
    assert removed == [("a", 1)]
    assert c.prune() == 0
    c.put("b", 20)
    assert ("b", 2) in removed
    c.remove("b")
    assert ("b", 20) in removed
    c.put("c", 3)
    assert c.set_listener(None) is c
    c.clear()
    assert c.is_empty()


def test_timed_cache_get_or_load_e_and_options() -> None:
    clock = _Clock()
    err = RuntimeError("load failed")
    timed = vcache.new_timed_with_options(
        [
            vcache.with_timeout(5.0),
            vcache.with_clock(clock),
        ]
    )

    assert timed.get_or_load("a", None) is None
    assert timed.get_or_load("a", lambda: 1) == 1
    assert timed.get_or_load("a", lambda: 2) == 1
    assert timed.get_or_load_e("bad", lambda: (0, err)) == (None, err)
    assert timed.get_or_load_e("b", lambda: (2, None)) == (2, None)
    assert timed.get_or_load_e("b", lambda: (3, None)) == (2, None)
    clock.advance(6.0)
    assert timed.get("a") is None


def test_timed_scheduled_uses_runner_and_can_cancel() -> None:
    clock = _Clock()
    runner_calls: list[str] = []
    stop_calls: list[str] = []

    def ticker_factory(delay: float):
        return object(), lambda: stop_calls.append(f"stop:{delay}")

    def runner(fn):
        runner_calls.append("run")

    c = vcache.new_timed(5.0, clock=clock, ticker_factory=ticker_factory, runner=runner)
    c.schedule_prune(0)
    c.schedule_prune(1.0)
    c.schedule_prune(1.0)
    c.cancel_prune_schedule()
    c.cancel_prune_schedule()

    assert runner_calls == ["run"]
    assert stop_calls == []
    scheduled = vcache.new_timed_scheduled(
        5.0,
        0.0,
        clock=clock,
        ticker_factory=ticker_factory,
        runner=runner,
    )
    assert isinstance(scheduled, vcache.TimedCache)


def test_timed_schedule_prune_loop_prunes_once_with_fake_event() -> None:
    clock = _Clock()
    removed: list[tuple[str, int]] = []
    stop_calls: list[str] = []

    class FakeEvent:
        def __init__(self) -> None:
            self.calls = 0
            self.stopped = False

        def is_set(self) -> bool:
            return self.stopped

        def wait(self, delay: float) -> None:
            self.calls += 1
            if self.calls == 1:
                clock.advance(6.0)
            else:
                self.stopped = True

        def set(self) -> None:
            self.stopped = True

    fake_event = FakeEvent()
    original_event = cachex.threading.Event

    def ticker_factory(delay: float):
        return object(), lambda: stop_calls.append(f"stop:{delay}")

    def runner(fn):
        fn()

    try:
        cachex.threading.Event = lambda: fake_event  # type: ignore[assignment]
        c = vcache.new_timed(
            5.0,
            clock=clock,
            listener=lambda key, value: removed.append((key, value)),
            ticker_factory=ticker_factory,
            runner=runner,
        )
        c.put("a", 1)
        c.schedule_prune(1.0)
    finally:
        cachex.threading.Event = original_event

    assert removed == [("a", 1)]
    assert c.size() == 0
    assert stop_calls == ["stop:1.0"]


def test_weak_cache_core_ttl_and_listener_behaviour() -> None:
    clock = _Clock()
    removed: list[tuple[str, int]] = []
    cache: vcache.WeakCache[str, _Box] = vcache.new_weak(
        5.0,
        clock=clock,
        listener=lambda key, value: removed.append((key, value.value)),
    )
    first = _Box(1)
    second = _Box(2)

    cache.put("a", first)
    assert cache.get("a") is first
    assert cache.contains_key("a")
    assert cache.keys() == ["a"]
    assert cache.hit_count() == 1
    assert cache.miss_count() == 0
    cache.put("a", second)
    assert removed == [("a", 1)]
    clock.advance(6.0)
    assert cache.get("a") is None
    assert ("a", 2) in removed
    assert not cache.contains_key("a")
    assert cache.miss_count() >= 1
    cache.set_listener(None)
    cache.put("b", _Box(3))
    cache.remove("b")
    cache.put("c", _Box(4))
    cache.clear()
    assert cache.is_empty()


def test_weak_cache_get_or_load_and_error_paths() -> None:
    err = RuntimeError("load failed")
    cache: vcache.WeakCache[str, _Box] = vcache.new_weak(0)
    loaded = _Box(1)

    assert cache.get("missing", default=loaded) is loaded
    assert cache.get_or_load("none", None) is None
    assert cache.get_or_load("a", lambda: loaded) is loaded
    assert cache.get_or_load("a", lambda: _Box(2)) is loaded
    assert cache.get_or_load_e("bad", lambda: (_Box(0), err)) == (None, err)
    next_box = _Box(3)
    assert cache.get_or_load_e("b", lambda: (next_box, None)) == (next_box, None)
    assert cache.get_or_load_e("b", lambda: (_Box(4), None)) == (next_box, None)


def test_weak_cache_options_and_aliases() -> None:
    clock = _Clock()
    weak = vcache.new_weak_with_options([vcache.with_timeout(5.0), vcache.with_clock(clock)])
    no_cache = vcache.new_no()
    box = _Box(1)

    assert weak._timeout == 5.0
    weak.put("a", box)
    clock.advance(6.0)
    assert weak.prune() == 1
    assert isinstance(no_cache, vcache.NoCache)


def test_default_ticker_factory_and_runner_smoke() -> None:
    calls: list[str] = []
    ticker = cachex._Ticker(60.0, lambda: calls.append("tick"))
    ticker.stop()
    created, stop = cachex._default_ticker_factory(60.0)
    stop()
    assert isinstance(created, cachex._Ticker)

    event = cachex.threading.Event()

    def mark() -> None:
        event.set()

    cachex._default_runner(mark)
    assert event.wait(1.0)
