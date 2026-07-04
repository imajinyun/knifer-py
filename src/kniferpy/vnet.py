from __future__ import annotations

import socket
import ssl

from kniferpy.internal import netx
from kniferpy.internal.netx import (
    LocalPortGenerator,
    MultipartFormData,
    TLSConfigBuilder,
    UploadSetting,
)

__all__ = [
    # Constants
    "LOCAL_IP",
    "IP_SPLIT_MARK",
    "IP_MASK_SPLIT_MARK",
    "IP_MASK_MAX",
    "PORT_RANGE_MIN",
    "PORT_RANGE_MAX",
    # Types
    "TLSConfigBuilder",
    "MultipartFormData",
    "UploadSetting",
    "LocalPortGenerator",
    # IP validation
    "is_ip",
    "is_ipv4",
    "is_ipv6",
    "is_inner_ip",
    # IP conversion
    "ipv4_to_long",
    "ipv4_to_long_default",
    "long_to_ipv4",
    "ipv6_to_int",
    "int_to_ipv6",
    # IP range
    "is_in_range",
    "first_ip",
    "last_ip",
    "address_count",
    "matches_wildcard",
    "hide_ip_part",
    "hide_ip_part_long",
    # Port
    "is_valid_port",
    "is_usable_local_port",
    "get_usable_local_port",
    "get_usable_local_port_from",
    "get_usable_local_port_in_range",
    "get_usable_local_ports",
    "new_local_port_generator",
    # Subnet math
    "mask_bit_by_mask",
    "count_by_mask_bit",
    "mask_by_mask_bit",
    "mask_by_ip_range",
    "count_by_ip_range",
    "format_ip_block",
    "begin_ip",
    "begin_ip_long",
    "end_ip",
    "end_ip_long",
    "is_mask_valid",
    "is_mask_bit_valid",
    "list_ips",
    "list_ip_cidr",
    "list_ip_range",
    # TLS
    "new_tls_config_builder",
    "create_tls_config",
    "tls_version",
    "new_cert_pool",
    "add_root_ca_bytes",
    # DNS
    "get_dns_info",
    "get_ip_by_host",
    "idn_to_ascii",
    # TCP
    "ping",
    "is_open",
    "connect",
    "is_connected",
    "netcat",
    "get_remote_address",
    # Address
    "build_inet_socket_address",
    "create_address",
    # Local interface
    "get_network_interface",
    "get_network_interfaces",
    "local_ipv4s",
    "local_ipv6s",
    "local_ips",
    "to_ip_list",
    "local_address_list",
    "get_localhost_str",
    "get_localhost",
    "get_local_host_name",
    "get_local_mac_address",
    "get_mac_address",
    "get_hardware_address",
    "get_local_hardware_address",
    # Misc
    "is_unknown",
    "parse_cookies",
    "get_multistage_reverse_proxy_ip",
    # Multipart
    "parse_multipart_form",
    "save_uploaded_file",
    "upload_file_name",
    "upload_file_size",
    "upload_file_content_type",
]

LOCAL_IP = netx.LOCAL_IP
IP_SPLIT_MARK = netx.IP_SPLIT_MARK
IP_MASK_SPLIT_MARK = netx.IP_MASK_SPLIT_MARK
IP_MASK_MAX = netx.IP_MASK_MAX
PORT_RANGE_MIN = netx.PORT_RANGE_MIN
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


def is_usable_local_port(port: int) -> bool:
    return netx.is_usable_local_port(port)


def get_usable_local_port() -> int:
    return netx.get_usable_local_port()


def get_usable_local_port_from(min_port: int) -> int:
    return netx.get_usable_local_port_from(min_port)


def get_usable_local_port_in_range(min_port: int, max_port: int) -> int:
    return netx.get_usable_local_port_in_range(min_port, max_port)


def get_usable_local_ports(num_requested: int, min_port: int, max_port: int) -> list[int]:
    return netx.get_usable_local_ports(num_requested, min_port, max_port)


def new_local_port_generator(begin_port: int = PORT_RANGE_MIN) -> LocalPortGenerator:
    return netx.new_local_port_generator(begin_port)


# ---------------------------------------------------------------------------
# Subnet math
# ---------------------------------------------------------------------------


def mask_bit_by_mask(mask: str) -> int:
    return netx.mask_bit_by_mask(mask)


def count_by_mask_bit(mask_bit: int, is_all: bool = False) -> int:
    return netx.count_by_mask_bit(mask_bit, is_all)


def mask_by_mask_bit(mask_bit: int) -> str:
    return netx.mask_by_mask_bit(mask_bit)


def mask_by_ip_range(from_ip: str, to_ip: str) -> str:
    return netx.mask_by_ip_range(from_ip, to_ip)


def count_by_ip_range(from_ip: str, to_ip: str) -> int:
    return netx.count_by_ip_range(from_ip, to_ip)


def format_ip_block(ip: str, mask: str) -> str:
    return netx.format_ip_block(ip, mask)


def begin_ip(ip: str, mask_bit: int) -> str:
    return netx.begin_ip(ip, mask_bit)


def begin_ip_long(ip: str, mask_bit: int) -> int:
    return netx.begin_ip_long(ip, mask_bit)


def end_ip(ip: str, mask_bit: int) -> str:
    return netx.end_ip(ip, mask_bit)


def end_ip_long(ip: str, mask_bit: int) -> int:
    return netx.end_ip_long(ip, mask_bit)


def is_mask_valid(mask: str) -> bool:
    return netx.is_mask_valid(mask)


def is_mask_bit_valid(mask_bit: int) -> bool:
    return netx.is_mask_bit_valid(mask_bit)


def list_ips(ip_range: str, is_all: bool = False) -> list[str]:
    return netx.list_ips(ip_range, is_all)


def list_ip_cidr(ip: str, mask_bit: int, is_all: bool = False) -> list[str]:
    return netx.list_ip_cidr(ip, mask_bit, is_all)


def list_ip_range(from_ip: str, to_ip: str) -> list[str]:
    return netx.list_ip_range(from_ip, to_ip)


# ---------------------------------------------------------------------------
# TLS
# ---------------------------------------------------------------------------


def new_tls_config_builder() -> TLSConfigBuilder:
    return netx.new_tls_config_builder()


def create_tls_config() -> ssl.SSLContext:
    return netx.create_tls_config()


def tls_version(version: str) -> int:
    return netx.tls_version(version)


def new_cert_pool() -> ssl.SSLContext:
    return netx.new_cert_pool()


def add_root_ca_bytes(ssl_context: ssl.SSLContext, ca_data: bytes) -> None:
    return netx.add_root_ca_bytes(ssl_context, ca_data)


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------


def get_dns_info(host: str, types: list[str] | None = None) -> dict[str, list[str]]:
    return netx.get_dns_info(host, types)


def get_ip_by_host(host: str) -> list[str]:
    return netx.get_ip_by_host(host)


def idn_to_ascii(domain: str) -> str:
    return netx.idn_to_ascii(domain)


# ---------------------------------------------------------------------------
# TCP
# ---------------------------------------------------------------------------


def ping(host: str, port: int, timeout: float = 3.0) -> bool:
    return netx.ping(host, port, timeout)


def is_open(host: str, port: int, timeout: float = 3.0) -> bool:
    return netx.is_open(host, port, timeout)


def connect(host: str, port: int, timeout: float = 3.0) -> socket.socket | None:
    return netx.connect(host, port, timeout)


def is_connected(sock: socket.socket | None) -> bool:
    return netx.is_connected(sock)


def netcat(host: str, port: int, data: bytes, timeout: float = 3.0) -> None:
    return netx.netcat(host, port, data, timeout)


def get_remote_address(sock: socket.socket) -> str:
    return netx.get_remote_address(sock)


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


def build_inet_socket_address(host: str, default_port: int) -> tuple[str, int]:
    return netx.build_inet_socket_address(host, default_port)


def create_address(host: str, port: int) -> tuple[str, int]:
    return netx.create_address(host, port)


# ---------------------------------------------------------------------------
# Local interface
# ---------------------------------------------------------------------------


def get_network_interface(name: str) -> dict | None:
    return netx.get_network_interface(name)


def get_network_interfaces() -> dict:
    return netx.get_network_interfaces()


def local_ipv4s() -> list[str]:
    return netx.local_ipv4s()


def local_ipv6s() -> list[str]:
    return netx.local_ipv6s()


def local_ips() -> list[str]:
    return netx.local_ips()


def to_ip_list(address_list: list[str]) -> list[str]:
    return netx.to_ip_list(address_list)


def local_address_list(address_filter=None) -> list[str]:
    return netx.local_address_list(address_filter)


def get_localhost_str() -> str:
    return netx.get_localhost_str()


def get_localhost() -> str:
    return netx.get_localhost()


def get_local_host_name() -> str:
    return netx.get_local_host_name()


def get_local_mac_address(separator: str = "-") -> str:
    return netx.get_local_mac_address(separator)


def get_mac_address(inet_address: str, separator: str = "-") -> str:
    return netx.get_mac_address(inet_address, separator)


def get_hardware_address(inet_address: str) -> str:
    return netx.get_hardware_address(inet_address)


def get_local_hardware_address() -> str:
    return netx.get_local_hardware_address()


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def is_unknown(check_string: str) -> bool:
    return netx.is_unknown(check_string)


def parse_cookies(cookie_str: str) -> dict[str, str]:
    return netx.parse_cookies(cookie_str)


def get_multistage_reverse_proxy_ip(headers: dict[str, str]) -> str:
    return netx.get_multistage_reverse_proxy_ip(headers)


# ---------------------------------------------------------------------------
# Multipart
# ---------------------------------------------------------------------------


def parse_multipart_form(
    body: bytes,
    content_type: str,
    setting: UploadSetting | None = None,
) -> MultipartFormData:
    return netx.parse_multipart_form(body, content_type, setting)


def save_uploaded_file(
    file_entry: tuple[str, bytes, str],
    dest_dir: str,
    dest_name: str = "",
    overwrite: bool = False,
) -> str:
    return netx.save_uploaded_file(file_entry, dest_dir, dest_name, overwrite)


def upload_file_name(file_entry: tuple[str, bytes, str]) -> str:
    return netx.upload_file_name(file_entry)


def upload_file_size(file_entry: tuple[str, bytes, str]) -> int:
    return netx.upload_file_size(file_entry)


def upload_file_content_type(file_entry: tuple[str, bytes, str]) -> str:
    return netx.upload_file_content_type(file_entry)