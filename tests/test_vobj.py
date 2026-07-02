from kniferpy import vobj


def test_equal_length_contains_and_empty() -> None:
    assert vobj.equal(1, 1.0)
    assert vobj.not_equal("a", "b")
    assert vobj.length([1, 2, 3]) == 3
    assert vobj.length(10) == -1
    assert vobj.contains([1, 2, 3], 2)
    assert vobj.contains("hello", "ell")
    assert vobj.contains({"a": 1}, 1)
    assert not vobj.contains({"a": 1}, 2)
    assert not vobj.contains(None, "x")
    assert not vobj.contains("hello", None)
    assert vobj.is_empty({})
    assert not vobj.is_empty(1)
    assert vobj.is_not_empty([1])


def test_none_and_empty_predicates() -> None:
    assert vobj.is_none(None)
    assert not vobj.is_none(0)
    assert vobj.is_not_none(0)
    assert not vobj.is_not_none(None)
    assert vobj.is_empty(None)
    assert vobj.is_empty("")
    assert vobj.is_empty([])
    assert not vobj.is_empty("go")


def test_defaults_apply_accept() -> None:
    name = "go"
    assert vobj.default_if_none(name, "x") == "go"
    assert vobj.default_if_none(None, "x") == "x"

    calls = 0

    def supplier() -> str:
        nonlocal calls
        calls += 1
        return "fallback"

    assert vobj.default_if_none_func(name, supplier) == "go"
    assert calls == 0
    assert vobj.default_if_none_func(None, supplier) == "fallback"
    assert calls == 1

    assert vobj.default_if_none_apply(name, str.upper, "fallback") == "GO"
    assert vobj.default_if_none_apply(None, str.upper, "fallback") == "fallback"

    assert vobj.apply(name, len) == 2
    assert vobj.apply(None, len) is None

    captured: list[str] = []
    vobj.accept(name, captured.append)
    vobj.accept(None, captured.append)
    assert captured == ["go"]


def test_basic_type_and_valid_number() -> None:
    assert vobj.is_basic_type("x")
    assert vobj.is_basic_type(1)
    assert not vobj.is_basic_type([1])
    assert not vobj.is_basic_type(None)
    assert vobj.is_valid_if_number(1)
    assert vobj.is_valid_if_number(1.25)
    assert not vobj.is_valid_if_number(float("nan"))
    assert not vobj.is_valid_if_number(float("inf"))
    assert vobj.is_valid_if_number("x")


def test_compare_and_compare_none() -> None:
    assert vobj.compare(1, 2) < 0
    assert vobj.compare(2, 1) > 0
    assert vobj.compare(1, 1) == 0
    assert vobj.compare(None, 1) > 0
    assert vobj.compare(1, None) < 0
    assert vobj.compare(None, None) == 0
    assert vobj.compare_none(None, 1, False) < 0
    assert vobj.compare_none(1, None, False) > 0


def test_type_and_string() -> None:
    assert vobj.type_of(None) is None
    assert vobj.type_of(42) is int
    assert vobj.type_name(None) == ""
    assert vobj.type_name(42) == "int"
    assert vobj.type_name("x") == "str"
    assert vobj.to_string(None) == "null"
    assert vobj.to_string(42) == "42"


def test_aggregate_helpers() -> None:
    assert vobj.empty_count(None, "", [], "go") == 3
    assert vobj.has_none("go", None)
    assert not vobj.has_none("go", 1)
    assert vobj.has_empty("go", [])
    assert not vobj.has_empty("go", [1])
    assert vobj.is_all_empty(None, "", [])
    assert not vobj.is_all_empty("", "x")
    assert vobj.is_all_not_empty("x", [1])
    assert not vobj.is_all_not_empty("x", [])
