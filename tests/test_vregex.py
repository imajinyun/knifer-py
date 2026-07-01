from kniferpy import vregex


def test_match_and_find() -> None:
    assert vregex.match(r"\d+", "abc123")
    assert not vregex.match(r"\d+", "abc")
    assert vregex.is_match(r"[a-z]+", "abc")
    assert not vregex.is_match(r"[a-z]+", "abc123")
    assert vregex.find(r"\d+", "a12b34") == "12"
    assert vregex.find_all(r"\d+", "a12b34") == ["12", "34"]
    assert vregex.count(r"\d+", "a12b34") == 2


def test_invalid_pattern_is_safe() -> None:
    assert vregex.match(r"(", "anything") is False
    assert vregex.find(r"(", "anything") == ""
    assert vregex.find_all(r"(", "anything") == []
    assert vregex.replace(r"(", "keep", "x") == "keep"


def test_replace_and_delete() -> None:
    assert vregex.replace(r"\d", "a1b2", "*") == "a*b*"
    assert vregex.replace_first(r"\d", "a1b2", "*") == "a*b2"
    assert vregex.replace_func(r"\d", "a1b2", lambda m: f"[{m.group(0)}]") == "a[1]b[2]"
    assert vregex.delete_all(r"\d", "a1b2") == "ab"
    assert vregex.delete_first(r"\d", "a1b2") == "ab2"


def test_groups() -> None:
    assert vregex.get_group(r"(\d+)-(\d+)", "id 12-34", 1) == "12"
    assert vregex.get_group(r"(\d+)-(\d+)", "id 12-34", 2) == "34"
    assert vregex.get_group_by_name(r"(?P<year>\d{4})", "y2026", "year") == "2026"
    assert vregex.find_all_group(r"(\d)(\w)", "1a2b", 2) == ["a", "b"]
    assert vregex.named_groups(r"(?P<k>\w+)=(?P<v>\d+)", "x=1") == {"k": "x", "v": "1"}


def test_first_number_and_escape() -> None:
    assert vregex.get_first_number("order #123 of 456") == 123
    assert vregex.get_first_number("no digits") is None
    assert vregex.escape("a.b*c") == r"a\.b\*c"
