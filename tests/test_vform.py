from kniferpy import vform


def test_is_email() -> None:
    assert vform.is_email("a@b.com")
    assert not vform.is_email("abc")


def test_is_email_with_options() -> None:
    assert vform.is_email_with_options("a@b.com")


def test_is_mobile() -> None:
    assert vform.is_mobile("13812345678")
    assert not vform.is_mobile("12812345678")


def test_is_mobile_with_options() -> None:
    assert vform.is_mobile_with_options("13812345678")


def test_is_url() -> None:
    assert vform.is_url("https://example.com")
    assert vform.is_url("ftp://x")
    assert not vform.is_url("/relative/path")
    assert not vform.is_url(" https://example.com")
    assert not vform.is_url("")


def test_is_ipv4() -> None:
    assert vform.is_ipv4("127.0.0.1")
    assert not vform.is_ipv4("256.0.0.1")


def test_is_ipv6() -> None:
    assert vform.is_ipv6("2001:db8::1")
    assert not vform.is_ipv6("127.0.0.1")
    assert not vform.is_ipv6("bad")


def test_is_id_card() -> None:
    assert vform.is_id_card("11010519491231002X")
    assert not vform.is_id_card("110105194912310021")


def test_is_id_card_with_options() -> None:
    assert vform.is_id_card_with_options("11010519491231002X")


def test_is_chinese() -> None:
    assert vform.is_chinese("你好")
    assert not vform.is_chinese("hello")
    assert not vform.is_chinese("")


def test_is_chinese_with_options() -> None:
    assert vform.is_chinese_with_options("你好")


def test_is_number_str() -> None:
    assert vform.is_number_str("-3.14")
    assert vform.is_number_str("42")
    assert not vform.is_number_str("ab")
    assert not vform.is_number_str("3.")


def test_is_number_str_with_options() -> None:
    assert vform.is_number_str_with_options("-3.14")


def test_with_email_matcher_custom() -> None:
    def custom_matcher(s: str) -> bool:
        return "@" in s
    assert vform.is_email_with_options("a@b", vform.with_email_matcher(custom_matcher))
    assert not vform.is_email_with_options("a@b", vform.with_email_matcher(lambda s: "x" in s))


def test_with_number_matcher_custom() -> None:
    def hex_matcher(s: str) -> bool:
        return all(c in "0123456789abcdefABCDEF" for c in s)
    assert vform.is_number_str_with_options("1af", vform.with_number_matcher(hex_matcher))
    assert not vform.is_number_str_with_options("1xz", vform.with_number_matcher(hex_matcher))


def test_with_mobile_matcher_custom() -> None:
    def any_matcher(s: str) -> bool:
        return len(s) == 11
    assert vform.is_mobile_with_options("12345678901", vform.with_mobile_matcher(any_matcher))


def test_with_id_card_matcher_custom() -> None:
    def any_matcher(s: str) -> bool:
        return len(s) == 18
    assert vform.is_id_card_with_options("123456789012345678", vform.with_id_card_matcher(any_matcher))


def test_with_chinese_matcher_custom() -> None:
    def any_matcher(s: str) -> bool:
        return "中" in s
    assert vform.is_chinese_with_options("中文", vform.with_chinese_matcher(any_matcher))
