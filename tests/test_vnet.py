import pytest

from kniferpy import vnet
from kniferpy.verr import ValidationError


def test_ip_type_detection() -> None:
    assert vnet.is_ip("127.0.0.1")
    assert vnet.is_ip("::1")
    assert not vnet.is_ip("not-an-ip")
    assert vnet.is_ipv4("192.168.0.1")
    assert not vnet.is_ipv4("::1")
    assert vnet.is_ipv6("2001:db8::1")
    assert not vnet.is_ipv6("192.168.0.1")


def test_inner_ip() -> None:
    assert vnet.is_inner_ip("127.0.0.1")
    assert vnet.is_inner_ip("10.0.0.1")
    assert vnet.is_inner_ip("192.168.1.1")
    assert vnet.is_inner_ip("169.254.1.1")
    assert vnet.is_inner_ip("::1")
    assert not vnet.is_inner_ip("8.8.8.8")
    assert not vnet.is_inner_ip("bad")


def test_ipv4_long_roundtrip() -> None:
    value = vnet.ipv4_to_long("1.2.3.4")
    assert value == 0x01020304
    assert vnet.long_to_ipv4(value) == "1.2.3.4"
    assert vnet.ipv4_to_long_default("bad", 42) == 42
    with pytest.raises(ValidationError):
        vnet.ipv4_to_long("999.1.1.1")
    with pytest.raises(ValidationError):
        vnet.long_to_ipv4(-1)


def test_ipv6_int_roundtrip() -> None:
    value = vnet.ipv6_to_int("::1")
    assert value == 1
    assert vnet.int_to_ipv6(value) == "::1"
    with pytest.raises(ValidationError):
        vnet.ipv6_to_int("192.168.0.1")


def test_cidr_range_and_membership() -> None:
    assert vnet.is_in_range("192.168.1.5", "192.168.1.0/24")
    assert not vnet.is_in_range("192.168.2.5", "192.168.1.0/24")
    assert not vnet.is_in_range("::1", "192.168.1.0/24")
    assert vnet.first_ip("192.168.1.0/24") == "192.168.1.0"
    assert vnet.last_ip("192.168.1.0/24") == "192.168.1.255"
    assert vnet.address_count("192.168.1.0/24") == 256
    with pytest.raises(ValidationError):
        vnet.first_ip("nope")


def test_wildcard_matching() -> None:
    assert vnet.matches_wildcard("192.168.*.*", "192.168.1.5")
    assert not vnet.matches_wildcard("192.168.*.*", "10.0.0.1")
    assert not vnet.matches_wildcard("192.168.*", "192.168.1.5")
    assert not vnet.matches_wildcard("192.168.1.5", "::1")


def test_hide_ip_part() -> None:
    assert vnet.hide_ip_part("1.2.3.4") == "1.2.3.*"
    assert vnet.hide_ip_part("no-dot") == "no-dot"
    assert vnet.hide_ip_part_long(0x01020304) == "1.2.3.*"


def test_valid_port() -> None:
    assert vnet.is_valid_port(0)
    assert vnet.is_valid_port(65535)
    assert not vnet.is_valid_port(-1)
    assert not vnet.is_valid_port(65536)
