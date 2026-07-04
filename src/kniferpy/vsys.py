"""System information and environment variable helpers.

Query operating-system, host, and current-user information from the standard
library, and read environment variables with typed defaults. All lookups fail
safe: missing or unparseable values fall back to the supplied default rather
than raising.
"""

from __future__ import annotations

from kniferpy.internal import sysx
from kniferpy.internal.sysx import HostInfo, OsInfo, RuntimeInfo, UserInfo

__all__ = [
    "HostInfo",
    "OsInfo",
    "RuntimeInfo",
    "UserInfo",
    "get",
    "get_bool",
    "get_current_pid",
    "get_host_info",
    "get_int",
    "get_or_default",
    "get_os_info",
    "get_user_info",
    "get_runtime_info",
    "get_total_memory",
    "get_free_memory",
    "get_max_memory",
    "get_total_thread_count",
    "get_goroutine_count",
    "get_ip_by_host",
    "get_multistage_reverse_proxy_ip",
    "is_unknown",
    "parse_cookies",
    "idn_to_ascii",
    "dump_system_info",
]


def get_os_info() -> OsInfo:
    """Return operating system information (name, arch, version, separators)."""
    return sysx.get_os_info()


def get_host_info() -> HostInfo:
    """Return the host name and primary non-loopback IPv4 address."""
    return sysx.get_host_info()


def get_user_info() -> UserInfo:
    """Return the current user and directory information."""
    return sysx.get_user_info()


def get_current_pid() -> int:
    """Return the current process identifier."""
    return sysx.get_current_pid()


def get(key: str, quiet: bool = True) -> str:
    """Return environment variable ``key`` (empty when unset)."""
    return sysx.get(key, quiet)


def get_or_default(key: str, default: str) -> str:
    """Return ``key``, or ``default`` when unset or empty."""
    return sysx.get_or_default(key, default)


def get_int(key: str, default: int = 0) -> int:
    """Return ``key`` parsed as an int, or ``default`` when unset or invalid."""
    return sysx.get_int(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    """Return ``key`` parsed as a bool, or ``default`` when unset or invalid."""
    return sysx.get_bool(key, default)


def get_total_memory() -> int:
    """Return total physical memory in bytes."""
    return sysx.get_total_memory()


def get_free_memory() -> int:
    """Return free physical memory in bytes."""
    return sysx.get_free_memory()


def get_max_memory() -> int:
    """Return max memory in bytes."""
    return sysx.get_max_memory()


def get_runtime_info() -> RuntimeInfo:
    """Return Python runtime information."""
    return sysx.get_runtime_info()


def get_total_thread_count() -> int:
    """Return active thread count."""
    return sysx.get_total_thread_count()


def get_goroutine_count() -> int:
    """Return active thread count (knifer-go compat alias)."""
    return sysx.get_goroutine_count()


def get_ip_by_host(host: str) -> list[str]:
    """Resolve hostname to IP addresses."""
    return sysx.get_ip_by_host(host)


def get_multistage_reverse_proxy_ip(headers: dict[str, str]) -> str:
    """Extract client IP from reverse proxy headers."""
    return sysx.get_multistage_reverse_proxy_ip(headers)


def is_unknown(value: str) -> bool:
    """Check if value is 'unknown' or empty."""
    return sysx.is_unknown(value)


def parse_cookies(cookie_header: str) -> dict[str, str]:
    """Parse a Cookie header string into a dict."""
    return sysx.parse_cookies(cookie_header)


def idn_to_ascii(domain: str) -> str:
    """Convert an internationalized domain name to ASCII."""
    return sysx.idn_to_ascii(domain)


def dump_system_info() -> str:
    """Return a human-readable system information string."""
    return sysx.dump_system_info()
