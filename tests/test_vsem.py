import threading
import time

import pytest

from kniferpy import vsem
from kniferpy.verr import ValidationError


def test_basic_acquire_release() -> None:
    s = vsem.new(2)
    assert s.acquire() is True
    assert s.use() == 1
    assert s.acquire() is True
    assert s.use() == 2
    s.release()
    assert s.use() == 1
    s.release()
    assert s.use() == 0


def test_cap() -> None:
    assert vsem.new(5).cap() == 5


def test_weighted_acquire() -> None:
    s = vsem.new(3)
    assert s.acquire(2) is True
    assert s.use() == 2
    assert s.try_acquire(2) is False
    assert s.try_acquire(1) is True
    assert s.use() == 3
    s.release(3)
    assert s.use() == 0


def test_try_acquire_no_block() -> None:
    s = vsem.new(1)
    assert s.try_acquire() is True
    assert s.try_acquire() is False
    s.release()
    assert s.try_acquire() is True


def test_try_acquire_invalid_closed_and_waiter_paths() -> None:
    s = vsem.new(2)
    assert s.try_acquire(0) is False
    assert s.try_acquire(3) is False

    closed = vsem.new(1)
    closed.close()
    assert closed.try_acquire() is False

    blocked = vsem.new(1)
    blocked.acquire()
    result: list[bool] = []

    def worker() -> None:
        result.append(blocked.acquire(timeout=1.0))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    assert blocked.try_acquire() is False
    blocked.release()
    t.join(timeout=1.0)
    assert result == [True]
    blocked.release()


def test_acquire_timeout() -> None:
    s = vsem.new(1)
    assert s.acquire() is True
    start = time.monotonic()
    assert s.acquire(timeout=0.05) is False
    assert time.monotonic() - start >= 0.05
    # The timed-out waiter must not linger and block later acquirers.
    s.release()
    assert s.acquire() is True


def test_blocking_acquire_wakes_on_release() -> None:
    s = vsem.new(1)
    s.acquire()
    result: list[bool] = []

    def worker() -> None:
        result.append(s.acquire(timeout=1.0))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    s.release()
    t.join(timeout=1.0)
    assert result == [True]


def test_fifo_fairness() -> None:
    s = vsem.new(2)
    s.acquire(2)  # fully saturated
    order: list[int] = []
    lock = threading.Lock()

    def worker(idx: int, weight: int) -> None:
        s.acquire(weight, timeout=1.0)
        with lock:
            order.append(idx)

    # First waiter needs 2 permits; second needs 1. FIFO must not let the
    # smaller request jump ahead even though 1 permit alone would satisfy it.
    t1 = threading.Thread(target=worker, args=(1, 2))
    t1.start()
    time.sleep(0.05)
    t2 = threading.Thread(target=worker, args=(2, 1))
    t2.start()
    time.sleep(0.05)

    s.release(1)  # not enough for waiter #1 (needs 2); #2 must not jump ahead
    time.sleep(0.05)
    assert order == []
    s.release(1)  # now waiter #1 can proceed
    t1.join(timeout=1.0)
    s.release(2)  # let waiter #1's permits free up for waiter #2
    t2.join(timeout=1.0)
    assert order == [1, 2]


def test_close_wakes_waiters() -> None:
    s = vsem.new(1)
    s.acquire()
    errors: list[ValidationError] = []

    def worker() -> None:
        try:
            s.acquire(timeout=1.0)
        except ValidationError as exc:
            errors.append(exc)

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    s.close()
    t.join(timeout=1.0)
    assert len(errors) == 1
    assert errors[0].code == "sem.closed"


def test_acquire_on_closed_raises() -> None:
    s = vsem.new(1)
    s.close()
    with pytest.raises(ValidationError) as exc:
        s.acquire()
    assert exc.value.code == "sem.closed"


def test_close_is_idempotent() -> None:
    s = vsem.new(1)
    s.close()
    s.close()


def test_guard_releases() -> None:
    s = vsem.new(1)
    with s.guard() as ok:
        assert ok is True
        assert s.use() == 1
    assert s.use() == 0


def test_guard_timeout_does_not_release() -> None:
    s = vsem.new(1)
    s.acquire()
    with s.guard(timeout=0.05) as ok:
        assert ok is False
    # Failed acquisition must not decrement the counter on exit.
    assert s.use() == 1


def test_validation() -> None:
    with pytest.raises(ValidationError):
        vsem.new(0)
    with pytest.raises(ValidationError):
        vsem.new(-1)
    sem, err = vsem.new_e(0)
    assert sem is None
    assert err is not None and err.code == "sem.invalid_capacity"
    sem, err = vsem.new_e(1)
    assert sem is not None
    assert err is None
    s = vsem.new(2)
    with pytest.raises(ValidationError):
        s.acquire(0)
    with pytest.raises(ValidationError):
        s.acquire(3)  # exceeds capacity
    with pytest.raises(ValidationError):
        s.release(0)
    err = s.release_e(0)
    assert err is not None and err.code == "sem.invalid_weight"


def test_release_too_many() -> None:
    s = vsem.new(2)
    s.acquire()
    with pytest.raises(ValidationError) as exc:
        s.release(2)
    assert exc.value.code == "sem.release_too_many"
    err = s.release_e(2)
    assert err is not None and err.code == "sem.release_too_many"
    assert s.release_e(1) is None
