from __future__ import annotations

from kniferpy.internal import netx

__all__ = [
    "PORT_RANGE_MAX",
    "is_ip",
    "is_ipv4",
    "is_ipv6",
    "is_inner_ip",
    "ipv4_to_long",
    "ipv4_to_long_default",
    "long_to_ipv4",
    "ipv6_to_int",
    "int_to_ipv6",
    "is_in_range",
    "first_ip",
    "last_ip",
    "address_count",
    "matches_wildcard",
    "hide_ip_part",
    "hide_ip_part_long",
    "is_valid_port",
]

PORT_RANGE_MAX = netx.PORT_RANGE_MAX


def is_ip(value: str) -> bool:
    return netx.is_ip(value)


def is_ipv4(value: str) -> bool:
    return netx.is_ipv4(value)


def is_ipv6(value: str) -> bool:
    return netx.is_ipv6(value)


def is_inner_ip(value: str) -> bool:
    return netx.is_inner_ip(value)


def ipv4_to_long(value: str) -> int:
    return netx.ipv4_to_long(value)


def ipv4_to_long_default(value: str, default: int = 0) -> int:
    return netx.ipv4_to_long_default(value, default)


def long_to_ipv4(value: int) -> str:
    return netx.long_to_ipv4(value)


def ipv6_to_int(value: str) -> int:
    return netx.ipv6_to_int(value)


def int_to_ipv6(value: int) -> str:
    return netx.int_to_ipv6(value)


def is_in_range(value: str, cidr: str) -> bool:
    return netx.is_in_range(value, cidr)


def first_ip(cidr: str) -> str:
    return netx.first_ip(cidr)


def last_ip(cidr: str) -> str:
    return netx.last_ip(cidr)


def address_count(cidr: str) -> int:
    return netx.address_count(cidr)


def matches_wildcard(wildcard: str, value: str) -> bool:
    return netx.matches_wildcard(wildcard, value)


def hide_ip_part(value: str) -> str:
    return netx.hide_ip_part(value)


def hide_ip_part_long(value: int) -> str:
    return netx.hide_ip_part_long(value)


def is_valid_port(port: int) -> bool:
    return netx.is_valid_port(port)
