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