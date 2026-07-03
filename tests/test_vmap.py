from __future__ import annotations

import pytest

from kniferpy import vmap
from kniferpy.verr import KniferError

# --- new / of / from_pairs / from_entries ------------------------------------


def test_new() -> None:
    assert vmap.new() == {}


def test_new_with_cap() -> None:
    assert vmap.new_with_cap(10) == {}


def test_of() -> None:
    result: dict[str, int] = vmap.of("a", 1, "b", 2)
    assert result == {"a": 1, "b": 2}


def test_of_odd_keys() -> None:
    result: dict[str, int] = vmap.of("a", 1, "b")
    assert result == {"a": 1}


def test_of_e() -> None:
    result, err = vmap.of_e("a", 1, "b", 2)
    assert result == {"a": 1, "b": 2}
    assert err is None


def test_of_e_odd_keys() -> None:
    result, err = vmap.of_e("a", 1, "b")
    assert result == {"a": 1}
    assert isinstance(err, ValueError)


def test_from_pairs() -> None:
    assert vmap.from_pairs(("a", 1), ("b", 2)) == {"a": 1, "b": 2}


def test_from_entries() -> None:
    assert vmap.from_entries([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}


# --- or_empty / is_empty / is_not_empty ---------------------------------------


def test_or_empty() -> None:
    assert vmap.or_empty({"a": 1}) == {"a": 1}
    assert vmap.or_empty(None) == {}


def test_is_empty() -> None:
    assert vmap.is_empty({}) is True
    assert vmap.is_empty({"a": 1}) is False


def test_is_not_empty() -> None:
    assert vmap.is_not_empty({"a": 1}) is True
    assert vmap.is_not_empty({}) is False


# --- contains_key / contains_value --------------------------------------------


def test_contains_key() -> None:
    assert vmap.contains_key({"a": 1}, "a") is True
    assert vmap.contains_key({"a": 1}, "b") is False


def test_contains_value() -> None:
    assert vmap.contains_value({"a": 1, "b": 2}, 1) is True
    assert vmap.contains_value({"a": 1, "b": 2}, 3) is False


# --- some / every -------------------------------------------------------------


def test_some() -> None:
    m = {"a": 1, "b": 2, "c": 3}
    assert vmap.some(m, lambda k, v: v > 2) is True
    assert vmap.some(m, lambda k, v: v > 10) is False


def test_every() -> None:
    m = {"a": 1, "b": 2, "c": 3}
    assert vmap.every(m, lambda k, v: v > 0) is True
    assert vmap.every(m, lambda k, v: v > 2) is False


# --- get / get_or / get_any ---------------------------------------------------


def test_get() -> None:
    assert vmap.get({"a": 1}, "a") == 1
    assert vmap.get({"a": 1}, "b") is None


def test_get_or() -> None:
    assert vmap.get_or({"a": 1}, "a", 0) == 1
    assert vmap.get_or({"a": 1}, "b", 0) == 0


def test_get_any() -> None:
    value, found = vmap.get_any({"a": 1, "b": 2}, "b", "a")
    assert value == 2
    assert found is True


def test_get_any_not_found() -> None:
    value, found = vmap.get_any({"a": 1}, "x", "y")
    assert value is None
    assert found is False


# --- find / find_key ----------------------------------------------------------


def test_find() -> None:
    result = vmap.find({"a": 1, "b": 2}, lambda k, v: v == 2)
    assert result == ("b", 2)


def test_find_not_found() -> None:
    assert vmap.find({"a": 1}, lambda k, v: v == 99) is None


def test_find_key() -> None:
    key, found = vmap.find_key({"a": 1, "b": 2}, lambda v: v == 2)
    assert key == "b"
    assert found is True


def test_find_key_not_found() -> None:
    key, found = vmap.find_key({"a": 1}, lambda v: v == 99)
    assert found is False


# --- keys / values / sorted_keys / entries ------------------------------------


def test_keys() -> None:
    assert set(vmap.keys({"a": 1, "b": 2})) == {"a", "b"}


def test_values() -> None:
    assert set(vmap.values({"a": 1, "b": 2})) == {1, 2}


def test_sorted_keys() -> None:
    assert vmap.sorted_keys({"b": 2, "a": 1}) == ["a", "b"]


def test_sorted_keys_by() -> None:
    assert vmap.sorted_keys_by({"ab": 1, "a": 2}, len) == ["a", "ab"]


def test_sorted_values() -> None:
    assert vmap.sorted_values({"b": 2, "a": 1}) == [1, 2]


def test_keys_of() -> None:
    assert set(vmap.keys_of({"a": 1, "b": 2, "c": 1}, 1)) == {"a", "c"}


def test_entries() -> None:
    entries = vmap.entries({"a": 1, "b": 2})
    assert set(entries) == {("a", 1), ("b", 2)}


# --- iter_items / iter_keys / iter_values -------------------------------------


def test_iter_items() -> None:
    result = list(vmap.iter_items({"a": 1, "b": 2}))
    assert len(result) == 2


def test_iter_keys() -> None:
    result = set(vmap.iter_keys({"a": 1, "b": 2}))
    assert result == {"a", "b"}


def test_iter_values() -> None:
    result = set(vmap.iter_values({"a": 1, "b": 2}))
    assert result == {1, 2}


# --- map_items / map_keys / map_values ----------------------------------------


def test_map_items() -> None:
    result = vmap.map_items({"a": 1, "b": 2}, lambda k, v: (k.upper(), v * 10))
    assert result == {"A": 10, "B": 20}


def test_map_keys() -> None:
    result = vmap.map_keys({"a": 1, "b": 2}, lambda k, v: k.upper())
    assert result == {"A": 1, "B": 2}


def test_map_values() -> None:
    result = vmap.map_values({"a": 1, "b": 2}, lambda k, v: v * 10)
    assert result == {"a": 10, "b": 20}


# --- map_err variations -------------------------------------------------------


def test_map_err_success() -> None:
    result = vmap.map_err({"a": 1}, lambda k, v: (k, v * 2, None))
    assert result == {"a": 2}


def test_map_err_failure() -> None:
    with pytest.raises(KniferError, match="boom"):
        vmap.map_err({"a": 1}, lambda k, v: (None, None, Exception("boom")))


def test_map_keys_err_failure() -> None:
    with pytest.raises(KniferError, match="fail"):
        vmap.map_keys_err({"a": 1}, lambda k, v: (None, Exception("fail")))


def test_map_values_err_failure() -> None:
    with pytest.raises(KniferError, match="fail"):
        vmap.map_values_err({"a": 1}, lambda k, v: (None, Exception("fail")))


# --- to_slice ----------------------------------------------------------------


def test_to_slice() -> None:
    result = vmap.to_slice({"a": 1, "b": 2}, lambda k, v: f"{k}={v}")
    assert set(result) == {"a=1", "b=2"}


# --- filter / reject / filter_keys / filter_values ----------------------------


def test_filter_items() -> None:
    result = vmap.filter_items({"a": 1, "b": 2, "c": 3}, lambda k, v: v > 1)
    assert result == {"b": 2, "c": 3}


def test_reject() -> None:
    result = vmap.reject({"a": 1, "b": 2, "c": 3}, lambda k, v: v > 1)
    assert result == {"a": 1}


def test_filter_keys() -> None:
    result = vmap.filter_keys({"a": 1, "b": 2, "c": 3}, lambda k: k in ("a", "c"))
    assert result == {"a": 1, "c": 3}


def test_filter_values() -> None:
    result = vmap.filter_values({"a": 1, "b": 2, "c": 3}, lambda v: v % 2 == 0)
    assert result == {"b": 2}


# --- pick_by / omit_by / partition --------------------------------------------


def test_pick_by() -> None:
    result = vmap.pick_by({"a": 1, "b": 2}, lambda k, v: v > 1)
    assert result == {"b": 2}


def test_omit_by() -> None:
    result = vmap.omit_by({"a": 1, "b": 2}, lambda k, v: v > 1)
    assert result == {"a": 1}


def test_partition() -> None:
    matched, rejected = vmap.partition({"a": 1, "b": 2, "c": 3}, lambda k, v: v > 1)
    assert matched == {"b": 2, "c": 3}
    assert rejected == {"a": 1}


# --- reduce / reduce_err ------------------------------------------------------


def test_reduce() -> None:
    result = vmap.reduce({"a": 1, "b": 2}, 0, lambda acc, k, v: acc + v)
    assert result == 3


def test_reduce_err_success() -> None:
    result = vmap.reduce_err({"a": 1, "b": 2}, 0, lambda acc, k, v: (acc + v, None))
    assert result == 3


def test_reduce_err_failure() -> None:
    with pytest.raises(KniferError, match="fail"):
        vmap.reduce_err({"a": 1}, 0, lambda acc, k, v: (None, Exception("fail")))


# --- filter_err ---------------------------------------------------------------


def test_filter_err_success() -> None:
    result = vmap.filter_err({"a": 1, "b": 2}, lambda k, v: (v > 1, None))
    assert result == {"b": 2}


def test_filter_err_failure() -> None:
    with pytest.raises(KniferError, match="err"):
        vmap.filter_err({"a": 1}, lambda k, v: (None, Exception("err")))


# --- group_by / count_by ------------------------------------------------------


def test_group_by() -> None:
    result = vmap.group_by(["a1", "a2", "b1"], lambda s: s[0])
    assert result == {"a": ["a1", "a2"], "b": ["b1"]}


def test_count_by() -> None:
    result = vmap.count_by(["a1", "a2", "b1"], lambda s: s[0])
    assert result == {"a": 2, "b": 1}


# --- inverse / invert ---------------------------------------------------------


def test_inverse() -> None:
    assert vmap.inverse({"a": 1, "b": 2}) == {1: "a", 2: "b"}


def test_invert() -> None:
    assert vmap.invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}


# --- merge / merge_with_overwrite / merge_without_overwrite -------------------


def test_merge() -> None:
    result = vmap.merge({"a": 1}, {"b": 2}, {"c": 3})
    assert result == {"a": 1, "b": 2, "c": 3}


def test_merge_with_overwrite() -> None:
    dst = {"a": 1, "b": 2}
    vmap.merge_with_overwrite(dst, {"b": 20, "c": 3})
    assert dst == {"a": 1, "b": 20, "c": 3}


def test_merge_without_overwrite() -> None:
    dst = {"a": 1, "b": 2}
    vmap.merge_without_overwrite(dst, {"b": 20, "c": 3})
    assert dst == {"a": 1, "b": 2, "c": 3}


def test_assign() -> None:
    assert vmap.assign({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_merge_func() -> None:
    result = vmap.merge_func(lambda old, new: old + new, {"a": 1}, {"a": 2, "b": 3})
    assert result == {"a": 3, "b": 3}


# --- intersect / diff / symmetric_diff ---------------------------------------


def test_intersect() -> None:
    result = vmap.intersect({"a": 1, "b": 2}, {"b": 20, "c": 3})
    assert result == {"b": 2}


def test_intersect_empty() -> None:
    assert vmap.intersect() == {}


def test_diff() -> None:
    result = vmap.diff({"a": 1, "b": 2, "c": 3}, {"b": 20})
    assert result == {"a": 1, "c": 3}


def test_symmetric_diff() -> None:
    result = vmap.symmetric_diff({"a": 1, "b": 2}, {"b": 2, "c": 3})
    assert result == {"a": 1, "c": 3}


# --- pick / omit --------------------------------------------------------------


def test_pick() -> None:
    assert vmap.pick({"a": 1, "b": 2, "c": 3}, "a", "c") == {"a": 1, "c": 3}


def test_omit() -> None:
    assert vmap.omit({"a": 1, "b": 2, "c": 3}, "a", "c") == {"b": 2}


# --- clear / update / clone ---------------------------------------------------


def test_clear() -> None:
    m = {"a": 1, "b": 2}
    vmap.clear(m)
    assert m == {}


def test_update() -> None:
    dst = {"a": 1}
    result = vmap.update(dst, {"b": 2})
    assert result == {"a": 1, "b": 2}
    assert dst == {"a": 1, "b": 2}


def test_clone() -> None:
    original = {"a": 1, "b": 2}
    cloned = vmap.clone(original)
    assert cloned == original
    assert cloned is not original


# --- equal / equal_by ---------------------------------------------------------


def test_equal() -> None:
    assert vmap.equal({"a": 1}, {"a": 1}) is True
    assert vmap.equal({"a": 1}, {"a": 2}) is False
    assert vmap.equal({"a": 1}, {"b": 1}) is False


def test_equal_by() -> None:
    a = {"x": [1, 2], "y": [3]}
    b = {"x": [1, 2], "y": [3]}
    assert vmap.equal_by(a, b, lambda v1, v2: v1 == v2) is True

    b2 = {"x": [1, 2], "y": [4]}
    assert vmap.equal_by(a, b2, lambda v1, v2: v1 == v2) is False


# --- for_each ----------------------------------------------------------------


def test_for_each() -> None:
    seen: list[str] = []
    vmap.for_each({"a": 1, "b": 2}, lambda k, v: seen.append(f"{k}={v}"))
    assert set(seen) == {"a=1", "b=2"}
