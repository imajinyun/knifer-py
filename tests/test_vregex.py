import pytest

from kniferpy import vregex


def test_match_and_find() -> None:
    assert vregex.match(r"\d+", "abc123")
    assert not vregex.match(r"\d+", "abc")
    assert vregex.is_match(r"[a-z]+", "abc")
    assert not vregex.is_match(r"[a-z]+", "abc123")
    assert vregex.find(r"\d+", "a12b34") == "12"
    assert vregex.find_all(r"\d+", "a12b34") == ["12", "34"]
    assert vregex.count(r"\d+", "a12b34") == 2


def test_match_no_match() -> None:
    assert not vregex.match(r"\d+", "abc")
    assert not vregex.match(r"\d+", "")


def test_is_match_anchored() -> None:
    assert vregex.is_match(r"\d+", "123")
    assert not vregex.is_match(r"\d+", "123abc")


def test_find_no_match() -> None:
    assert vregex.find(r"\d+", "abc") == ""


def test_find_all_no_match() -> None:
    assert vregex.find_all(r"\d+", "abc") == []


def test_count_no_match() -> None:
    assert vregex.count(r"\d+", "abc") == 0


def test_count_multiple() -> None:
    assert vregex.count(r"the", "the cat and the dog") == 2


def test_invalid_pattern_is_safe() -> None:
    assert vregex.match(r"(", "anything") is False
    assert vregex.find(r"(", "anything") == ""
    assert vregex.find_all(r"(", "anything") == []
    assert vregex.replace(r"(", "keep", "x") == "keep"
    assert vregex.count(r"(", "anything") == 0
    assert vregex.is_match(r"(", "anything") is False


def test_replace_and_delete() -> None:
    assert vregex.replace(r"\d", "a1b2", "*") == "a*b*"
    assert vregex.replace_first(r"\d", "a1b2", "*") == "a*b2"
    assert vregex.replace_func(r"\d", "a1b2", lambda m: f"[{m.group(0)}]") == "a[1]b[2]"
    assert vregex.delete_all(r"\d", "a1b2") == "ab"
    assert vregex.delete_first(r"\d", "a1b2") == "ab2"


def test_replace_no_match() -> None:
    assert vregex.replace(r"\d+", "abc", "*") == "abc"


def test_replace_first_no_match() -> None:
    assert vregex.replace_first(r"\d+", "abc", "*") == "abc"


def test_delete_all_non_matching() -> None:
    assert vregex.delete_all(r"\d+", "abc") == "abc"


def test_delete_first_non_matching() -> None:
    assert vregex.delete_first(r"\d+", "abc") == "abc"


def test_replace_func_no_match() -> None:
    assert vregex.replace_func(r"\d+", "abc", lambda m: "x") == "abc"


def test_groups() -> None:
    assert vregex.get_group(r"(\d+)-(\d+)", "id 12-34", 1) == "12"
    assert vregex.get_group(r"(\d+)-(\d+)", "id 12-34", 2) == "34"
    assert vregex.get_group_by_name(r"(?P<year>\d{4})", "y2026", "year") == "2026"
    assert vregex.find_all_group(r"(\d)(\w)", "1a2b", 2) == ["a", "b"]
    assert vregex.named_groups(r"(?P<k>\w+)=(?P<v>\d+)", "x=1") == {"k": "x", "v": "1"}


def test_get_group_no_match() -> None:
    assert vregex.get_group(r"(\d+)", "abc", 0) == ""
    assert vregex.get_group(r"(\d+)", "abc", 1) == ""


def test_get_group_out_of_range() -> None:
    assert vregex.get_group(r"(\d+)", "123", 99) == ""


def test_get_group_by_name_no_match() -> None:
    assert vregex.get_group_by_name(r"(?P<year>\d{4})", "abc", "year") == ""


def test_get_group_by_name_invalid() -> None:
    assert vregex.get_group_by_name(r"(\d{4})", "2026", "year") == ""


def test_find_all_group_no_match() -> None:
    assert vregex.find_all_group(r"(\d)(\w)", "abc", 1) == []


def test_named_groups_no_match() -> None:
    assert vregex.named_groups(r"(?P<k>\w+)=(?P<v>\d+)", "abc") == {}


def test_named_groups_invalid_pattern() -> None:
    assert vregex.named_groups(r"(", "abc") == {}


def test_first_number_and_escape() -> None:
    assert vregex.get_first_number("order #123 of 456") == 123
    assert vregex.get_first_number("no digits") is None
    assert vregex.escape("a.b*c") == r"a\.b\*c"


def test_get_first_number_zero() -> None:
    assert vregex.get_first_number("0 items") == 0


def test_get_first_number_negative() -> None:
    # Only extracts digits, not the minus sign
    assert vregex.get_first_number("-123") == 123


def test_escape_special_chars() -> None:
    assert vregex.escape("a(b)c") == r"a\(b\)c"
    assert vregex.escape("a+b?c") == r"a\+b\?c"
    assert vregex.escape("a.b*c") == r"a\.b\*c"