"""System information and environment variable helpers.

Query operating-system, host, and current-user information from the standard
library, and read environment variables with typed defaults. All lookups fail
safe: missing or unparseable values fall back to the supplied default rather
than raising.
"""

from __future__ import annotations

from kniferpy.internal import sysx
from kniferpy.internal.sysx import HostInfo, OsInfo, PythonInfo, RuntimeInfo, UserInfo

# ── Go-compat type aliases ─────────────────────────────────────────────────────

from typing import Any, Callable

GoInfo = PythonInfo  # Go: system.GoInfo
HostInfoOption = Callable[[Any], None]
GoInfoOption = Callable[[Any], None]
OsInfoOption = Callable[[Any], None]
RuntimeInfoOption = Callable[[Any], None]
UserInfoOption = Callable[[Any], None]
ProcessOption = Callable[[Any], None]
DumpOption = Callable[[Any], None]

__all__ = [
    "HostInfo",
    "OsInfo",
    "PythonInfo",
    "RuntimeInfo",
    "UserInfo",
    "current_pid",
    "dump_system_info",
    "dump_system_info_to",
    "env",
    "env_bool",
    "env_int",
    "env_or_default",
    "free_memory",
    "get",
    "get_bool",
    "get_cpu_cores",
    "get_current_pid",
    "get_env_all",
    "get_free_memory",
    "get_goroutine_count",
    "get_host_info",
    "get_int",
    "get_ip_by_host",
    "get_max_memory",
    "get_multistage_reverse_proxy_ip",
    "get_or_default",
    "get_os_info",
    "get_python_info",
    "get_runtime_info",
    "get_total_memory",
    "get_total_thread_count",
    "get_user_info",
    "idn_to_ascii",
    "is_unknown",
    "max_memory",
    "new_host_info",
    "new_os_info",
    "new_python_info",
    "new_runtime_info",
    "new_user_info",
    "parse_cookies",
    "reset_info_cache",
    "sys_host_info",
    "sys_os_info",
    "sys_python_info",
    "sys_runtime_info",
    "sys_user_info",
    "system_host_info",
    "system_os_info",
    "system_runtime_info",
    "system_user_info",
    "total_goroutine_count",
    "total_memory",
    # Go-compat type aliases
    "GoInfo",
    "HostInfoOption",
    "GoInfoOption",
    "OsInfoOption",
    "RuntimeInfoOption",
    "UserInfoOption",
    "ProcessOption",
    "DumpOption",
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


def dump_system_info_to(writer) -> None:
    """Write system information to ``writer``."""
    return sysx.dump_system_info_to(writer)


def get_env_all() -> dict[str, str]:
    """Return all environment variables as a dict."""
    return sysx.get_env_all()


def get_cpu_cores() -> int:
    """Return the number of logical CPU cores."""
    return sysx.get_cpu_cores()


def reset_info_cache() -> None:
    """Clear cached system info snapshots."""
    return sysx.reset_info_cache()


def new_host_info() -> HostInfo:
    """Create a fresh HostInfo instance (never cached)."""
    return sysx.new_host_info()


def new_os_info() -> OsInfo:
    """Create a fresh OsInfo instance (never cached)."""
    return sysx.new_os_info()


def new_user_info() -> UserInfo:
    """Create a fresh UserInfo instance (never cached)."""
    return sysx.new_user_info()


def new_runtime_info() -> RuntimeInfo:
    """Create a fresh RuntimeInfo instance (never cached)."""
    return sysx.new_runtime_info()


def system_host_info() -> HostInfo:
    """Return cached HostInfo (singleton, cleared by reset_info_cache)."""
    return sysx.system_host_info()


def system_os_info() -> OsInfo:
    """Return cached OsInfo (singleton, cleared by reset_info_cache)."""
    return sysx.system_os_info()


def system_user_info() -> UserInfo:
    """Return cached UserInfo (singleton, cleared by reset_info_cache)."""
    return sysx.system_user_info()


def system_runtime_info() -> RuntimeInfo:
    """Return cached RuntimeInfo (singleton, cleared by reset_info_cache)."""
    return sysx.system_runtime_info()


def env(key: str) -> str:
    """Short alias for ``get(key, quiet=True)``."""
    return sysx.env(key)


def env_or_default(key: str, default: str) -> str:
    """Short alias for ``get_or_default``."""
    return sysx.env_or_default(key, default)


def env_int(key: str, default: int = 0) -> int:
    """Short alias for ``get_int``."""
    return sysx.env_int(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    """Short alias for ``get_bool``."""
    return sysx.env_bool(key, default)


def current_pid() -> int:
    """Short alias for ``get_current_pid``."""
    return sysx.current_pid()


def total_memory() -> int:
    """Short alias for ``get_total_memory``."""
    return sysx.total_memory()


def free_memory() -> int:
    """Short alias for ``get_free_memory``."""
    return sysx.free_memory()


def max_memory() -> int:
    """Short alias for ``get_max_memory``."""
    return sysx.max_memory()


def total_goroutine_count() -> int:
    """Short alias for ``get_goroutine_count``."""
    return sysx.total_goroutine_count()


def new_python_info() -> PythonInfo:
    """Create a fresh PythonInfo instance."""
    return sysx.new_python_info()


def get_python_info() -> PythonInfo:
    """Return cached PythonInfo (singleton, cleared by reset_info_cache)."""
    return sysx.get_python_info()


def sys_host_info() -> HostInfo:
    """Short alias for ``system_host_info``."""
    return sysx.sys_host_info()


def sys_os_info() -> OsInfo:
    """Short alias for ``system_os_info``."""
    return sysx.sys_os_info()


def sys_user_info() -> UserInfo:
    """Short alias for ``system_user_info``."""
    return sysx.sys_user_info()


def sys_runtime_info() -> RuntimeInfo:
    """Short alias for ``system_runtime_info``."""
    return sysx.sys_runtime_info()


def sys_python_info() -> PythonInfo:
    """Short alias for ``get_python_info``."""
    return sysx.sys_python_info()
