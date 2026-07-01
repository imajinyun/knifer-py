from kniferpy import vmask


def test_hide_and_first_mask() -> None:
    assert vmask.hide("abcdef", 1, 4) == "a***ef"
    assert vmask.hide("abc", -1, 99) == "***"
    assert vmask.first_mask("secret") == "s*****"
    assert vmask.first_mask("  ") == ""


def test_personal_identifiers() -> None:
    assert vmask.chinese_name("张三丰") == "张**"
    assert vmask.mobile_phone("13812345678") == "138****5678"
    assert vmask.fixed_phone("01012345678") == "0101*****78"
    assert vmask.id_card("110101199003074512", 6, 4) == "110101********4512"
    assert vmask.email("someone@example.com") == "s******@example.com"
    assert vmask.password("hunter2") == "*******"


def test_financial_and_network() -> None:
    assert vmask.bank_card("6222021234567890123") == "6222 **** **** **** 123"
    assert vmask.ipv4("192.168.0.1") == "192.*.*.*"
    assert vmask.ipv6("2001:db8::1") == "2001:*:*:*:*:*:*:*:*"
    assert vmask.passport("E12345678") == "E1*****78"
    assert vmask.credit_code("91350100M000100Y43") == "9135**********0Y43"


def test_car_license_and_address() -> None:
    assert vmask.car_license("京A12345") == "京A1***5"
    assert vmask.address("北京市海淀区中关村大街1号", 4) == "北京市海淀区中关村****"
    assert vmask.clear() == ""
