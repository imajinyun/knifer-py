import pytest

from kniferpy.vjob import (
    Batch,
    ErrInvalidMapJob,
    ErrInvalidRange,
    ErrNilJob,
    Options,
    Slice,
    new_batch,
    new_batch_single,
    new_map,
    new_map_keys,
    new_slice,
    new_slice_single,
    run,
    run_with,
)

# --- run ---


def test_run_nil_job():
    with pytest.raises(ErrNilJob, match="job is nil"):
        run(None)


def test_run_empty_job():
    j = new_slice(lambda start, end: None, 0)
    run(j)  # no-op


def test_run_slice_default():
    results = []

    def fn(start: int, end: int):
        results.append((start, end))

    j = new_slice(fn, 5)
    run(j)
    assert results == [(0, 5)]


def test_run_with_custom_opts():
    results = []

    def fn(start: int, end: int):
        results.append((start, end))

    j = new_slice(fn, 5)
    run_with(j, Options(BatchSize=2, MaxConcurrency=2))
    assert sorted(results) == [(0, 2), (2, 4), (4, 5)]


# --- new_slice_single ----------------------------------------------------


def test_new_slice_single():
    results = []

    def fn(idx: int):
        results.append(idx)

    j = new_slice_single(fn, 3)
    run(j)
    assert sorted(results) == [0, 1, 2]


def test_new_slice_single_merge():
    side_effects = []

    def fn(idx: int):
        def merge():
            side_effects.append(idx)

        return merge

    j = new_slice_single(fn, 3)
    run(j)
    assert side_effects == [0, 1, 2]


# --- new_batch_single ----------------------------------------------------


def test_new_batch_single():
    seen = []

    def fn(val: int):
        seen.append(val)

    j = new_batch_single(fn, [3, 1, 2])
    run(j)
    assert sorted(seen) == [1, 2, 3]


def test_new_batch_single_with_opts():
    seen = []

    def fn(val: int):
        seen.append(val)

    j = new_batch_single(fn, [1, 2, 3]).with_batch_size(1).with_max_concurrency(2)
    run(j)
    assert sorted(seen) == [1, 2, 3]


# --- new_map -------------------------------------------------------------


def test_new_map():
    data = {2: "b", 1: "a"}
    keys = []

    def fn(key: int):
        keys.append(key)

    j = new_map(fn, data)
    run(j)
    assert sorted(keys) == [1, 2]


def test_new_map_empty():
    j = new_map(lambda k: None, {})
    run(j)  # no-op


def test_new_map_invalid_fn():
    with pytest.raises(ErrInvalidMapJob, match="callable"):
        new_map("not a function", {"a": 1})


def test_new_map_invalid_data():
    with pytest.raises(ErrInvalidMapJob, match="dict"):
        new_map(lambda k: None, [1, 2, 3])


# --- new_map_keys --------------------------------------------------------


def test_new_map_keys():
    data = {"a": 1, "b": 2}
    keys = []

    def fn(key: str):
        keys.append(key)

    j = new_map_keys(fn, data)
    run(j)
    assert sorted(keys) == ["a", "b"]


# --- Slice range validation ----------------------------------------------


def test_slice_invalid_range():
    j = new_slice(lambda start, end: None, 5)
    with pytest.raises(ErrInvalidRange):
        j.run(-1, 3)
    with pytest.raises(ErrInvalidRange):
        j.run(3, 2)
    with pytest.raises(ErrInvalidRange):
        j.run(0, 10)


# --- Batch range validation ----------------------------------------------


def test_batch_invalid_range():
    j = new_batch(lambda vals: None, [1, 2, 3])
    with pytest.raises(ErrInvalidRange):
        j.run(-1, 2)
    with pytest.raises(ErrInvalidRange):
        j.run(2, 1)
    with pytest.raises(ErrInvalidRange):
        j.run(0, 5)


# --- Slice with_batch_size / with_max_concurrency ------------------------


def test_slice_with_batch_size():
    j = new_slice(lambda start, end: None, 10)
    j.with_batch_size(3)
    assert j.job_options().BatchSize == 3


def test_slice_with_max_concurrency():
    j = new_slice(lambda start, end: None, 10)
    j.with_max_concurrency(4)
    assert j.job_options().MaxConcurrency == 4


def test_slice_chaining():
    j = new_slice(lambda start, end: None, 10).with_batch_size(3).with_max_concurrency(4)
    opts = j.job_options()
    assert opts.BatchSize == 3
    assert opts.MaxConcurrency == 4


# --- Batch with_batch_size / with_max_concurrency ------------------------


def test_batch_with_batch_size():
    j = new_batch(lambda vals: None, [1, 2, 3])
    j.with_batch_size(2)
    assert j.job_options().BatchSize == 2


def test_batch_with_max_concurrency():
    j = new_batch(lambda vals: None, [1, 2, 3])
    j.with_max_concurrency(4)
    assert j.job_options().MaxConcurrency == 4


# --- concurrent execution ------------------------------------------------


def test_concurrent_slice():
    results = []

    def fn(start: int, end: int):
        results.append((start, end))

    j = new_slice(fn, 10).with_batch_size(2).with_max_concurrency(4)
    run(j)
    all_indices = []
    for start, end in results:
        all_indices.extend(range(start, end))
    assert sorted(all_indices) == list(range(10))


def test_concurrent_batch():
    results = []

    def fn(vals: list[int]):
        results.extend(vals)

    j = new_batch(fn, list(range(20))).with_batch_size(3).with_max_concurrency(4)
    run(j)
    assert sorted(results) == list(range(20))


# --- Options normalization -----------------------------------------------


def test_options_normalized():
    opts = Options()
    n = opts.normalized(10)
    assert n.BatchSize == 10
    assert n.MaxConcurrency == 1


def test_options_normalized_custom():
    opts = Options(BatchSize=3, MaxConcurrency=5)
    n = opts.normalized(10)
    assert n.BatchSize == 3
    assert n.MaxConcurrency == 5


# --- chunks helper -------------------------------------------------------


def test_chunks():
    from kniferpy.internal.jobx import chunks

    assert chunks(0, 3) == 0
    assert chunks(10, 3) == 4  # 3+3+3+1
    assert chunks(10, 1) == 10
    assert chunks(10, 10) == 1
    assert chunks(10, 0) == 0


# --- run_with explicit options -------------------------------------------


def test_run_with_explicit():
    results = []

    def fn(start: int, end: int):
        results.append((start, end))

    j = new_slice(fn, 6)
    run_with(j, Options(BatchSize=2, MaxConcurrency=1))
    assert results == [(0, 2), (2, 4), (4, 6)]


def test_run_with_default_opts():
    results = []

    def fn(start: int, end: int):
        results.append((start, end))

    j = new_slice(fn, 3)
    run_with(j, Options())
    assert results == [(0, 3)]


# --- Merge side effects --------------------------------------------------


def test_merge_side_effects():
    ops = []

    def fn(idx: int):
        def merge():
            ops.append(f"merge_{idx}")

        return merge

    j = new_slice_single(fn, 3)
    run(j)
    assert ops == ["merge_0", "merge_1", "merge_2"]


# --- nil run function ----------------------------------------------------


def test_slice_nil_run():
    j = Slice(None, 5)
    result = j.run(0, 5)
    assert result is None


def test_batch_nil_run():
    j = Batch(None, [1, 2, 3])
    result = j.run(0, 3)
    assert result is None