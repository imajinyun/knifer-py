from __future__ import annotations

import socket
import ssl
from typing import Any, Callable

from kniferpy.internal import netx
from kniferpy.internal.netx import (
    LocalPortGenerator,
    MultipartFormData,
    TLSConfigBuilder,
    UploadSetting,
)

# ── Go-compat type aliases ─────────────────────────────────────────────────────

from typing import Any, Callable

Dialer = Any
ConnectOption = Callable[[Any], None]
PingOption = Callable[[Any], None]
ResolveOption = Callable[[Any], None]
AddressOption = Callable[[Any], None]
PortOption = Callable[[Any], None]
InterfaceOption = Callable[[Any], None]
TLSFileOption = Callable[[Any], None]
UploadSaveOption = Callable[[Any], None]
IPOption = Callable[[Any], None]
WildcardOption = Callable[[Any], None]
OpenUploadedFileFunc = Callable[[str], Any]

__all__ = [
    # Constants
    "LOCAL_IP",
    "IP_SPLIT_MARK",
    "IP_MASK_SPLIT_MARK",
    "IP_MASK_MAX",
    "PORT_RANGE_MIN",
    "PORT_RANGE_MAX",
    "SSL",
    "SSLv2",
    "SSLv3",
    "TLS",
    "TLSv1",
    "TLSv11",
    "TLSv12",
    "TLSv13",
    # Types
    "TLSConfigBuilder",
    "MultipartFormData",
    "UploadSetting",
    "LocalPortGenerator",
    # IP validation
    "is_ip",
    "is_ip_with_options",
    "is_ipv4",
    "is_ipv4_with_options",
    "is_ipv6",
    "is_ipv6_with_options",
    "is_inner_ip",
    "is_inner_ip_with_options",
    # IP conversion
    "ipv4_to_long",
    "ipv4_to_long_with_options",
    "ipv4_to_long_default",
    "ipv4_to_long_default_with_options",
    "long_to_ipv4",
    "ipv6_to_int",
    "ipv6_to_int_with_options",
    "int_to_ipv6",
    # IP range
    "is_in_range",
    "is_in_range_with_options",
    "first_ip",
    "last_ip",
    "address_count",
    "matches_wildcard",
    "matches_wildcard_with_options",
    "hide_ip_part",
    "hide_ip_part_long",
    # Port
    "is_valid_port",
    "is_usable_local_port",
    "is_usable_local_port_with_options",
    "get_usable_local_port",
    "get_usable_local_port_with_options",
    "get_usable_local_port_from",
    "get_usable_local_port_from_with_options",
    "get_usable_local_port_in_range",
    "get_usable_local_port_in_range_with_options",
    "get_usable_local_ports",
    "get_usable_local_ports_with_options",
    "new_local_port_generator",
    "new_local_port_generator_with_options",
    # Subnet math
    "mask_bit_by_mask",
    "mask_bit_by_mask_with_options",
    "count_by_mask_bit",
    "mask_by_mask_bit",
    "mask_by_ip_range",
    "mask_by_ip_range_with_options",
    "count_by_ip_range",
    "count_by_ip_range_with_options",
    "format_ip_block",
    "format_ip_block_with_options",
    "begin_ip",
    "begin_ip_with_options",
    "begin_ip_long",
    "begin_ip_long_with_options",
    "end_ip",
    "end_ip_with_options",
    "end_ip_long",
    "end_ip_long_with_options",
    "is_mask_valid",
    "is_mask_valid_with_options",
    "is_mask_bit_valid",
    "list_ips",
    "list_ips_with_options",
    "list_ip_cidr",
    "list_ip_cidr_with_options",
    "list_ip_range",
    "list_ip_range_with_options",
    # TLS
    "new_tls_config_builder",
    "create_tls_config",
    "tls_version",
    "new_cert_pool",
    "add_root_ca_bytes",
    # DNS
    "get_dns_info",
    "get_dns_info_with_options",
    "get_ip_by_host",
    "get_ip_by_host_with_options",
    "idn_to_ascii",
    # TCP
    "ping",
    "ping_with_options",
    "is_open",
    "is_open_with_options",
    "connect",
    "connect_with_options",
    "is_connected",
    "netcat",
    "netcat_with_options",
    "get_remote_address",
    # Address
    "build_inet_socket_address",
    "build_inet_socket_address_with_options",
    "create_address",
    "create_address_with_options",
    # Local interface
    "get_network_interface",
    "get_network_interface_with_options",
    "get_network_interfaces",
    "get_network_interfaces_with_options",
    "local_ipv4s",
    "local_ipv4s_with_options",
    "local_ipv6s",
    "local_ipv6s_with_options",
    "local_ips",
    "local_ips_with_options",
    "to_ip_list",
    "local_address_list",
    "local_address_list_with_options",
    "get_localhost_str",
    "get_localhost_str_with_options",
    "get_localhost",
    "get_localhost_with_options",
    "get_local_host_name",
    "get_local_host_name_with_options",
    "get_local_mac_address",
    "get_local_mac_address_with_options",
    "get_mac_address",
    "get_mac_address_with_options",
    "get_hardware_address",
    "get_hardware_address_with_options",
    "get_local_hardware_address",
    "get_local_hardware_address_with_options",
    # Misc
    "is_unknown",
    "parse_cookies",
    "get_multistage_reverse_proxy_ip",
    # Multipart
    "new_upload_setting",
    "parse_multipart_form",
    "save_uploaded_file",
    "upload_file_name",
    "upload_file_size",
    "upload_file_content_type",
    # Go-compat type aliases
    "Dialer",
    "ConnectOption",
    "PingOption",
    "ResolveOption",
    "AddressOption",
    "PortOption",
    "InterfaceOption",
    "TLSFileOption",
    "UploadSaveOption",
    "IPOption",
    "WildcardOption",
    "OpenUploadedFileFunc",
]

LOCAL_IP = netx.LOCAL_IP
IP_SPLIT_MARK = netx.IP_SPLIT_MARK
IP_MASK_SPLIT_MARK = netx.IP_MASK_SPLIT_MARK
IP_MASK_MAX = netx.IP_MASK_MAX
PORT_RANGE_MIN = netx.PORT_RANGE_MIN
PORT_RANGE_MAX = netx.PORT_RANGE_MAX
SSL = netx.SSL
SSLv2 = netx.SSLv2
SSLv3 = netx.SSLv3
TLS = netx.TLS
TLSv1 = netx.TLSv1
TLSv11 = netx.TLSv11
TLSv12 = netx.TLSv12
TLSv13 = netx.TLSv13

# IP validation
is_ip = netx.is_ip
is_ip_with_options = netx.is_ip_with_options
is_ipv4 = netx.is_ipv4
is_ipv4_with_options = netx.is_ipv4_with_options
is_ipv6 = netx.is_ipv6
is_ipv6_with_options = netx.is_ipv6_with_options
is_inner_ip = netx.is_inner_ip
is_inner_ip_with_options = netx.is_inner_ip_with_options

# IP conversion
ipv4_to_long = netx.ipv4_to_long
ipv4_to_long_with_options = netx.ipv4_to_long_with_options
ipv4_to_long_default = netx.ipv4_to_long_default
ipv4_to_long_default_with_options = netx.ipv4_to_long_default_with_options
long_to_ipv4 = netx.long_to_ipv4
ipv6_to_int = netx.ipv6_to_int
ipv6_to_int_with_options = netx.ipv6_to_int_with_options
int_to_ipv6 = netx.int_to_ipv6

# IP range
is_in_range = netx.is_in_range
is_in_range_with_options = netx.is_in_range_with_options
first_ip = netx.first_ip
last_ip = netx.last_ip
address_count = netx.address_count
matches_wildcard = netx.matches_wildcard
matches_wildcard_with_options = netx.matches_wildcard_with_options
hide_ip_part = netx.hide_ip_part
hide_ip_part_long = netx.hide_ip_part_long

# Port
is_valid_port = netx.is_valid_port
is_usable_local_port = netx.is_usable_local_port
is_usable_local_port_with_options = netx.is_usable_local_port_with_options
get_usable_local_port = netx.get_usable_local_port
get_usable_local_port_with_options = netx.get_usable_local_port_with_options
get_usable_local_port_from = netx.get_usable_local_port_from
get_usable_local_port_from_with_options = netx.get_usable_local_port_from_with_options
get_usable_local_port_in_range = netx.get_usable_local_port_in_range
get_usable_local_port_in_range_with_options = netx.get_usable_local_port_in_range_with_options
get_usable_local_ports = netx.get_usable_local_ports
get_usable_local_ports_with_options = netx.get_usable_local_ports_with_options
new_local_port_generator = netx.new_local_port_generator
new_local_port_generator_with_options = netx.new_local_port_generator_with_options

# Subnet math
mask_bit_by_mask = netx.mask_bit_by_mask
mask_bit_by_mask_with_options = netx.mask_bit_by_mask_with_options
count_by_mask_bit = netx.count_by_mask_bit
mask_by_mask_bit = netx.mask_by_mask_bit
mask_by_ip_range = netx.mask_by_ip_range
mask_by_ip_range_with_options = netx.mask_by_ip_range_with_options
count_by_ip_range = netx.count_by_ip_range
count_by_ip_range_with_options = netx.count_by_ip_range_with_options
format_ip_block = netx.format_ip_block
format_ip_block_with_options = netx.format_ip_block_with_options
begin_ip = netx.begin_ip
begin_ip_with_options = netx.begin_ip_with_options
begin_ip_long = netx.begin_ip_long
begin_ip_long_with_options = netx.begin_ip_long_with_options
end_ip = netx.end_ip
end_ip_with_options = netx.end_ip_with_options
end_ip_long = netx.end_ip_long
end_ip_long_with_options = netx.end_ip_long_with_options
is_mask_valid = netx.is_mask_valid
is_mask_valid_with_options = netx.is_mask_valid_with_options
is_mask_bit_valid = netx.is_mask_bit_valid
list_ips = netx.list_ips
list_ips_with_options = netx.list_ips_with_options
list_ip_cidr = netx.list_ip_cidr
list_ip_cidr_with_options = netx.list_ip_cidr_with_options
list_ip_range = netx.list_ip_range
list_ip_range_with_options = netx.list_ip_range_with_options

# TLS
new_tls_config_builder = netx.new_tls_config_builder
create_tls_config = netx.create_tls_config
tls_version = netx.tls_version
new_cert_pool = netx.new_cert_pool
add_root_ca_bytes = netx.add_root_ca_bytes

# DNS
get_dns_info = netx.get_dns_info
get_dns_info_with_options = netx.get_dns_info_with_options
get_ip_by_host = netx.get_ip_by_host
get_ip_by_host_with_options = netx.get_ip_by_host_with_options
idn_to_ascii = netx.idn_to_ascii

# TCP
ping = netx.ping
ping_with_options = netx.ping_with_options
is_open = netx.is_open
is_open_with_options = netx.is_open_with_options
connect = netx.connect
connect_with_options = netx.connect_with_options
is_connected = netx.is_connected
netcat = netx.netcat
netcat_with_options = netx.netcat_with_options
get_remote_address = netx.get_remote_address

# Address
build_inet_socket_address = netx.build_inet_socket_address
build_inet_socket_address_with_options = netx.build_inet_socket_address_with_options
create_address = netx.create_address
create_address_with_options = netx.create_address_with_options

# Local interface
get_network_interface = netx.get_network_interface
get_network_interface_with_options = netx.get_network_interface_with_options
get_network_interfaces = netx.get_network_interfaces
get_network_interfaces_with_options = netx.get_network_interfaces_with_options
local_ipv4s = netx.local_ipv4s
local_ipv4s_with_options = netx.local_ipv4s_with_options
local_ipv6s = netx.local_ipv6s
local_ipv6s_with_options = netx.local_ipv6s_with_options
local_ips = netx.local_ips
local_ips_with_options = netx.local_ips_with_options
to_ip_list = netx.to_ip_list
local_address_list = netx.local_address_list
local_address_list_with_options = netx.local_address_list_with_options
get_localhost_str = netx.get_localhost_str
get_localhost_str_with_options = netx.get_localhost_str_with_options
get_localhost = netx.get_localhost
get_localhost_with_options = netx.get_localhost_with_options
get_local_host_name = netx.get_local_host_name
get_local_host_name_with_options = netx.get_local_host_name_with_options
get_local_mac_address = netx.get_local_mac_address
get_local_mac_address_with_options = netx.get_local_mac_address_with_options
get_mac_address = netx.get_mac_address
get_mac_address_with_options = netx.get_mac_address_with_options
get_hardware_address = netx.get_hardware_address
get_hardware_address_with_options = netx.get_hardware_address_with_options
get_local_hardware_address = netx.get_local_hardware_address
get_local_hardware_address_with_options = netx.get_local_hardware_address_with_options

# Misc
is_unknown = netx.is_unknown
parse_cookies = netx.parse_cookies
get_multistage_reverse_proxy_ip = netx.get_multistage_reverse_proxy_ip

# Multipart
new_upload_setting = netx.new_upload_setting
parse_multipart_form = netx.parse_multipart_form
save_uploaded_file = netx.save_uploaded_file
upload_file_name = netx.upload_file_name
upload_file_size = netx.upload_file_size
upload_file_content_type = netx.upload_file_content_type