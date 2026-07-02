from kniferpy import vver


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
