from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from kniferpy.verr import ValidationError


class _Waiter:
    __slots__ = ("err", "n", "ready")

    def __init__(self, n: int) -> None:
        self.n = n
        self.ready = threading.Event()
        self.err: Exception | None = None


class Semaphore:
    """A weighted, cancellable, and closeable counting semaphore.

    Unlike ``threading.Semaphore`` this supports acquiring/releasing multiple
    permits at once and wakes blocked waiters in FIFO order for fairness.
    Instances are safe for concurrent use.
    """

    __slots__ = ("_cap", "_closed", "_cur", "_mux", "_waiters")

    def __init__(self, cap: int) -> None:
        if cap <= 0:
            raise ValidationError(f"vsem: invalid capacity: {cap}", code="sem.invalid_capacity")
        self._cap = cap
        self._cur = 0
        self._mux = threading.Lock()
        self._waiters: list[_Waiter] = []
        self._closed = False

    def acquire(self, n: int = 1, *, timeout: float | None = None) -> bool:
        """Obtain ``n`` permits, blocking until success, timeout, or close.

        Returns ``True`` on success and ``False`` on timeout. Raises
        ``ValidationError`` for an invalid weight or when the semaphore is
        already closed.
        """
        if n <= 0 or n > self._cap:
            raise ValidationError(f"vsem: invalid weight: {n}", code="sem.invalid_weight")

        with self._mux:
            if self._closed:
                raise self._closed_error()
            # Fast path: no waiters and enough capacity.
            if not self._waiters and self._cur + n <= self._cap:
                self._cur += n
                return True
            # Slow path: enqueue and wait.
            waiter = _Waiter(n)
            self._waiters.append(waiter)

        if waiter.ready.wait(timeout):
            with self._mux:
                if waiter.err is not None:
                    raise waiter.err
                return True

        # Timeout: remove from the queue, compensating if permits were granted
        # in the race between the timeout firing and re-acquiring the lock.
        with self._mux:
            if waiter.ready.is_set():
                if waiter.err is not None:
                    raise waiter.err
                self._cur -= n
                self._notify_locked()
            else:
                self._remove_waiter_locked(waiter)
                self._notify_locked()
            return False

    def try_acquire(self, n: int = 1) -> bool:
        """Attempt to obtain ``n`` permits without blocking."""
        if n <= 0 or n > self._cap:
            return False
        with self._mux:
            if self._closed or self._waiters:
                return False
            if self._cur + n <= self._cap:
                self._cur += n
                return True
            return False

    def release(self, n: int = 1) -> None:
        """Release ``n`` permits and wake waiters in FIFO order."""
        if n <= 0:
            raise ValidationError(f"vsem: invalid weight: {n}", code="sem.invalid_weight")
        with self._mux:
            if self._cur < n:
                raise ValidationError(
                    "vsem: release more than acquired", code="sem.release_too_many"
                )
            self._cur -= n
            self._notify_locked()

    @contextmanager
    def guard(self, n: int = 1, *, timeout: float | None = None) -> Iterator[bool]:
        """Context manager that acquires ``n`` permits and always releases them.

        Yields ``True`` when acquired and ``False`` on timeout; permits are
        only released when they were actually acquired.
        """
        acquired = self.acquire(n, timeout=timeout)
        try:
            yield acquired
        finally:
            if acquired:
                self.release(n)

    def use(self) -> int:
        """Return the number of currently acquired permits."""
        with self._mux:
            return self._cur

    def cap(self) -> int:
        """Return the total capacity."""
        return self._cap

    def close(self) -> None:
        """Close the semaphore and wake all waiters with a closed error.

        Already acquired permits are not reclaimed; holders still release them.
        """
        with self._mux:
            if self._closed:
                return
            self._closed = True
            for waiter in self._waiters:
                waiter.err = self._closed_error()
                waiter.ready.set()
            self._waiters = []

    def _notify_locked(self) -> None:
        while self._waiters:
            waiter = self._waiters[0]
            if self._cur + waiter.n > self._cap:
                return  # Keep FIFO fairness: do not let later waiters jump ahead.
            self._cur += waiter.n
            self._waiters.pop(0)
            waiter.err = None
            waiter.ready.set()

    def _remove_waiter_locked(self, target: _Waiter) -> None:
        for i, waiter in enumerate(self._waiters):
            if waiter is target:
                del self._waiters[i]
                return

    @staticmethod
    def _closed_error() -> ValidationError:
        return ValidationError("vsem: closed", code="sem.closed")


def new(cap: int) -> Semaphore:
    """Create a semaphore with ``cap`` permits."""
    return Semaphore(cap)
