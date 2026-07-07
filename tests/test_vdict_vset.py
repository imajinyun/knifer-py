import warnings

import pytest

from kniferpy import vdict, vset

# ── vdict backward compat (all PascalCase functions are deprecated) ──────────


def test_vdict_backward_compat() -> None:
    value = {"a": 1, "b": 2, "c": 3}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert not vdict.is_empty(value)
        assert vdict.contains_key(value, "a")
        assert vdict.contains_value(value, 2)
        assert vdict.get_or(value, "missing", 9) == 9
        assert vdict.keys(value) == ["a", "b", "c"]
        assert vdict.values(value) == [1, 2, 3]
        assert vdict.sorted_keys({"b": 2, "a": 1}) == ["a", "b"]
        assert vdict.map_values(value, lambda key, item: f"{key}:{item}") == {
            "a": "a:1",
            "b": "b:2",
            "c": "c:3",
        }
        assert vdict.filter_items(value, lambda key, item: item >= 2) == {"b": 2, "c": 3}
        assert vdict.merge({"a": 1}, {"b": 2}, {"a": 3}) == {"a": 3, "b": 2}
        assert vdict.pick(value, {"a", "c"}) == {"a": 1, "c": 3}
        assert vdict.omit(value, {"b"}) == {"a": 1, "c": 3}
        assert vdict.invert({"a": 1}) == {1: "a"}
        assert vdict.clone(value) == value


def test_vdict_deprecation_warning() -> None:
    with pytest.warns(DeprecationWarning, match="kniferpy.vdict.New is deprecated"):
        vdict.New()


def test_vdict_deprecation_warning_Get() -> None:
    with pytest.warns(DeprecationWarning, match="kniferpy.vdict.Get is deprecated"):
        vdict.Get({"a": 1}, "a")


# ── vset ─────────────────────────────────────────────────────────────────────


def test_vset_helpers() -> None:
    left = vset.new(1, 2, 3)
    right = vset.from_iterable([3, 4])

    assert vset.contains(left, 2)
    assert vset.union(left, right) == {1, 2, 3, 4}
    assert vset.intersect(left, right) == {3}
    assert vset.sub(left, right) == {1, 2}
    assert vset.equal(left, {1, 2, 3})
    assert sorted(vset.members(left)) == [1, 2, 3]
