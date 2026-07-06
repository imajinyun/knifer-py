from __future__ import annotations

import json

from kniferpy import vset


def test_new_and_add() -> None:
    s = vset.New(1, 2, 3)
    assert s.contains(1)
    assert s.contains(2)
    assert s.contains(3)
    assert not s.contains(4)


def test_add_remove() -> None:
    s = vset.New(1, 2)
    s.add(3)
    assert s.contains(3)
    s.remove(2)
    assert not s.contains(2)
    s.remove(99)  # no error


def test_len() -> None:
    s = vset.New(1, 2, 3)
    assert len(s) == 3
    assert len(vset.New()) == 0


def test_members() -> None:
    s = vset.New(1, 2, 3)
    m = s.members()
    assert sorted(m) == [1, 2, 3]


def test_union() -> None:
    a = vset.New(1, 2, 3)
    b = vset.New(3, 4, 5)
    u = a.union(b)
    assert sorted(u.members()) == [1, 2, 3, 4, 5]


def test_intersect() -> None:
    a = vset.New(1, 2, 3)
    b = vset.New(2, 3, 4)
    i = a.intersect(b)
    assert sorted(i.members()) == [2, 3]


def test_sub() -> None:
    a = vset.New(1, 2, 3)
    b = vset.New(2, 3)
    d = a.sub(b)
    assert sorted(d.members()) == [1]


def test_equal() -> None:
    assert vset.New(1, 2).equal(vset.New(2, 1))
    assert not vset.New(1, 2).equal(vset.New(1, 2, 3))


def test_eq_operator() -> None:
    assert vset.New(1, 2) == vset.New(2, 1)
    assert vset.New(1, 2) != vset.New(1, 2, 3)


def test_contains_operator() -> None:
    s = vset.New(1, 2, 3)
    assert 1 in s
    assert 4 not in s


def test_or_and_sub_operators() -> None:
    a = vset.New(1, 2, 3)
    b = vset.New(3, 4, 5)
    assert sorted((a | b).members()) == [1, 2, 3, 4, 5]
    assert sorted((a & b).members()) == [3]
    assert sorted((a - b).members()) == [1, 2]


def test_iteration() -> None:
    s = vset.New(1, 2, 3)
    assert sorted(list(s)) == [1, 2, 3]


def test_str_repr() -> None:
    s = vset.New(1, 2)
    assert "set" in str(s)
    assert "1" in str(s)


def test_json_roundtrip() -> None:
    s = vset.New(1, 2, 3)
    json_str = s.to_json()
    s2 = vset.New().from_json(json_str)
    assert s.equal(s2)


def test_json_with_options() -> None:
    s = vset.New(1, 2, 3)
    opt = vset.WithSetMarshalFunc(lambda v: json.dumps(list(reversed(v))).encode())
    json_str = s.to_json([opt])
    assert json_str == "[3, 2, 1]"


def test_typed_constructors() -> None:
    assert vset.NewInt(1, 2, 3).contains(1)
    assert vset.NewString("a", "b").contains("a")
    assert vset.NewInt64(42).contains(42)


def test_empty() -> None:
    s = vset.New()
    assert len(s) == 0
    assert s.members() == []
    assert s.equal(vset.New())


def test_intersect_optimization() -> None:
    a = vset.New(1, 2, 3)
    b = vset.New(2, 3, 4, 5, 6, 7, 8, 9, 10)
    i = a.intersect(b)
    assert sorted(i.members()) == [2, 3]


def test_custom_json_unmarshal_and_marshal_json() -> None:
    s = vset.New(1, 2)
    marshal_opt = vset.WithSetMarshalFunc(lambda values: b"custom")
    unmarshal_opt = vset.WithSetUnmarshalFunc(lambda data: [3, 4])

    assert s.marshal_json([marshal_opt]) == b"custom"
    s.unmarshal_json(b"ignored", [unmarshal_opt])
    assert sorted(s.members()) == [1, 2, 3, 4]
    s2 = vset.Set.from_json("ignored", [unmarshal_opt])
    assert sorted(s2.members()) == [3, 4]


def test_yaml_helpers_and_fallback(monkeypatch) -> None:
    s = vset.New("a", "b")

    dumped = s.to_yaml()
    assert "a" in dumped
    assert sorted(vset.Set.from_yaml(dumped).members()) == ["a", "b"]
    assert sorted(s.marshal_yaml()) == ["a", "b"]

    target = vset.New()
    target.unmarshal_yaml(["x", "y"])
    assert sorted(target.members()) == ["x", "y"]
    target.unmarshal_yaml("not-list")
    assert sorted(target.members()) == ["x", "y"]


def test_bulk_set_helpers_and_relationships() -> None:
    s = vset.New(1)
    s.add_all(2, 3)
    assert s.contains_all(1, 2, 3)
    assert not s.contains_all(1, 4)
    assert vset.New(1, 2).is_subset(s)
    assert s.is_superset(vset.New(1, 2)) is False
    assert vset.New(1, 2).is_superset(s) is True
    assert sorted(s.symmetric_difference(vset.New(3, 4)).members()) == [1, 2, 4]
    assert sorted(s.difference(vset.New(2)).members()) == [1, 3]
    assert s.to_slice() == s.members()
    assert not s.is_empty()
    assert s.size() == 3
    s.remove_all(1, 2)
    assert sorted(s.members()) == [3]
    clone = s.clone()
    assert clone == s
    assert clone is not s
    s.clear()
    assert s.is_empty()


def test_for_each_filter_map_reduce() -> None:
    s = vset.New(1, 2, 3)
    seen: list[int] = []
    s.for_each(seen.append)

    assert sorted(seen) == [1, 2, 3]
    assert sorted(s.filter(lambda item: item % 2 == 1).members()) == [1, 3]
    assert sorted(s.map(lambda item: item * 10).members()) == [10, 20, 30]
    assert s.reduce(lambda total, item: total + item, 0) == 6


def test_more_typed_constructors_and_type_aliases() -> None:
    assert vset.NewInt32(1).contains(1)
    assert vset.NewUint(1).contains(1)
    assert vset.NewUint32(1).contains(1)
    assert vset.NewUint64(1).contains(1)
    assert isinstance(vset.NewInt(1), vset.Set)
    assert isinstance(vset.NewString("x"), vset.Set)


def test_plain_set_helpers() -> None:
    items = vset.new(1, 2, 2)
    other = vset.from_iterable([2, 3])

    assert items == {1, 2}
    assert other == {2, 3}
    assert vset.contains(items, 1)
    assert vset.union(items, other) == {1, 2, 3}
    assert vset.intersect(items, other) == {2}
    assert vset.sub(items, other) == {1}
    assert vset.equal(items, {2, 1})
    assert sorted(vset.members(items)) == [1, 2]


def test_set_equality_with_non_set() -> None:
    assert (vset.New(1) == {1}) is False
