import pytest

from kniferpy import vmask


def test_hide_and_first_mask() -> None:
    assert vmask.hide("abcdef", 1, 4) == "a***ef"
    assert vmask.hide("abc", -1, 99) == "***"
    assert vmask.first_mask("secret") == "s*****"
    assert vmask.first_mask("  ") == ""


def test_hide_edge_cases() -> None:
    assert vmask.hide("", 0, 0) == ""
    assert vmask.hide("ab", 0, 0) == "ab"
    assert vmask.hide("ab", 1, 1) == "ab"
    assert vmask.hide("ab", 0, 2) == "**"
    assert vmask.hide("测试", 0, 2) == "**"


def test_personal_identifiers() -> None:
    assert vmask.chinese_name("张三丰") == "张**"
    assert vmask.chinese_name("") == ""
    assert vmask.mobile_phone("13812345678") == "138****5678"
    assert vmask.mobile_phone("") == ""
    assert vmask.fixed_phone("01012345678") == "0101*****78"
    assert vmask.fixed_phone("") == ""
    assert vmask.id_card("110101199003074512", 6, 4) == "110101********4512"
    assert vmask.id_card("", 6, 4) == ""
    assert vmask.email("someone@example.com") == "s******@example.com"
    assert vmask.email("") == ""
    assert vmask.password("hunter2") == "*******"
    assert vmask.password("") == ""


def test_email_short_local_part() -> None:
    assert vmask.email("a@b.com") == "a@b.com"


def test_email_no_at() -> None:
    assert vmask.email("noatsign") == "noatsign"


def test_id_card_invalid_params() -> None:
    # front + end > length returns empty
    assert vmask.id_card("123456", 4, 4) == ""


def test_financial_and_network() -> None:
    assert vmask.bank_card("6222021234567890123") == "6222 **** **** **** 123"
    assert vmask.ipv4("192.168.0.1") == "192.*.*.*"
    assert vmask.ipv6("2001:db8::1") == "2001:*:*:*:*:*:*:*:*"
    assert vmask.passport("E12345678") == "E1*****78"
    assert vmask.credit_code("91350100M000100Y43") == "9135**********0Y43"


def test_bank_card_short() -> None:
    assert vmask.bank_card("12345678") == "12345678"


def test_bank_card_empty() -> None:
    assert vmask.bank_card("") == ""


def test_bank_card_with_spaces() -> None:
    result = vmask.bank_card("6222 0212 3456 7890 123")
    assert "****" in result


def test_ipv4_no_dot() -> None:
    assert vmask.ipv4("192") == "192.*.*.*"


def test_ipv6_no_colon() -> None:
    assert vmask.ipv6("2001") == "2001:*:*:*:*:*:*:*:*"


def test_passport_short() -> None:
    assert vmask.passport("AB") == "**"


def test_passport_empty() -> None:
    assert vmask.passport("") == ""


def test_credit_code_short() -> None:
    assert vmask.credit_code("ABC") == "***"


def test_credit_code_empty() -> None:
    assert vmask.credit_code("") == ""


def test_car_license_and_address() -> None:
    assert vmask.car_license("京A12345") == "京A1***5"
    assert vmask.car_license("京A123456") == "京A1****6"
    assert vmask.address("北京市海淀区中关村大街1号", 4) == "北京市海淀区中关村****"
    assert vmask.clear() == ""


def test_car_license_unknown_length() -> None:
    assert vmask.car_license("ABC") == "ABC"


def test_car_license_empty() -> None:
    assert vmask.car_license("") == ""


def test_address_empty() -> None:
    assert vmask.address("", 4) == ""