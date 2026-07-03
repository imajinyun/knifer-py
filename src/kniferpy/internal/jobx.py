"""Parallel job execution with slice, batch, and map adapters.

Ports knifer-go's internal/job with Python-idiomatic mappings:

- Go context.Context -> explicit context (optional, None defaults to no-op)
- Go Sliceable interface -> Python Protocol
- Go goroutines + semaphore -> concurrent.futures.ThreadPoolExecutor
- Go Merge callbacks -> Callable[[], None]
- Go generics -> Python typevars

Errors use kniferpy.verr types with codes knifer.job.<reason>.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, TypeVar

from kniferpy.verr import KniferError

# --- errors --------------------------------------------------------------------

class ErrNilJob(KniferError):
    pass


class ErrInvalidRange(KniferError):
    pass


class ErrInvalidMapJob(KniferError):
    pass


# --- types ---------------------------------------------------------------------

Merge = Callable[[], None]

T = TypeVar("T")


class Sliceable(Protocol):
    def len(self) -> int:
        ...

    def run(self, start: int, end: int) -> Merge | None:
        ...


class OptionCarrier(Protocol):
    def job_options(self) -> Options:
        ...


@dataclass
class Options:
    BatchSize: int = 0
    MaxConcurrency: int = 0

    def normalized(self, length: int) -> Options:
        bs = self.BatchSize if self.BatchSize > 0 else length
        mc = self.MaxConcurrency if self.MaxConcurrency > 0 else 1
        return Options(BatchSize=bs, MaxConcurrency=mc)


def chunks(length: int, batch_size: int) -> int:
    if length <= 0 or batch_size <= 0:
        return 0
    return (length + batch_size - 1) // batch_size


# --- run -----------------------------------------------------------------------

def _replay_merges(job: Sliceable, merges: list[Merge | None]) -> None:
    for idx, merge in enumerate(merges):
        if merge is None:
            continue
        try:
            merge()
        except Exception:
            raise


def _run_serial(job: Sliceable, opts: Options, merges: list[Merge | None]) -> None:
    length = job.len()
    idx = 0
    start = 0
    while start < length:
        end = min(start + opts.BatchSize, length)
        result = job.run(start, end)
        if result is not None:
            merges[idx] = result
        idx += 1
        start = end
    _replay_merges(job, merges)


def _run_concurrent(job: Sliceable, opts: Options, merges: list[Merge | None]) -> None:
    length = job.len()
    with concurrent.futures.ThreadPoolExecutor(max_workers=opts.MaxConcurrency) as executor:
        pending: list[tuple[int, concurrent.futures.Future[Merge | None]]] = []
        idx = 0
        start = 0
        while start < length:
            end = min(start + opts.BatchSize, length)
            f = executor.submit(_run_shard, job, start, end)
            pending.append((idx, f))
            idx += 1
            start = end

        for shard_idx, future in pending:
            merge = future.result()
            if merge is not None:
                merges[shard_idx] = merge

    _replay_merges(job, merges)


def _run_shard(job: Sliceable, start: int, end: int) -> Merge | None:
    return job.run(start, end)


def run(job: Sliceable) -> None:
    if job is None:
        raise ErrNilJob("job is nil")
    length = job.len()
    if length <= 0:
        return

    if hasattr(job, "job_options"):
        opts: Options = job.job_options()
    else:
        opts = Options()

    opts = opts.normalized(length)
    chunk_count = chunks(length, opts.BatchSize)
    merges: list[Merge | None] = [None] * chunk_count

    if opts.MaxConcurrency == 1 or chunk_count == 1:
        _run_serial(job, opts, merges)
    else:
        _run_concurrent(job, opts, merges)


def run_with(job: Sliceable, opts: Options) -> None:
    if job is None:
        raise ErrNilJob("job is nil")
    length = job.len()
    if length <= 0:
        return

    opts = opts.normalized(length)
    chunk_count = chunks(length, opts.BatchSize)
    merges: list[Merge | None] = [None] * chunk_count

    if opts.MaxConcurrency == 1 or chunk_count == 1:
        _run_serial(job, opts, merges)
    else:
        _run_concurrent(job, opts, merges)


# --- Slice adapter -------------------------------------------------------------

_SINGLE_CONCURRENCY = 32


class Slice:
    def __init__(self, fn: Callable[[int, int], Merge | None], length: int):
        self._run = fn
        self._length = length
        self._options = Options()

    def with_batch_size(self, size: int) -> Slice:
        self._options.BatchSize = size
        return self

    def with_max_concurrency(self, max_concurrency: int) -> Slice:
        self._options.MaxConcurrency = max_concurrency
        return self

    def job_options(self) -> Options:
        return self._options

    def len(self) -> int:
        return self._length

    def run(self, start: int, end: int) -> Merge | None:
        if self._run is None:
            return None
        if start < 0 or end < start or end > self._length:
            raise ErrInvalidRange("invalid range")
        return self._run(start, end)


def new_slice(fn: Callable[[int, int], Merge | None], length: int) -> Slice:
    return Slice(fn, length)


def new_slice_single(fn: Callable[[int], Merge | None], length: int) -> Slice:
    def adapter(start: int, end: int) -> Merge | None:
        if fn is None:
            return None
        return fn(start)

    return Slice(adapter, length).with_batch_size(1).with_max_concurrency(_SINGLE_CONCURRENCY)


# --- Batch adapter -------------------------------------------------------------

class Batch:
    def __init__(self, fn: Callable[[list[Any]], Merge | None], vals: list[Any]):
        self._run = fn
        self._vals = list(vals)
        self._options = Options()

    def with_batch_size(self, size: int) -> Batch:
        self._options.BatchSize = size
        return self

    def with_max_concurrency(self, max_concurrency: int) -> Batch:
        self._options.MaxConcurrency = max_concurrency
        return self

    def job_options(self) -> Options:
        return self._options

    def len(self) -> int:
        return len(self._vals)

    def run(self, start: int, end: int) -> Merge | None:
        if self._run is None:
            return None
        if start < 0 or end < start or end > len(self._vals):
            raise ErrInvalidRange("invalid range")
        return self._run(self._vals[start:end])


def new_batch(fn: Callable[[list[Any]], Merge | None], vals: list[Any]) -> Batch:
    return Batch(fn, vals)


def new_batch_single(fn: Callable[[Any], Merge | None], vals: list[Any]) -> Batch:
    def adapter(batch: list[Any]) -> Merge | None:
        if fn is None:
            return None
        return fn(batch[0])

    return Batch(adapter, vals).with_batch_size(1).with_max_concurrency(_SINGLE_CONCURRENCY)


# --- Map adapter ---------------------------------------------------------------

def new_map(fn: Any, data: dict[Any, Any]) -> Slice:
    if not callable(fn):
        raise ErrInvalidMapJob(f"job run must be a callable, got {type(fn).__name__}")
    if not isinstance(data, dict):
        raise ErrInvalidMapJob(f"job data must be a dict, got {type(data).__name__}")

    keys = list(data.keys())

    def adapter(idx: int) -> Any:
        return fn(keys[idx])

    return new_slice_single(adapter, len(keys))


def new_map_keys(fn: Callable[[Any], Merge | None], data: dict[Any, Any]) -> Batch:
    keys = list(data.keys())
    return new_batch_single(fn, keys)