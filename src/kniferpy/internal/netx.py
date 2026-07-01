from __future__ import annotations

import ipaddress

from kniferpy.verr import ValidationError

PORT_RANGE_MAX = 0xFFFF
IPV4_MAX = 0xFFFFFFFF
IPV6_MAX = (1 << 128) - 1


def _parse(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def is_ip(value: str) -> bool:
    return _parse(value) is not None


def is_ipv4(value: str) -> bool:
    return isinstance(_parse(value), ipaddress.IPv4Address)


def is_ipv6(value: str) -> bool:
    return isinstance(_parse(value), ipaddress.IPv6Address)


def is_inner_ip(value: str) -> bool:
    ip = _parse(value)
    if ip is None:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


def ipv4_to_long(value: str) -> int:
    ip = _parse(value)
    if not isinstance(ip, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid IPv4 address: {value}",
            code="knifer.net.invalid_ipv4",
            context={"value": value},
        )
    return int(ip)


def ipv4_to_long_default(value: str, default: int = 0) -> int:
    try:
        return ipv4_to_long(value)
    except ValidationError:
        return default


def long_to_ipv4(value: int) -> str:
    if value < 0 or value > IPV4_MAX:
        raise ValidationError(
            message=f"IPv4 integer out of range: {value}",
            code="knifer.net.ipv4_out_of_range",
            context={"value": value},
        )
    return str(ipaddress.IPv4Address(value))


def ipv6_to_int(value: str) -> int:
    ip = _parse(value)
    if not isinstance(ip, ipaddress.IPv6Address):
        raise ValidationError(
            message=f"invalid IPv6 address: {value}",
            code="knifer.net.invalid_ipv6",
            context={"value": value},
        )
    return int(ip)


def int_to_ipv6(value: int) -> str:
    if value < 0 or value > IPV6_MAX:
        raise ValidationError(
            message=f"IPv6 integer out of range: {value}",
            code="knifer.net.ipv6_out_of_range",
            context={"value": value},
        )
    return str(ipaddress.IPv6Address(value))


def _network(cidr: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        return ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError:
        return None


def is_in_range(value: str, cidr: str) -> bool:
    ip = _parse(value)
    network = _network(cidr)
    if ip is None or network is None:
        return False
    if ip.version != network.version:
        return False
    return ip in network


def first_ip(cidr: str) -> str:
    network = _network(cidr)
    if network is None:
        raise ValidationError(
            message=f"invalid CIDR: {cidr}",
            code="knifer.net.invalid_cidr",
            context={"cidr": cidr},
        )
    return str(network.network_address)


def last_ip(cidr: str) -> str:
    network = _network(cidr)
    if network is None:
        raise ValidationError(
            message=f"invalid CIDR: {cidr}",
            code="knifer.net.invalid_cidr",
            context={"cidr": cidr},
        )
    return str(network.broadcast_address)


def address_count(cidr: str) -> int:
    network = _network(cidr)
    if network is None:
        raise ValidationError(
            message=f"invalid CIDR: {cidr}",
            code="knifer.net.invalid_cidr",
            context={"cidr": cidr},
        )
    return network.num_addresses


def matches_wildcard(wildcard: str, value: str) -> bool:
    ip = _parse(value)
    if not isinstance(ip, ipaddress.IPv4Address):
        return False
    octets = str(ip).split(".")
    patterns = wildcard.split(".")
    if len(patterns) != 4:
        return False
    for pattern, octet in zip(patterns, octets, strict=True):
        if pattern == "*":
            continue
        if not pattern.isdigit() or not 0 <= int(pattern) <= 255:
            return False
        if int(pattern) != int(octet):
            return False
    return True


def hide_ip_part(value: str) -> str:
    index = value.rfind(".")
    if index < 0:
        return value
    return value[: index + 1] + "*"


def hide_ip_part_long(value: int) -> str:
    return hide_ip_part(long_to_ipv4(value))


def is_valid_port(port: int) -> bool:
    return 0 <= port <= PORT_RANGE_MAX
