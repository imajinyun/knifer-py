import re

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


# ========== New: GetGroup0 / GetGroup1 ==========


def test_get_group0() -> None:
    assert vregex.get_group0(r"\d+", "order 123") == "123"
    assert vregex.get_group0(r"\d+", "abc") == ""


def test_get_group1() -> None:
    assert vregex.get_group1(r"(\d+)-(\d+)", "id 12-34") == "12"
    assert vregex.get_group1(r"\d+", "abc") == ""


# ========== New: GetOK ==========


def test_get_ok() -> None:
    val, ok = vregex.get_ok(r"(\d+)-(\d+)", "id 12-34", 1)
    assert val == "12"
    assert ok is True


def test_get_ok_no_match() -> None:
    val, ok = vregex.get_ok(r"(\d+)", "abc", 0)
    assert val == ""
    assert ok is False


def test_get_ok_invalid_pattern() -> None:
    val, ok = vregex.get_ok(r"(", "anything", 0)
    assert val == ""
    assert ok is False


def test_get_ok_out_of_range() -> None:
    val, ok = vregex.get_ok(r"(\d+)", "123", 99)
    assert val == ""
    assert ok is False


# ========== New: FindAllGroup0 / FindAllGroup1 ==========


def test_find_all_group0() -> None:
    assert vregex.find_all_group0(r"\d+", "a1b23c") == ["1", "23"]


def test_find_all_group1() -> None:
    assert vregex.find_all_group1(r"(\d)(\w)", "1a2b3c") == ["1", "2", "3"]


# ========== New: DelLast / DelPre ==========


def test_del_last() -> None:
    assert vregex.del_last(r"\d+", "a1b2c3") == "a1b2c"
    assert vregex.del_last(r"\d+", "abc") == "abc"
    assert vregex.del_last(r"(", "abc") == "abc"


def test_del_pre() -> None:
    # DelPre deletes everything through the first match (including the match itself)
    assert vregex.del_pre(r"\d+", "aaa123bbb") == "bbb"
    assert vregex.del_pre(r"\d+", "abc") == "abc"
    assert vregex.del_pre(r"(", "abc") == "abc"


# ========== New: Contains ==========


def test_contains() -> None:
    assert vregex.contains(r"\d+", "abc123") is True
    assert vregex.contains(r"\d+", "abc") is False
    assert vregex.contains(r"(", "abc") is False


# ========== New: IndexOf / LastIndexOf ==========


def test_index_of() -> None:
    mr = vregex.index_of(r"\d+", "abc123def")
    assert mr is not None
    assert mr.text == "123"
    assert mr.start == 3
    assert mr.end == 6


def test_index_of_no_match() -> None:
    assert vregex.index_of(r"\d+", "abc") is None


def test_index_of_invalid_pattern() -> None:
    assert vregex.index_of(r"(", "abc") is None


def test_last_index_of() -> None:
    mr = vregex.last_index_of(r"\d+", "a1b2c3")
    assert mr is not None
    assert mr.text == "3"
    assert mr.start == 5
    assert mr.end == 6


def test_last_index_of_no_match() -> None:
    assert vregex.last_index_of(r"\d+", "abc") is None


# ========== New: GetAllGroups / GetAllGroupNames ==========


def test_get_all_groups() -> None:
    assert vregex.get_all_groups(
        r"(\d)(\w)", "1a 2b", with_group0=False, find_all=True
    ) == ["1", "a", "2", "b"]


def test_get_all_groups_with_group0() -> None:
    assert vregex.get_all_groups(
        r"(\d)(\w)", "1a 2b", with_group0=True, find_all=True
    ) == ["1a", "1", "a", "2b", "2", "b"]


def test_get_all_groups_no_match() -> None:
    assert vregex.get_all_groups(r"\d+", "abc") == []


def test_get_all_group_names() -> None:
    assert vregex.get_all_group_names(r"(?P<k>\w+)=(?P<v>\d+)", "x=1") == {"k": "x", "v": "1"}


def test_get_all_group_names_no_match() -> None:
    assert vregex.get_all_group_names(r"(?P<k>\d+)", "abc") == {}


# ========== New: ExtractMulti / ExtractMultiAndDelPre ==========


def test_extract_multi() -> None:
    assert vregex.extract_multi(r"(\d+)-(\w+)", "id 12-abc", "$2-$1") == "abc-12"


def test_extract_multi_no_match() -> None:
    assert vregex.extract_multi(r"\d+", "abc", "$1") == ""


def test_extract_multi_invalid_pattern() -> None:
    assert vregex.extract_multi(r"(", "abc", "$1") == ""


def test_extract_multi_and_del_pre() -> None:
    holder = ["12-abc 34-def"]
    result = vregex.extract_multi_and_del_pre(r"(\d+)-(\w+)", holder, "$2-$1")
    assert result == "abc-12"
    assert holder[0] == " 34-def"


def test_extract_multi_and_del_pre_no_match() -> None:
    holder = ["abc"]
    result = vregex.extract_multi_and_del_pre(r"\d+", holder, "$1")
    assert result == ""
    assert holder[0] == "abc"


# ========== New: TemplateVars ==========


def test_template_vars() -> None:
    assert vregex.template_vars("$1-$2-$1") == [2, 1]


def test_template_vars_empty() -> None:
    assert vregex.template_vars("no vars") == []


# ========== New: ReplaceAll / ReplaceAllFunc ==========


def test_replace_all() -> None:
    assert vregex.replace_all("hello 123 world 456", r"\d+", "[$0]") == "hello [123] world [456]"


def test_replace_all_no_match() -> None:
    assert vregex.replace_all("abc", r"\d+", "x") == "abc"


def test_replace_all_invalid_pattern() -> None:
    assert vregex.replace_all("abc", r"(", "x") == "abc"


def test_internal_match_result_fallback_and_none_branches() -> None:
    regex = re.compile(r"\d+")
    fallback = vregex.index_of_re(None, "abc")
    assert fallback is None
    assert vregex.last_index_of_re(None, "abc") is None
    assert vregex.get_all_groups_re(None, "abc", False, False) == []
    assert vregex.get_all_group_names_re(None) == []
    assert vregex.find_all_group_re(None, "abc", "x") == []
    assert vregex.del_last_re(None, "abc") == "abc"
    assert vregex.del_pre_re(None, "abc") == "abc"
    assert vregex.extract_multi_re(None, "abc", "$1") == "abc"
    assert vregex.extract_multi_and_del_pre_re(None, "abc", "$1") == "abc"
    assert vregex.replace_all_re(None, "abc", "x") == "abc"
    assert vregex.replace_all_func_re(None, "abc", lambda m: "x") == "abc"
    assert vregex.contains_re(None, "abc") is False
    assert vregex.count_re(None, "abc") == 0
    assert vregex.is_match_re(None, "abc") is False
    assert vregex.get_re(None, "abc", 0) == ""
    assert vregex.get_re_ok(None, "abc", 0) == ("", False)
    assert vregex.get_by_name_re(None, "abc", "x") == ""
    assert vregex.get_by_name_re(regex, "abc", "") == ""


def test_precompiled_regex_helpers() -> None:
    regex = re.compile(r"(?P<num>\d+)-(?P<word>\w+)")

    assert vregex.contains_re(regex, "id 12-abc")
    assert vregex.count_re(regex, "12-a 34-b") == 2
    assert vregex.is_match_re(regex, "12-abc")
    assert not vregex.is_match_re(regex, "id 12-abc")
    assert vregex.get_re(regex, "id 12-abc", 0) == "12-abc"
    assert vregex.get_re(regex, "id 12-abc", 2) == "abc"
    assert vregex.get_re(regex, "id 12-abc", 9) == ""
    assert vregex.get_by_name_re(regex, "id 12-abc", "word") == "abc"
    assert vregex.get_by_name_re(regex, "id 12-abc", "missing") == ""
    assert vregex.get_all_group_names_re(regex) == ["num", "word"]
    assert vregex.find_all_group_re(regex, "12-a 34-b", "word") == ["a", "b"]
    assert vregex.find_all_group_re(regex, "12-a", "missing") == []
    assert vregex.del_all_re(regex, "12-a x 34-b") == " x "
    assert vregex.del_first_re(regex, "12-a x 34-b") == " x 34-b"
    assert vregex.replace_first_re(regex, "12-a x 34-b", r"\g<word>") == "a x 34-b"
    assert vregex.replace_all_re(regex, "12-a 34-b", r"\g<word>") == "a b"
    assert vregex.replace_all_func_re(regex, "12-a", lambda m: m.group("word").upper()) == "A"


def test_compiled_delete_extract_variants_and_empty_content() -> None:
    regex = re.compile(r"(\d+)-(\w+)")

    assert vregex.del_last_re(regex, "12-a 34-b") == "12-a "
    assert vregex.del_last_re(regex, "abc") == "abc"
    assert vregex.del_last_re(regex, "") == ""
    assert vregex.del_pre_re(regex, "xx 12-a yy") == "xx "
    assert vregex.del_pre_re(regex, "abc") == "abc"
    assert vregex.del_pre_re(regex, "") == ""
    assert vregex.extract_multi_re(regex, "12-a", r"\2-\1") == "a-12"
    assert vregex.extract_multi_re(regex, "", r"\2") == ""
    assert vregex.extract_multi_and_del_pre_re(regex, "xx 12-a yy", r"\2") == "a yy"
    assert vregex.extract_multi_and_del_pre_re(regex, "abc", r"\2") == "abc"
    assert vregex.extract_multi_and_del_pre_re(regex, "", r"\2") == ""
    assert vregex.replace_all_re(regex, "", "x") == ""
    assert vregex.replace_all_func_re(regex, "", lambda m: "x") == ""


def test_each_first_escape_and_number_ok() -> None:
    regex = re.compile(r"(?P<num>\d+)")
    each_seen: list[str] = []
    first_seen: list[str] = []

    vregex.each(regex, "a1b22", lambda mr: each_seen.append(mr.text))
    vregex.first(regex, "a1b22", lambda mr: first_seen.append(mr.group_names["num"]))
    vregex.each(None, "a1", lambda mr: each_seen.append("bad"))
    vregex.each(regex, "a1", None)
    vregex.first(None, "a1", lambda mr: first_seen.append("bad"))
    vregex.first(regex, "a1", None)

    assert each_seen == ["1", "22"]
    assert first_seen == ["1"]
    assert vregex.escape_char(".") == r"\."
    assert vregex.escape_char("ab") == "ab"
    assert vregex.escape_char("x") == "x"
    assert vregex.get_first_number_ok("id 123") == (123, True)
    assert vregex.get_first_number_ok("none") == (0, False)


def test_replace_all_func() -> None:
    result = vregex.replace_all_func("a1b2c", r"\d", lambda mr: f"[{mr.text}]")
    assert result == "a[1]b[2]c"


def test_replace_all_func_no_match() -> None:
    assert vregex.replace_all_func("abc", r"\d+", lambda mr: "x") == "abc"


# ========== New: EscapeChar ==========


def test_escape_char() -> None:
    assert vregex.escape_char(".") == "\\."
    assert vregex.escape_char("*") == "\\*"
    assert vregex.escape_char("a") == "a"
    assert vregex.escape_char("$") == "\\$"
    assert vregex.escape_char("") == ""


# ========== New: GetFirstNumberOK ==========


def test_get_first_number_ok() -> None:
    val, ok = vregex.get_first_number_ok("order #123")
    assert val == 123
    assert ok is True


def test_get_first_number_ok_no_digits() -> None:
    val, ok = vregex.get_first_number_ok("no digits")
    assert val == 0
    assert ok is False


# ========== New: Constants ==========


def test_re_chinese_constants() -> None:
    assert vregex.RE_CHINESE == r"\p{Han}"
    assert vregex.RE_CHINESES == r"^\p{Han}+$"


# ========== New: Pre-compiled regex helpers ==========


def test_contains_re() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    assert vregex.contains_re(r, "abc123") is True
    assert vregex.contains_re(r, "abc") is False


def test_count_re() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    assert vregex.count_re(r, "a1b2c3") == 3
    assert vregex.count_re(r, "abc") == 0


def test_is_match_re() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    assert vregex.is_match_re(r, "123") is True
    assert vregex.is_match_re(r, "123abc") is False


def test_get_re() -> None:
    import re as _re
    r = _re.compile(r"(\d+)-(\w+)")
    assert vregex.get_re(r, "id 12-abc", 1) == "12"
    assert vregex.get_re(r, "id 12-abc", 2) == "abc"


def test_get_re_ok() -> None:
    import re as _re
    r = _re.compile(r"(\d+)-(\w+)")
    val, ok = vregex.get_re_ok(r, "id 12-abc", 1)
    assert val == "12"
    assert ok is True


def test_get_by_name_re() -> None:
    import re as _re
    r = _re.compile(r"(?P<year>\d{4})")
    assert vregex.get_by_name_re(r, "y2026", "year") == "2026"


def test_del_all_re() -> None:
    import re as _re
    r = _re.compile(r"\d")
    assert vregex.del_all_re(r, "a1b2c") == "abc"


def test_del_first_re() -> None:
    import re as _re
    r = _re.compile(r"\d")
    assert vregex.del_first_re(r, "a1b2c") == "ab2c"


def test_replace_first_re() -> None:
    import re as _re
    r = _re.compile(r"\d")
    assert vregex.replace_first_re(r, "a1b2c", "*") == "a*b2c"


# ========== New: Each / First ==========


def test_each() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    results: list[vregex.MatchResult] = []
    vregex.each(r, "a1b23c", lambda mr: results.append(mr))
    assert len(results) == 2
    assert results[0].text == "1"
    assert results[1].text == "23"


def test_each_with_groups() -> None:
    import re as _re
    r = _re.compile(r"(\d+)-(\w+)")
    results: list[vregex.MatchResult] = []
    vregex.each(r, "12-abc 34-def", lambda mr: results.append(mr))
    assert len(results) == 2
    assert results[0].groups == ["12-abc", "12", "abc"]
    assert results[1].groups == ["34-def", "34", "def"]


def test_each_nil() -> None:
    results: list[vregex.MatchResult] = []
    vregex.each(None, "abc", lambda mr: results.append(mr))  # type: ignore[arg-type]
    assert results == []


def test_first() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    results: list[vregex.MatchResult] = []
    vregex.first(r, "a1b23c", lambda mr: results.append(mr))
    assert len(results) == 1
    assert results[0].text == "1"


def test_first_no_match() -> None:
    import re as _re
    r = _re.compile(r"\d+")
    results: list[vregex.MatchResult] = []
    vregex.first(r, "abc", lambda mr: results.append(mr))
    assert results == []
