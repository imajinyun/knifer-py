from __future__ import annotations

import pytest

from kniferpy import vslice
from kniferpy.verr import KniferError

# --- is_empty / is_not_empty --------------------------------------------------


def test_is_empty() -> None:
    assert vslice.is_empty([]) is True
    assert vslice.is_empty([1]) is False


def test_is_not_empty() -> None:
    assert vslice.is_not_empty([1]) is True
    assert vslice.is_not_empty([]) is False


# --- contains / index_of / last_index_of --------------------------------------


def test_contains() -> None:
    assert vslice.contains([1, 2, 3], 2) is True
    assert vslice.contains([1, 2, 3], 4) is False


def test_index_of() -> None:
    assert vslice.index_of(["a", "b", "c"], "b") == 1
    assert vslice.index_of(["a", "b", "c"], "z") == -1


def test_last_index_of() -> None:
    assert vslice.last_index_of([1, 2, 3, 2], 2) == 3
    assert vslice.last_index_of([1, 2, 3], 4) == -1


# --- reverse / distinct / uniq ------------------------------------------------


def test_reverse() -> None:
    assert vslice.reverse([1, 2, 3]) == [3, 2, 1]


def test_distinct() -> None:
    assert vslice.distinct([1, 2, 2, 3, 1]) == [1, 2, 3]


def test_uniq() -> None:
    assert vslice.uniq([1, 2, 2, 3]) == [1, 2, 3]


def test_uniq_by() -> None:
    items = ["a1", "a2", "b1", "b2"]
    assert vslice.uniq_by(items, lambda s: s[0]) == ["a1", "b1"]


# --- join --------------------------------------------------------------------


def test_join() -> None:
    assert vslice.join([1, 2, 3], "-") == "1-2-3"


def test_join_default_sep() -> None:
    assert vslice.join(["a", "b", "c"]) == "abc"


# --- filter / reject / filter_map ---------------------------------------------


def test_filter_values() -> None:
    assert vslice.filter_values([1, 2, 3, 4], lambda x: x % 2 == 0) == [2, 4]


def test_reject() -> None:
    assert vslice.reject([1, 2, 3, 4], lambda x: x % 2 == 0) == [1, 3]


def test_filter_map() -> None:
    result = vslice.filter_map([1, 2, 3, 4], lambda x: (x * 10, x % 2 == 0))
    assert result == [20, 40]


# --- map / map_err / flat_map -------------------------------------------------


def test_map_values() -> None:
    assert vslice.map_values([1, 2, 3], lambda x: x * 2) == [2, 4, 6]


def test_map_err_success() -> None:
    result = vslice.map_err([1, 2, 3], lambda x: (x * 2, None))
    assert result == [2, 4, 6]


def test_map_err_failure() -> None:
    with pytest.raises(KniferError, match="boom"):
        vslice.map_err([1, 2, 3], lambda x: (None, Exception("boom")))


def test_flat_map() -> None:
    assert vslice.flat_map([1, 2, 3], lambda x: [x, x * 10]) == [1, 10, 2, 20, 3, 30]


# --- reduce / reduce_err ------------------------------------------------------


def test_reduce() -> None:
    assert vslice.reduce([1, 2, 3], 0, lambda acc, x: acc + x) == 6


def test_reduce_err_success() -> None:
    result = vslice.reduce_err([1, 2, 3], 0, lambda acc, x: (acc + x, None))
    assert result == 6


def test_reduce_err_failure() -> None:
    with pytest.raises(KniferError, match="fail"):
        vslice.reduce_err([1, 2, 3], 0, lambda acc, x: (None, Exception("fail")))


# --- filter_err ---------------------------------------------------------------


def test_filter_err_success() -> None:
    result = vslice.filter_err([1, 2, 3, 4], lambda x: (x % 2 == 0, None))
    assert result == [2, 4]


def test_filter_err_failure() -> None:
    with pytest.raises(KniferError, match="err"):
        vslice.filter_err([1, 2, 3], lambda x: (None, Exception("err")))


# --- find / find_index --------------------------------------------------------


def test_find() -> None:
    assert vslice.find([1, 2, 3, 4], lambda x: x > 2) == 3
    assert vslice.find([1, 2, 3], lambda x: x > 10) is None


def test_find_index() -> None:
    assert vslice.find_index([1, 2, 3, 4], lambda x: x > 2) == 2
    assert vslice.find_index([1, 2, 3], lambda x: x > 10) == -1


# --- iter_items / iter_indexed ------------------------------------------------


def test_iter_items() -> None:
    assert list(vslice.iter_items([1, 2, 3])) == [1, 2, 3]


def test_iter_indexed() -> None:
    assert list(vslice.iter_indexed(["a", "b"])) == [(0, "a"), (1, "b")]


# --- group_by / count_by / key_by / associate ---------------------------------


def test_group_by() -> None:
    items = ["a1", "a2", "b1"]
    result = vslice.group_by(items, lambda s: s[0])
    assert result == {"a": ["a1", "a2"], "b": ["b1"]}


def test_count_by() -> None:
    result = vslice.count_by(["a1", "a2", "b1"], lambda s: s[0])
    assert result == {"a": 2, "b": 1}


def test_key_by() -> None:
    result = vslice.key_by([("a", 1), ("b", 2)], lambda x: x[0])
    assert result == {"a": ("a", 1), "b": ("b", 2)}


def test_associate() -> None:
    result = vslice.associate([1, 2, 3], lambda x: (str(x), x * 10))
    assert result == {"1": 10, "2": 20, "3": 30}


def test_slice_to_map() -> None:
    result = vslice.slice_to_map([1, 2], lambda x: (str(x), x))
    assert result == {"1": 1, "2": 2}


# --- chunk / window / sliding -------------------------------------------------


def test_chunk() -> None:
    assert vslice.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_zero_size() -> None:
    assert vslice.chunk([1, 2, 3], 0) == []


def test_window() -> None:
    assert vslice.window([1, 2, 3, 4], 2) == [[1, 2], [2, 3], [3, 4]]


def test_window_size_too_large() -> None:
    assert vslice.window([1, 2], 3) == []


def test_sliding() -> None:
    assert vslice.sliding([1, 2, 3, 4, 5], 3, 2) == [[1, 2, 3], [3, 4, 5]]


def test_sliding_invalid_params() -> None:
    assert vslice.sliding([1, 2, 3], 0, 1) == []
    assert vslice.sliding([1, 2, 3], 2, 0) == []


# --- zip2 / unzip2 ------------------------------------------------------------


def test_zip2() -> None:
    assert vslice.zip2([1, 2], ["a", "b"]) == [(1, "a"), (2, "b")]


def test_unzip2() -> None:
    result = vslice.unzip2([(1, "a"), (2, "b")])
    assert result == ([1, 2], ["a", "b"])


def test_unzip2_empty() -> None:
    assert vslice.unzip2([]) == ([], [])


# --- flatten / compact --------------------------------------------------------


def test_flatten() -> None:
    assert vslice.flatten([[1, 2], [3], [4, 5]]) == [1, 2, 3, 4, 5]


def test_compact() -> None:
    assert vslice.compact([1, None, 2, None, 3]) == [1, 2, 3]


# --- partition_by -------------------------------------------------------------


def test_partition_by() -> None:
    result = vslice.partition_by([1, 1, 2, 2, 3], lambda x: x)
    assert result == [[1, 1], [2, 2], [3]]


def test_partition_by_empty() -> None:
    assert vslice.partition_by([], lambda x: x) == []


# --- sub / concat / union / intersection / subtract ---------------------------


def test_sub() -> None:
    assert vslice.sub([1, 2, 3, 4, 5], 1, 4) == [2, 3, 4]


def test_concat() -> None:
    assert vslice.concat([1, 2], [3, 4], [5]) == [1, 2, 3, 4, 5]


def test_union() -> None:
    assert vslice.union([1, 2, 3], [3, 4, 5]) == [1, 2, 3, 4, 5]


def test_intersection() -> None:
    assert vslice.intersection([1, 2, 3, 4], [3, 4, 5]) == [3, 4]


def test_subtract() -> None:
    assert vslice.subtract([1, 2, 3, 4], [3, 4, 5]) == [1, 2]


# --- page --------------------------------------------------------------------


def test_page() -> None:
    assert vslice.page([1, 2, 3, 4, 5], 1, 2) == [1, 2]
    assert vslice.page([1, 2, 3, 4, 5], 2, 2) == [3, 4]
    assert vslice.page([1, 2, 3, 4, 5], 3, 2) == [5]


def test_page_invalid() -> None:
    assert vslice.page([1, 2, 3], 0, 2) == []
    assert vslice.page([1, 2, 3], 1, 0) == []


# --- for_each ----------------------------------------------------------------


def test_for_each() -> None:
    seen: list[int] = []
    vslice.for_each([1, 2, 3], lambda x: seen.append(x))
    assert seen == [1, 2, 3]
