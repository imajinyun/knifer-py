from __future__ import annotations

import email.message
import email.parser
import ipaddress
import os
import socket
import ssl
import tempfile
from typing import Any, Callable

from kniferpy.verr import ValidationError

# --- constants ---

LOCAL_IP = "127.0.0.1"
IP_SPLIT_MARK = "-"
IP_MASK_SPLIT_MARK = "/"
IP_MASK_MAX = 32
PORT_RANGE_MIN = 1024
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


# ---------------------------------------------------------------------------
# TLS configuration builder
# ---------------------------------------------------------------------------

_SSL_VERSIONS: dict[str, int] = {
    "SSL": ssl.PROTOCOL_TLS,
    "SSLv2": ssl.PROTOCOL_TLS,
    "SSLv3": ssl.PROTOCOL_TLS,
    "TLS": ssl.PROTOCOL_TLS,
    "TLSv1": ssl.PROTOCOL_TLSv1,
    "TLSv1.1": ssl.PROTOCOL_TLSv1_1,
    "TLSv1.2": ssl.PROTOCOL_TLSv1_2,
    "TLSv1.3": ssl.PROTOCOL_TLS_CLIENT,
}

# Exported TLS/SSL protocol label constants
SSL = "SSL"
SSLv2 = "SSLv2"
SSLv3 = "SSLv3"
TLS = "TLS"
TLSv1 = "TLSv1"
TLSv11 = "TLSv1.1"
TLSv12 = "TLSv1.2"
TLSv13 = "TLSv1.3"


class TLSConfigBuilder:
    """Builds an :class:`ssl.SSLContext` with fluent methods."""

    __slots__ = ("_context",)

    def __init__(self) -> None:
        self._context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    def set_min_version(self, version: str) -> TLSConfigBuilder:
        v = _SSL_VERSIONS.get(version)
        if v is not None:
            self._context.minimum_version = _ssl_version_code(v)
        return self

    def set_max_version(self, version: str) -> TLSConfigBuilder:
        v = _SSL_VERSIONS.get(version)
        if v is not None:
            self._context.maximum_version = _ssl_version_code(v)
        return self

    def set_server_name(self, name: str) -> TLSConfigBuilder:
        self._context.check_hostname = bool(name)
        return self

    def add_root_ca_file(self, path: str) -> TLSConfigBuilder:
        self._context.load_verify_locations(cafile=path)
        return self

    def add_root_ca_bytes(self, data: bytes) -> TLSConfigBuilder:
        self._context.load_verify_locations(cadata=data.decode("utf-8", errors="replace"))
        return self

    def set_certificates(self, cert_file: str, key_file: str | None = None) -> TLSConfigBuilder:
        self._context.load_cert_chain(cert_file, keyfile=key_file)
        return self

    def build(self) -> ssl.SSLContext:
        return self._context


def _ssl_version_code(proto: int) -> ssl.TLSVersion:
    mapping = {
        ssl.PROTOCOL_TLSv1: ssl.TLSVersion.TLSv1,
        ssl.PROTOCOL_TLSv1_1: ssl.TLSVersion.TLSv1_1,
        ssl.PROTOCOL_TLSv1_2: ssl.TLSVersion.TLSv1_2,
        ssl.PROTOCOL_TLS_CLIENT: ssl.TLSVersion.TLSv1_3,
    }
    return mapping.get(proto, ssl.TLSVersion.MINIMUM_SUPPORTED)


def new_tls_config_builder() -> TLSConfigBuilder:
    return TLSConfigBuilder()


def create_tls_config() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def tls_version(version: str) -> int:
    return _SSL_VERSIONS.get(version, ssl.PROTOCOL_TLS)


# ---------------------------------------------------------------------------
# DNS helpers
# ---------------------------------------------------------------------------

_DNS_TYPE_MAP = {"A": 1, "AAAA": 28, "MX": 15, "NS": 2, "TXT": 16, "CNAME": 5}


def get_dns_info(host: str, types: list[str] | None = None) -> dict[str, list[str]]:
    """Resolve DNS records for a host. Returns a dict mapping record types to lists of values."""
    if types is None:
        types = ["A", "AAAA"]
    import socket as _socket

    result: dict[str, list[str]] = {}
    for t in types:
        try:
            answers = _socket.getaddrinfo(host, None, family=_socket.AF_UNSPEC)
            if t in ("A", "AAAA"):
                af = _socket.AF_INET if t == "A" else _socket.AF_INET6
                result[t] = sorted(set(a[4][0] for a in answers if a[0] == af))
            elif t == "MX":
                # MX records not available via getaddrinfo — use a sentinel
                result[t] = []
            else:
                result[t] = []
        except _socket.gaierror:
            result[t] = []
    return result


def get_ip_by_host(host: str) -> list[str]:
    """Resolve hostname to IP addresses."""
    import socket as _socket

    try:
        answers = _socket.getaddrinfo(host, None)
        return sorted(set(a[4][0] for a in answers))
    except _socket.gaierror:
        return []


def idn_to_ascii(domain: str) -> str:
    """Convert an internationalized domain name to ASCII."""
    return domain.encode("idna").decode("ascii")


# ---------------------------------------------------------------------------
# TCP Ping / Connect helpers
# ---------------------------------------------------------------------------


def ping(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check TCP reachability to host:port. Returns True if a connection is established."""
    import socket as _socket

    try:
        with _socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, _socket.timeout):
        return False


def is_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """Alias for :func:`ping`."""
    return ping(host, port, timeout)


def connect(host: str, port: int, timeout: float = 3.0) -> socket.socket | None:
    """Establish a TCP connection to host:port and return the socket, or None."""
    import socket as _socket

    try:
        sock = _socket.create_connection((host, port), timeout=timeout)
        return sock
    except (OSError, _socket.timeout):
        return None


def is_connected(sock: socket.socket | None) -> bool:
    """Check if a socket is still connected."""
    if sock is None:
        return False
    try:
        sock.getpeername()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Multipart form parsing
# ---------------------------------------------------------------------------


class UploadSetting:
    """Configuration for multipart upload parsing."""

    __slots__ = (
        "max_file_size",
        "memory_threshold",
        "tmp_upload_path",
        "file_exts",
        "allow_file_exts",
    )

    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,
        memory_threshold: int = 1024 * 1024,
        tmp_upload_path: str = "",
        file_exts: list[str] | None = None,
        allow_file_exts: list[str] | None = None,
    ) -> None:
        self.max_file_size = max_file_size
        self.memory_threshold = memory_threshold
        self.tmp_upload_path = tmp_upload_path or tempfile.gettempdir()
        self.file_exts = file_exts or []
        self.allow_file_exts = allow_file_exts or []


class MultipartFormData:
    """Parsed multipart form data."""

    __slots__ = ("_fields", "_files")

    def __init__(self) -> None:
        self._fields: dict[str, list[str]] = {}
        self._files: dict[str, list[tuple[str, bytes, str]]] = {}

    def is_loaded(self) -> bool:
        return bool(self._fields or self._files)

    def get_param(self, name: str) -> str:
        vals = self._fields.get(name, [])
        return vals[0] if vals else ""

    def get_param_names(self) -> list[str]:
        return sorted(self._fields)

    def get_array_param(self, name: str) -> list[str]:
        return self._fields.get(name, [])

    def get_file(self, name: str) -> tuple[str, bytes, str] | None:
        files = self._files.get(name, [])
        return files[0] if files else None

    def get_files(self, name: str) -> list[tuple[str, bytes, str]]:
        return self._files.get(name, [])

    def get_file_param_names(self) -> list[str]:
        return sorted(self._files)

    def get_param_map(self) -> dict[str, str]:
        return {k: v[0] for k, v in self._fields.items() if v}

    def get_param_list_map(self) -> dict[str, list[str]]:
        return dict(self._fields)

    def get_file_map(self) -> dict[str, tuple[str, bytes, str]]:
        return {k: v[0] for k, v in self._files.items() if v}

    def get_file_list_value_map(self) -> dict[str, list[tuple[str, bytes, str]]]:
        return dict(self._files)

    def get_list_param(self, name: str) -> list[str]:
        return self._fields.get(name, [])

    def get_file_list(self, name: str) -> list[tuple[str, bytes, str]]:
        return self._files.get(name, [])


def new_upload_setting() -> UploadSetting:
    """Create a new UploadSetting with default values."""
    return UploadSetting()


def _parse_header_params(header_value: str) -> tuple[str, dict[str, str]]:
    """Parse a parameterized header into ``(value, params)``."""
    parts = header_value.split(";", 1)
    value = parts[0].strip()
    params: dict[str, str] = {}
    if len(parts) > 1:
        for param in parts[1].split(";"):
            param = param.strip()
            if "=" not in param:
                continue
            k, v = param.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            params[k] = v
    return value, params


def parse_multipart_form(
    body: bytes,
    content_type: str,
    setting: UploadSetting | None = None,
) -> MultipartFormData:
    """Parse a multipart/form-data body into fields and files."""
    setting = setting or UploadSetting()
    result = MultipartFormData()

    # Extract boundary
    _, params = _parse_header_params(content_type)
    boundary = params.get("boundary", "")
    if not boundary:
        raise ValidationError(
            message="missing boundary in multipart content-type",
            code="knifer.net.missing_boundary",
            context={"content_type": content_type},
        )

    # Split body by boundary
    boundary_bytes = boundary.encode("utf-8")
    delimiter = b"--" + boundary_bytes
    parts = body.split(delimiter)

    for part in parts[1:-1]:  # skip preamble and epilogue
        if not part.strip() or part.startswith(b"--"):
            continue

        # Strip leading CRLF
        part = part.lstrip(b"\r\n")

        # Split headers from body
        header_end = part.find(b"\r\n\r\n")
        if header_end < 0:
            header_end = part.find(b"\n\n")
        if header_end < 0:
            continue

        header_bytes = part[:header_end]
        body_bytes = part[header_end + 4 :]  # skip \r\n\r\n
        # Strip trailing \r\n that precedes the next boundary
        body_bytes = body_bytes.rstrip(b"\r\n")

        headers = email.parser.BytesParser().parsebytes(header_bytes + b"\r\n\r\n")
        disposition = headers.get("Content-Disposition", "")
        _, disp_params = _parse_header_params(disposition)

        name = disp_params.get("name", "")
        filename = disp_params.get("filename")

        if filename:
            # File upload
            ext = os.path.splitext(filename)[1].lower()
            if setting.file_exts and ext not in setting.file_exts:
                continue
            if setting.allow_file_exts and ext not in setting.allow_file_exts:
                raise ValidationError(
                    message=f"file extension not allowed: {ext}",
                    code="knifer.net.file_ext_not_allowed",
                    context={"ext": ext, "filename": filename},
                )
            if len(body_bytes) > setting.max_file_size:
                raise ValidationError(
                    message=f"file exceeds max size: {len(body_bytes)} > {setting.max_file_size}",
                    code="knifer.net.file_too_large",
                    context={"filename": filename, "size": len(body_bytes)},
                )
            content_type_val = headers.get("Content-Type", "application/octet-stream")
            result._files.setdefault(name, []).append((filename, body_bytes, content_type_val))
        elif name:
            result._fields.setdefault(name, []).append(body_bytes.decode("utf-8", errors="replace"))

    return result


def save_uploaded_file(
    file_entry: tuple[str, bytes, str],
    dest_dir: str,
    dest_name: str = "",
    overwrite: bool = False,
) -> str:
    """Save an uploaded file entry to disk. Returns the full path."""
    filename, data, _ = file_entry
    save_name = dest_name or filename
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, save_name)
    if not overwrite and os.path.exists(file_path):
        raise ValidationError(
            message=f"file already exists: {file_path}",
            code="knifer.net.file_exists",
            context={"path": file_path},
        )
    with open(file_path, "wb") as f:
        f.write(data)
    return file_path


def upload_file_name(file_entry: tuple[str, bytes, str]) -> str:
    return file_entry[0]


def upload_file_size(file_entry: tuple[str, bytes, str]) -> int:
    return len(file_entry[1])


def upload_file_content_type(file_entry: tuple[str, bytes, str]) -> str:
    return file_entry[2]


# ---------------------------------------------------------------------------
# Subnet math
# ---------------------------------------------------------------------------


def _parse_cidr(cidr: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        return ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError:
        return None


def mask_bit_by_mask(mask: str) -> int:
    """Return the prefix length from a subnet mask (e.g., '255.255.255.0' -> 24)."""
    ip = _parse(mask)
    if not isinstance(ip, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid mask: {mask}",
            code="knifer.net.invalid_mask",
            context={"mask": mask},
        )
    binary = bin(int(ip))[2:].zfill(32)
    if "01" in binary:
        raise ValidationError(
            message=f"not a valid subnet mask: {mask}",
            code="knifer.net.invalid_mask",
            context={"mask": mask},
        )
    return binary.count("1")


def count_by_mask_bit(mask_bit: int, is_all: bool = False) -> int:
    """Return the number of addresses in a subnet with the given prefix length."""
    if mask_bit < 0 or mask_bit > 32:
        raise ValidationError(
            message=f"invalid mask bit: {mask_bit}",
            code="knifer.net.invalid_mask_bit",
            context={"mask_bit": mask_bit},
        )
    total = 1 << (32 - mask_bit)
    if is_all:
        return total
    return max(0, total - 2)


def mask_by_mask_bit(mask_bit: int) -> str:
    """Return the subnet mask for a given prefix length."""
    if mask_bit < 0 or mask_bit > 32:
        raise ValidationError(
            message=f"invalid mask bit: {mask_bit}",
            code="knifer.net.invalid_mask_bit",
            context={"mask_bit": mask_bit},
        )
    mask_int = (IPV4_MAX << (32 - mask_bit)) & IPV4_MAX
    return str(ipaddress.IPv4Address(mask_int))


def mask_by_ip_range(from_ip: str, to_ip: str) -> str:
    """Compute the subnet mask from an IP range."""
    from_addr = _parse(from_ip)
    to_addr = _parse(to_ip)
    if not isinstance(from_addr, ipaddress.IPv4Address) or not isinstance(
        to_addr, ipaddress.IPv4Address
    ):
        raise ValidationError(
            message="invalid IP range",
            code="knifer.net.invalid_ip_range",
            context={"from_ip": from_ip, "to_ip": to_ip},
        )
    diff = int(to_addr) ^ int(from_addr)
    if diff == 0:
        return "255.255.255.255"
    prefix = 32 - diff.bit_length()
    return mask_by_mask_bit(prefix)


def count_by_ip_range(from_ip: str, to_ip: str) -> int:
    """Count addresses in an IP range."""
    from_addr = _parse(from_ip)
    to_addr = _parse(to_ip)
    if not isinstance(from_addr, ipaddress.IPv4Address) or not isinstance(
        to_addr, ipaddress.IPv4Address
    ):
        raise ValidationError(
            message="invalid IP range",
            code="knifer.net.invalid_ip_range",
            context={"from_ip": from_ip, "to_ip": to_ip},
        )
    return int(to_addr) - int(from_addr) + 1


def format_ip_block(ip: str, mask: str) -> str:
    """Format an IP and mask as CIDR notation."""
    parsed = _parse(ip)
    if not isinstance(parsed, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid IP: {ip}",
            code="knifer.net.invalid_ip",
            context={"ip": ip},
        )
    return f"{ip}/{mask_bit_by_mask(mask)}"


def begin_ip(ip: str, mask_bit: int) -> str:
    """Return the first/gateway address of a subnet."""
    addr = _parse(ip)
    if not isinstance(addr, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid IP: {ip}",
            code="knifer.net.invalid_ip",
            context={"ip": ip},
        )
    if mask_bit < 0 or mask_bit > 32:
        raise ValidationError(
            message=f"invalid mask bit: {mask_bit}",
            code="knifer.net.invalid_mask_bit",
            context={"mask_bit": mask_bit},
        )
    mask_int = (IPV4_MAX << (32 - mask_bit)) & IPV4_MAX
    return str(ipaddress.IPv4Address(int(addr) & mask_int))


def begin_ip_long(ip: str, mask_bit: int) -> int:
    return ipv4_to_long(begin_ip(ip, mask_bit))


def end_ip(ip: str, mask_bit: int) -> str:
    """Return the last/broadcast address of a subnet."""
    addr = _parse(ip)
    if not isinstance(addr, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid IP: {ip}",
            code="knifer.net.invalid_ip",
            context={"ip": ip},
        )
    if mask_bit < 0 or mask_bit > 32:
        raise ValidationError(
            message=f"invalid mask bit: {mask_bit}",
            code="knifer.net.invalid_mask_bit",
            context={"mask_bit": mask_bit},
        )
    mask_int = (IPV4_MAX << (32 - mask_bit)) & IPV4_MAX
    return str(ipaddress.IPv4Address((int(addr) & mask_int) | (~mask_int & IPV4_MAX)))


def end_ip_long(ip: str, mask_bit: int) -> int:
    return ipv4_to_long(end_ip(ip, mask_bit))


def is_mask_valid(mask: str) -> bool:
    try:
        mask_bit_by_mask(mask)
        return True
    except ValidationError:
        return False


def is_mask_bit_valid(mask_bit: int) -> bool:
    return 0 <= mask_bit <= 32


def list_ips(ip_range: str, is_all: bool = False) -> list[str]:
    """List all IPs in a CIDR range."""
    network = _parse_cidr(ip_range)
    if network is None:
        raise ValidationError(
            message=f"invalid CIDR: {ip_range}",
            code="knifer.net.invalid_cidr",
            context={"ip_range": ip_range},
        )
    hosts = list(network.hosts()) if not is_all else list(network)
    return [str(h) for h in hosts]


def list_ip_cidr(ip: str, mask_bit: int, is_all: bool = False) -> list[str]:
    """List all IPs given a base IP and prefix length."""
    addr = _parse(ip)
    if not isinstance(addr, ipaddress.IPv4Address):
        raise ValidationError(
            message=f"invalid IP: {ip}",
            code="knifer.net.invalid_ip",
            context={"ip": ip},
        )
    network = ipaddress.IPv4Network(f"{ip}/{mask_bit}", strict=False)
    hosts = list(network.hosts()) if not is_all else list(network)
    return [str(h) for h in hosts]


def list_ip_range(from_ip: str, to_ip: str) -> list[str]:
    """List all IPs between from_ip and to_ip (inclusive)."""
    from_addr = _parse(from_ip)
    to_addr = _parse(to_ip)
    if not isinstance(from_addr, ipaddress.IPv4Address) or not isinstance(
        to_addr, ipaddress.IPv4Address
    ):
        raise ValidationError(
            message="invalid IP range",
            code="knifer.net.invalid_ip_range",
            context={"from_ip": from_ip, "to_ip": to_ip},
        )
    start = int(from_addr)
    end = int(to_addr)
    if start > end:
        raise ValidationError(
            message="from_ip must be <= to_ip",
            code="knifer.net.invalid_ip_range",
            context={"from_ip": from_ip, "to_ip": to_ip},
        )
    return [str(ipaddress.IPv4Address(i)) for i in range(start, end + 1)]


# ---------------------------------------------------------------------------
# Local interface / network info
# ---------------------------------------------------------------------------


def _get_local_ips(version: int = 0) -> list[str]:
    """Get all local IP addresses using standard library only."""
    ips: set[str] = set()
    try:
        family = (
            socket.AF_INET
            if version == 4
            else (socket.AF_INET6 if version == 6 else socket.AF_UNSPEC)
        )
        for info in socket.getaddrinfo(socket.gethostname(), None, family=family):
            ip = info[4][0]
            if version == 4 and ":" in ip:
                continue
            if version == 6 and ":" not in ip:
                continue
            if ip.startswith("fe80:"):
                continue
            ips.add(ip)
    except socket.gaierror:
        pass

    # Also try common local addresses
    if version == 0 or version == 4:
        ips.add(LOCAL_IP)

    return sorted(ips)


def get_network_interface(name: str) -> dict[str, Any] | None:
    """Get info for a specific network interface. Returns None if not found."""
    return None


def get_network_interfaces() -> dict[str, Any]:
    """Get all network interfaces. Returns empty dict as pure Python fallback."""
    return {}


def local_ipv4s() -> list[str]:
    return _get_local_ips(version=4)


def local_ipv6s() -> list[str]:
    return _get_local_ips(version=6)


def local_ips() -> list[str]:
    return _get_local_ips()


def to_ip_list(address_list: list[str]) -> list[str]:
    return sorted(set(address_list))


def get_localhost_str() -> str:
    return LOCAL_IP


def get_localhost() -> str:
    return LOCAL_IP


def get_local_host_name() -> str:
    return socket.gethostname()


def get_local_mac_address(separator: str = "-") -> str:
    """Get the MAC address of the first non-loopback interface."""
    import uuid

    mac = uuid.getnode()
    return separator.join(f"{(mac >> (i * 8)) & 0xFF:02x}" for i in reversed(range(6)))


def get_mac_address(inet_address: str, separator: str = "-") -> str:
    """Get MAC address for a specific IP."""
    import uuid

    node = uuid.getnode()
    return separator.join(f"{(node >> (i * 8)) & 0xFF:02x}" for i in reversed(range(6)))


def get_hardware_address(inet_address: str) -> str:
    return get_mac_address(inet_address, separator=":")


def get_local_hardware_address() -> str:
    return get_mac_address(get_localhost_str(), separator=":")


def local_address_list(address_filter=None) -> list[str]:
    """Get local IPs, optionally filtered."""
    ips = local_ips()
    if address_filter is None:
        return ips
    return [ip for ip in ips if address_filter(ip)]


# ---------------------------------------------------------------------------
# Port generator
# ---------------------------------------------------------------------------


class LocalPortGenerator:
    """Stateful port generator for finding available ports."""

    __slots__ = ("_next_port",)

    def __init__(self, begin_port: int = PORT_RANGE_MIN) -> None:
        self._next_port = begin_port

    def gen(self) -> int:
        port = self._next_port
        self._next_port += 1
        if self._next_port > PORT_RANGE_MAX:
            self._next_port = PORT_RANGE_MIN
        return port


def is_usable_local_port(port: int) -> bool:
    if not is_valid_port(port):
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return True
    except OSError:
        return False


def _find_usable_port(start: int, end: int) -> int:
    for port in range(start, end + 1):
        if is_usable_local_port(port):
            return port
    raise ValidationError(
        message=f"no usable port in range {start}-{end}",
        code="knifer.net.no_usable_port",
        context={"start": start, "end": end},
    )


def get_usable_local_port() -> int:
    return _find_usable_port(PORT_RANGE_MIN, PORT_RANGE_MAX)


def get_usable_local_port_from(min_port: int) -> int:
    return _find_usable_port(min_port, PORT_RANGE_MAX)


def get_usable_local_port_in_range(min_port: int, max_port: int) -> int:
    return _find_usable_port(min_port, max_port)


def get_usable_local_ports(num_requested: int, min_port: int, max_port: int) -> list[int]:
    ports: list[int] = []
    used: set[int] = set()
    for port in range(min_port, max_port + 1):
        if len(ports) >= num_requested:
            break
        if port in used:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                ports.append(port)
                used.add(port)
        except OSError:
            continue
    if len(ports) < num_requested:
        raise ValidationError(
            message=f"only found {len(ports)} of {num_requested} requested ports",
            code="knifer.net.no_usable_port",
            context={"found": len(ports), "requested": num_requested},
        )
    return ports


def new_local_port_generator(begin_port: int = PORT_RANGE_MIN) -> LocalPortGenerator:
    return LocalPortGenerator(begin_port)


# ---------------------------------------------------------------------------
# NetCat / TCP connectivity
# ---------------------------------------------------------------------------


def netcat(host: str, port: int, data: bytes, timeout: float = 3.0) -> None:
    """Send data via TCP and return the response."""
    import socket as _socket

    try:
        with _socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(data)
    except (OSError, _socket.timeout) as exc:
        raise ValidationError(
            message=f"netcat failed: {exc}",
            code="knifer.net.netcat_failed",
            context={"host": host, "port": port},
        ) from exc


def get_remote_address(sock: socket.socket) -> str:
    try:
        addr = sock.getpeername()
        return f"{addr[0]}:{addr[1]}"
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Address construction
# ---------------------------------------------------------------------------


def build_inet_socket_address(host: str, default_port: int) -> tuple[str, int]:
    """Parse host:port or host, defaulting to default_port."""
    if ":" in host and host.count(":") == 1:
        parts = host.rsplit(":", 1)
        port_str = parts[1]
        if port_str.isdigit():
            return parts[0], int(port_str)
    return host, default_port


def create_address(host: str, port: int) -> tuple[str, int]:
    return host, port


# ---------------------------------------------------------------------------
# Misc network utilities
# ---------------------------------------------------------------------------


_UNKNOWN_PATTERNS = ("unknown", "none", "null", "n/a", "")


def is_unknown(check_string: str) -> bool:
    return check_string.strip().lower() in _UNKNOWN_PATTERNS


def parse_cookies(cookie_str: str) -> dict[str, str]:
    """Parse a Cookie header string into a dict of name -> value."""
    cookies: dict[str, str] = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, value = item.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies


def get_multistage_reverse_proxy_ip(headers: dict[str, str]) -> str:
    """Extract the real client IP from reverse proxy headers."""
    for hdr in ("X-Forwarded-For", "X-Real-IP", "Proxy-Client-IP", "WL-Proxy-Client-IP"):
        val = headers.get(hdr, "")
        if val and not is_unknown(val):
            return val.split(",")[0].strip()
    return ""


# TLS cert pool
def new_cert_pool() -> ssl.SSLContext:
    return ssl.create_default_context()


def add_root_ca_bytes(ssl_context: ssl.SSLContext, ca_data: bytes) -> None:
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as f:
        f.write(ca_data)
        f.flush()
        ssl_context.load_verify_locations(cafile=f.name)


# ── Go-compat Root CA additions ─────────────────────────────────────────────


def add_root_ca_file_with_options(builder: Any, path: str, **_opts: Any) -> None:
    """Add a root CA file to a TLS config builder (Go compat)."""
    builder.add_root_ca_file(path)


def add_root_ca_reader(builder: Any, reader: Any) -> None:
    """Add root CA from a reader to a TLS config builder (Go compat)."""
    data = reader.read()
    builder.add_root_ca_bytes(data)


def add_root_ca_reader_with_options(builder: Any, reader: Any, **_opts: Any) -> None:
    """Add root CA from a reader with options (Go compat)."""
    add_root_ca_reader(builder, reader)


def local_address_list_by_interface(
    interface_filter: Callable[[Any], bool] | None = None,
    address_filter: Callable[[Any], bool] | None = None,
) -> list[str]:
    """List IP addresses filtered by interface and address (Go compat)."""
    result: list[str] = []
    for interface, addrs in _get_interface_addresses():
        if interface_filter is not None and not interface_filter(interface):
            continue
        for addr in addrs:
            if address_filter is not None and not address_filter(addr):
                continue
            result.append(addr)
    return result


def _get_interface_addresses() -> list[tuple[Any, list[str]]]:
    """Get network interface name/address pairs."""
    import socket as _socket

    hostname = _socket.gethostname()
    ips: list[tuple[Any, list[str]]] = []
    try:
        for info in _socket.getaddrinfo(hostname, None):
            name = info[0].name if hasattr(info[0], "name") else ""
            ip = info[4][0]
            ips.append((name, [ip]))
    except Exception:
        pass
    return ips


# ========== WithOptions variants ==========


def is_ip_with_options(value: str, **_opts: Any) -> bool:
    return is_ip(value)


def is_ipv4_with_options(value: str, **_opts: Any) -> bool:
    return is_ipv4(value)


def is_ipv6_with_options(value: str, **_opts: Any) -> bool:
    return is_ipv6(value)


def is_inner_ip_with_options(value: str, **_opts: Any) -> bool:
    return is_inner_ip(value)


def ipv4_to_long_with_options(value: str, **_opts: Any) -> int:
    return ipv4_to_long(value)


def ipv4_to_long_default_with_options(value: str, default: int = 0, **_opts: Any) -> int:
    return ipv4_to_long_default(value, default)


def ipv6_to_int_with_options(value: str, **_opts: Any) -> int:
    return ipv6_to_int(value)


def is_in_range_with_options(value: str, cidr: str, **_opts: Any) -> bool:
    return is_in_range(value, cidr)


def matches_wildcard_with_options(wildcard: str, value: str, **_opts: Any) -> bool:
    return matches_wildcard(wildcard, value)


def mask_bit_by_mask_with_options(mask: str, **_opts: Any) -> int:
    return mask_bit_by_mask(mask)


def mask_by_ip_range_with_options(from_ip: str, to_ip: str, **_opts: Any) -> str:
    return mask_by_ip_range(from_ip, to_ip)


def count_by_ip_range_with_options(from_ip: str, to_ip: str, **_opts: Any) -> int:
    return count_by_ip_range(from_ip, to_ip)


def format_ip_block_with_options(ip: str, mask: str, **_opts: Any) -> str:
    return format_ip_block(ip, mask)


def begin_ip_with_options(ip: str, mask_bit: int, **_opts: Any) -> str:
    return begin_ip(ip, mask_bit)


def begin_ip_long_with_options(ip: str, mask_bit: int, **_opts: Any) -> int:
    return begin_ip_long(ip, mask_bit)


def end_ip_with_options(ip: str, mask_bit: int, **_opts: Any) -> str:
    return end_ip(ip, mask_bit)


def end_ip_long_with_options(ip: str, mask_bit: int, **_opts: Any) -> int:
    return end_ip_long(ip, mask_bit)


def is_mask_valid_with_options(mask: str, **_opts: Any) -> bool:
    return is_mask_valid(mask)


def list_ips_with_options(ip_range: str, is_all: bool = False, **_opts: Any) -> list[str]:
    return list_ips(ip_range, is_all)


def list_ip_cidr_with_options(
    ip: str, mask_bit: int, is_all: bool = False, **_opts: Any
) -> list[str]:
    return list_ip_cidr(ip, mask_bit, is_all)


def list_ip_range_with_options(from_ip: str, to_ip: str, **_opts: Any) -> list[str]:
    return list_ip_range(from_ip, to_ip)


def get_ip_by_host_with_options(host: str, **_opts: Any) -> list[str]:
    return get_ip_by_host(host)


def get_dns_info_with_options(
    host: str, types: list[str] | None = None, **_opts: Any
) -> dict[str, list[str]]:
    return get_dns_info(host, types)


def ping_with_options(host: str, port: int, timeout: float = 3.0, **_opts: Any) -> bool:
    return ping(host, port, timeout)


def is_open_with_options(host: str, port: int, timeout: float = 3.0, **_opts: Any) -> bool:
    return ping(host, port, timeout)


def connect_with_options(
    host: str, port: int, timeout: float = 3.0, **_opts: Any
) -> socket.socket | None:
    return connect(host, port, timeout)


def netcat_with_options(
    host: str, port: int, data: bytes, timeout: float = 3.0, **_opts: Any
) -> None:
    return netcat(host, port, data, timeout)


def build_inet_socket_address_with_options(
    host: str, default_port: int, **_opts: Any
) -> tuple[str, int]:
    return build_inet_socket_address(host, default_port)


def create_address_with_options(host: str, port: int, **_opts: Any) -> tuple[str, int]:
    return create_address(host, port)


def get_network_interface_with_options(name: str, **_opts: Any) -> dict | None:
    return get_network_interface(name)


def get_network_interfaces_with_options(**_opts: Any) -> dict:
    return get_network_interfaces()


def local_ipv4s_with_options(**_opts: Any) -> list[str]:
    return local_ipv4s()


def local_ipv6s_with_options(**_opts: Any) -> list[str]:
    return local_ipv6s()


def local_ips_with_options(**_opts: Any) -> list[str]:
    return local_ips()


def local_address_list_with_options(address_filter=None, **_opts: Any) -> list[str]:
    return local_address_list(address_filter)


def get_localhost_str_with_options(**_opts: Any) -> str:
    return get_localhost_str()


def get_localhost_with_options(**_opts: Any) -> str:
    return get_localhost()


def get_local_host_name_with_options(**_opts: Any) -> str:
    return get_local_host_name()


def get_local_mac_address_with_options(separator: str = "-", **_opts: Any) -> str:
    return get_local_mac_address(separator)


def get_mac_address_with_options(inet_address: str, separator: str = "-", **_opts: Any) -> str:
    return get_mac_address(inet_address, separator)


def get_hardware_address_with_options(inet_address: str, **_opts: Any) -> str:
    return get_hardware_address(inet_address)


def get_local_hardware_address_with_options(**_opts: Any) -> str:
    return get_local_hardware_address()


def is_usable_local_port_with_options(port: int, **_opts: Any) -> bool:
    return is_usable_local_port(port)


def get_usable_local_port_with_options(**_opts: Any) -> int:
    return get_usable_local_port()


def get_usable_local_port_from_with_options(min_port: int, **_opts: Any) -> int:
    return get_usable_local_port_from(min_port)


def get_usable_local_port_in_range_with_options(min_port: int, max_port: int, **_opts: Any) -> int:
    return get_usable_local_port_in_range(min_port, max_port)


def get_usable_local_ports_with_options(
    num_requested: int, min_port: int, max_port: int, **_opts: Any
) -> list[int]:
    return get_usable_local_ports(num_requested, min_port, max_port)


def new_local_port_generator_with_options(
    begin_port: int = PORT_RANGE_MIN, **_opts: Any
) -> LocalPortGenerator:
    return new_local_port_generator(begin_port)
