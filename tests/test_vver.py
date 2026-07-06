from kniferpy import vver
from kniferpy.internal import verx


def _sign(n: int) -> int:
    return (n > 0) - (n < 0)


def test_compare_version() -> None:
    cases = [
        ("", "v1", -1),
        ("v1", "v1", 0),
        ("v1", "", 1),
        ("1.0.0", "1.0.2", -1),
        ("1.0.2", "1.0.2a", -1),
        ("1.0.3", "1.0.2a", 1),
        ("1.0a", "1.0.1", 1),
        ("1.0.1", "1.0a", -1),
        ("1.13.0", "1.12.1c", 1),
        ("V0.0.20170102", "V0.0.20170101", 1),
        ("1.0.0", "1.0", 0),
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0+2", "1.0.0+1", 1),
    ]
    for left, right, want in cases:
        assert _sign(vver.compare_version(left, right)) == want, (left, right)


def test_comparison_helpers() -> None:
    assert vver.is_greater_than("1.0.3", "1.0.2")
    assert vver.is_greater_than_or_equal("1.0.2", "1.0.2")
    assert vver.is_less_than("1.0.1", "1.0.2")
    assert vver.is_less_than_or_equal("1.0.2", "1.0.2")
    assert not vver.is_greater_than("1.0.1", "1.0.2")
    assert not vver.is_less_than("1.0.3", "1.0.2")


def test_match_el() -> None:
    cases = [
        ("1.0.2", ">=1.0.2", True),
        ("1.0.2", "\u22651.0.2", True),
        ("1.0.2", "<1.0.1;1.0.2", True),
        ("1.0.2", "<1.0.2", False),
        ("1.0.2", "<=1.0.2", True),
        ("1.0.2", "\u22641.0.2", True),
        ("1.0.2", "1.0.0-1.1.1", True),
        ("1.0.2", "1.0.3-1.1.1", False),
        ("1.0.2", "-1.0.2", True),
        ("1.0.2", "1.0.2-", True),
        ("1.0.2", "", False),
    ]
    for current, expr, want in cases:
        assert vver.match_el(current, expr) is want, (current, expr)


def test_match_el_with_delimiter_and_any_match() -> None:
    assert vver.match_el_with_delimiter("1.0.2", "<1.0.1,1.0.2", ",")
    assert vver.match_el_with_delimiter("1.0.2", "1.0.1,1.0.2-1.1.1", ",")
    # "-" is an invalid delimiter and must fail closed.
    assert not vver.match_el_with_delimiter("1.0.2", ">1.0.0", "-")
    assert vver.any_match("1.0.2", "<1.0.1", "1.0.2")
    assert vver.any_match_slice("1.0.2", ["<1.0.1", "1.0.2"])


def test_null_comparison_expression() -> None:
    assert vver.match_el("1.0.0", ">null")


def test_parse_version_tokens_and_edges() -> None:
    empty = verx.parse_version("")
    parsed = verx.parse_version("v1.02-alpha.1+build.05")
    trailing_dash = verx.parse_version("1.0-")
    trailing_plus = verx.parse_version("1.0+")

    assert empty.sequence == []
    assert parsed.sequence[0].number is True
    assert parsed.sequence[0].num == str(ord("v") - ord("0"))
    assert [token.num or token.text for token in parsed.sequence][1:] == ["1", "2"]
    assert [token.text for token in parsed.pre] == ["alpha", "1"]
    assert [token.text for token in parsed.build] == ["build", "5"]
    assert trailing_dash.pre == []
    assert trailing_plus.build == []
    assert verx._normalize_number("-000") == "0"
    assert verx._normalize_number("-001") == "-1"


def test_compare_number_string_and_zero_rest() -> None:
    assert verx._compare_number_string("-2", "1") < 0
    assert verx._compare_number_string("-10", "-2") < 0
    assert vver.compare_version("1.0.0.0", "1") == 0
    assert vver.compare_version("1.0.0.1", "1") > 0


def test_match_el_invalid_delimiters_and_error_tuple() -> None:
    assert not vver.match_el_with_delimiter("1.0.0", ">=1.0.0", "")
    assert not vver.match_el_with_delimiter("1.0.0", ">=1.0.0", ">")
    assert not vver.match_el_with_delimiter("1.0.0", ">=1.0.0", "-")
    assert vver.match_el_with_delimiter("1.0.0", ">=1.0.0|<0.9", "|")
    assert vver.match_el_by_delimiter("1.0.0", "0.9|1.0.0", "|")
    assert vver.match_el_with_delimiter_err("1.0.0", "", ";") == (False, None)
    matched, err = vver.match_el_with_delimiter_err("1.0.0", ">=1.0.0", "-")
    assert matched is False
    assert err is not None


def test_unicode_comparison_operators_and_open_ranges() -> None:
    assert vver.match_el("1.0.0", "≥=1.0.0")
    assert vver.match_el("1.0.0", "≤=1.0.0")
    assert vver.match_el("1.0.0", "≤1.0.0")
    assert not vver.match_el("1.0.1", "≤1.0.0")
    assert vver.match_el("1.0.0", "1.0.0-")
    assert vver.match_el("0.9.0", "-1.0.0")
    assert not vver.match_el("2.0.0", "-1.0.0")


def test_internal_split_and_prefix_helpers() -> None:
    assert verx._compare_op_prefix("") == ""
    assert verx._compare_op_prefix(">=1") == ">="
    assert verx._compare_op_prefix(">1") == ">"
    assert verx._compare_op_prefix("=1") == ""
    assert verx._valid_delimiter("|")
    assert not verx._valid_delimiter(" ")
    assert verx._split_expression(" a | | b ", "|") == ["a", "b"]
    assert verx._compare_nullable(None, None) == 0
    assert verx._compare_nullable(None, "1") < 0
    assert verx._compare_nullable("1", None) > 0
