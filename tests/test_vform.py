from kniferpy import vform


def test_is_email() -> None:
    assert vform.is_email("a@b.com")
    assert not vform.is_email("abc")


def test_is_mobile() -> None:
    assert vform.is_mobile("13812345678")
    assert not vform.is_mobile("12812345678")


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


def test_is_chinese() -> None:
    assert vform.is_chinese("你好")
    assert not vform.is_chinese("hello")
    assert not vform.is_chinese("")


def test_is_number_str() -> None:
    assert vform.is_number_str("-3.14")
    assert vform.is_number_str("42")
    assert not vform.is_number_str("ab")
    assert not vform.is_number_str("3.")
