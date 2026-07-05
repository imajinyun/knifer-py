from __future__ import annotations

import getpass
import os
import platform
import socket
import sys
import tempfile
from dataclasses import dataclass

from kniferpy.internal import convx


@dataclass(frozen=True, slots=True)
class OsInfo:
    """Operating system information."""

    name: str
    arch: str
    version: str
    file_separator: str
    line_separator: str
    path_separator: str

    def is_linux(self) -> bool:
        return self.name == "Linux"

    def is_mac(self) -> bool:
        return self.name == "Darwin"

    def is_mac_os_x(self) -> bool:
        """Check if OS is macOS (Go compat alias)."""
        return self.is_mac()

    def is_windows(self) -> bool:
        return self.name == "Windows"

    def is_aix(self) -> bool:
        return self.name == "AIX"

    def is_solaris(self) -> bool:
        return self.name == "SunOS"

    def is_freebsd(self) -> bool:
        return self.name == "FreeBSD"

    def __str__(self) -> str:
        return (
            f"OS Arch:        {self.arch}\n"
            f"OS Name:        {self.name}\n"
            f"OS Version:     {self.version}\n"
            f"File Separator: {self.file_separator}\n"
            f"Line Separator: {self.line_separator}\n"
            f"Path Separator: {self.path_separator}\n"
        )


@dataclass(frozen=True, slots=True)
class HostInfo:
    """Host name and primary address information."""

    name: str
    address: str

    def __str__(self) -> str:
        return f"Host Name:    {self.name}\nHost Address: {self.address}\n"


@dataclass(frozen=True, slots=True)
class UserInfo:
    """Current user and directory information."""

    name: str
    home_dir: str
    current_dir: str
    temp_dir: str
    language: str
    country: str

    def __str__(self) -> str:
        return (
            f"User Name:        {self.name}\n"
            f"User Home Dir:    {self.home_dir}\n"
            f"User Current Dir: {self.current_dir}\n"
            f"User Temp Dir:    {self.temp_dir}\n"
            f"User Language:    {self.language}\n"
            f"User Country:     {self.country}\n"
        )


@dataclass(frozen=True, slots=True)
class RuntimeInfo:
    """Python runtime information (knifer-go GoInfo/RuntimeInfo equivalent)."""

    python_version: str
    python_implementation: str
    python_compiler: str
    python_path: list[str]
    prefix: str
    executable: str

    def get_total_memory(self) -> int:
        return _get_total_memory()

    def get_free_memory(self) -> int:
        return _get_free_memory()

    def get_max_memory(self) -> int:
        return _get_total_memory()

    def get_usable_memory(self) -> int:
        total = _get_total_memory()
        free = _get_free_memory()
        return total - free

    def get_heap_inuse(self) -> int:
        return self.get_usable_memory()

    def get_thread_count(self) -> int:
        return get_total_thread_count()

    def get_goroutine_count(self) -> int:
        return self.get_thread_count()

    def get_mem_stats(self) -> dict[str, int]:
        return {
            "total": _get_total_memory(),
            "free": _get_free_memory(),
            "max": _get_total_memory(),
            "usable": self.get_usable_memory(),
            "heap_inuse": self.get_heap_inuse(),
            "thread_count": self.get_thread_count(),
        }

    def refresh(self) -> RuntimeInfo:
        return get_runtime_info()

    def __str__(self) -> str:
        return (
            f"Python Version:        {self.python_version}\n"
            f"Python Implementation:  {self.python_implementation}\n"
            f"Python Compiler:       {self.python_compiler}\n"
            f"Python Prefix:         {self.prefix}\n"
            f"Python Executable:     {self.executable}\n"
        )


def _line_separator() -> str:
    return "\r\n" if os.name == "nt" else "\n"


def _os_version() -> str:
    # Environment overrides mirror knifer-go's readOsVersion precedence.
    for key in ("OSVERSION", "OSTYPE"):
        value = os.environ.get(key)
        if value:
            return value
    return platform.release().strip()


def get_os_info() -> OsInfo:
    """Return operating system information from the standard library."""
    return OsInfo(
        name=platform.system(),
        arch=platform.machine(),
        version=_os_version(),
        file_separator=os.sep,
        line_separator=_line_separator(),
        path_separator=os.pathsep,
    )


def _fix_path(path: str) -> str:
    """Append a trailing separator to a non-empty path (matches Go fixPath)."""
    if not path:
        return path
    return path if path.endswith(os.sep) else path + os.sep


def _parse_locale(locale: str) -> tuple[str, str]:
    """Parse a ``LANG`` string such as ``zh_CN.UTF-8`` into (language, country)."""
    if not locale:
        return "", ""
    dot = locale.find(".")
    if dot >= 0:
        locale = locale[:dot]
    parts = locale.split("_")
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _first_non_loopback_ipv4() -> str:
    """Return the primary outbound IPv4 address, or empty when unavailable."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # No packets are sent; this just picks the routable source address.
            sock.connect(("8.8.8.8", 80))
            ip: str = sock.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return ""


def get_host_info() -> HostInfo:
    """Return the host name and primary non-loopback IPv4 address."""
    try:
        name = socket.gethostname()
    except OSError:
        name = ""
    return HostInfo(name=name, address=_first_non_loopback_ipv4())


def get_user_info() -> UserInfo:
    """Return the current user and directory information."""
    try:
        name = getpass.getuser()
    except (OSError, KeyError):
        name = os.environ.get("USER") or os.environ.get("USERNAME") or ""

    home = os.path.expanduser("~")
    if home == "~":
        home = os.environ.get("HOME", "")

    try:
        current = os.getcwd()
    except OSError:
        current = ""

    lang, country = _parse_locale(os.environ.get("LANG", ""))
    if not lang:
        lang, country = _parse_locale(os.environ.get("LC_ALL", ""))

    return UserInfo(
        name=name,
        home_dir=_fix_path(home),
        current_dir=_fix_path(current),
        temp_dir=_fix_path(tempfile.gettempdir()),
        language=lang,
        country=country,
    )


def get_current_pid() -> int:
    """Return the current process identifier."""
    return os.getpid()


# --- Environment variable helpers -------------------------------------------


def get(key: str, quiet: bool = True) -> str:
    """Return the value of environment variable ``key`` (empty when unset).

    When ``quiet`` is false a warning is printed to stderr for a missing key,
    mirroring knifer-go's ``Get``.
    """
    value = os.environ.get(key)
    if value is None:
        if not quiet:
            print(f"[kniferpy] env {key!r} not found", file=sys.stderr)
        return ""
    return value


def get_or_default(key: str, default: str) -> str:
    """Return the value of ``key``, or ``default`` when unset or empty."""
    value = os.environ.get(key)
    if not value:
        return default
    return value


def get_int(key: str, default: int = 0) -> int:
    """Return ``key`` parsed as an int, or ``default`` when unset or invalid."""
    value = os.environ.get(key)
    if value is None:
        return default
    return convx.to_int(value, default)


def get_bool(key: str, default: bool = False) -> bool:
    """Return ``key`` parsed as a bool, or ``default`` when unset or invalid."""
    value = os.environ.get(key)
    if value is None:
        return default
    return convx.to_bool(value, default)


# --- Runtime / process info --------------------------------------------------


def _get_total_memory() -> int:
    """Return total physical memory in bytes."""
    try:
        import psutil
        return psutil.virtual_memory().total
    except ImportError:
        return 0


def _get_free_memory() -> int:
    """Return free physical memory in bytes."""
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        return 0


def _get_max_memory() -> int:
    """Return max memory the process can use (system total)."""
    return _get_total_memory()


def get_total_memory() -> int:
    return _get_total_memory()


def get_free_memory() -> int:
    return _get_free_memory()


def get_max_memory() -> int:
    return _get_max_memory()


def get_runtime_info() -> RuntimeInfo:
    """Return Python runtime information."""
    import sysconfig
    return RuntimeInfo(
        python_version=sys.version,
        python_implementation=platform.python_implementation(),
        python_compiler=platform.python_compiler(),
        python_path=sys.path,
        prefix=sys.prefix,
        executable=sys.executable,
    )


def get_total_thread_count() -> int:
    """Return the number of threads in the current process."""
    try:
        import threading
        return threading.active_count()
    except Exception:
        return 0


def get_goroutine_count() -> int:
    """Alias for get_total_thread_count, matching knifer-go naming."""
    return get_total_thread_count()


# --- Network helpers ---------------------------------------------------------


def get_ip_by_host(host: str) -> list[str]:
    """Resolve hostname to IP addresses."""
    try:
        info = socket.getaddrinfo(host, None)
        return sorted(set(a[4][0] for a in info))
    except (socket.gaierror, OSError):
        return []


def get_multistage_reverse_proxy_ip(headers: dict[str, str]) -> str:
    """Extract the client IP from reverse proxy headers like X-Forwarded-For."""
    for key in ("X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP"):
        value = headers.get(key, "").strip()
        if value:
            # Take the first IP in X-Forwarded-For chain
            return value.split(",")[0].strip()
    return ""


def is_unknown(value: str) -> bool:
    """Check if a string is 'unknown' or empty (used for IP detection)."""
    v = value.strip().lower()
    return v == "" or v == "unknown"


def parse_cookies(cookie_header: str) -> dict[str, str]:
    """Parse a Cookie header string into a dict."""
    if not cookie_header:
        return {}
    result: dict[str, str] = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def idn_to_ascii(domain: str) -> str:
    """Convert an internationalized domain name to ASCII."""
    return domain.encode("idna").decode("ascii")


# --- Dump system info --------------------------------------------------------


def _readable_size(byte_count: int) -> str:
    if byte_count < 1024:
        return f"{byte_count} B"
    for unit in ("KB", "MB", "GB", "TB"):
        byte_count /= 1024.0
        if byte_count < 1024:
            return f"{byte_count:.1f} {unit}"
    return f"{byte_count:.1f} PB"


def dump_system_info() -> str:
    """Return a human-readable string of system information."""
    lines: list[str] = []
    os_info = get_os_info()
    host_info = get_host_info()
    user_info = get_user_info()

    lines.append("=== System Info ===")
    lines.append(f"OS:      {os_info.name} {os_info.version} ({os_info.arch})")
    lines.append(f"Host:    {host_info.name} ({host_info.address})")
    lines.append(f"User:    {user_info.name}")
    lines.append(f"Home:    {user_info.home_dir}")
    lines.append(f"Temp:    {user_info.temp_dir}")
    lines.append(f"PID:     {get_current_pid()}")
    lines.append(f"Threads: {get_total_thread_count()}")
    lines.append(f"Memory:  {_readable_size(get_total_memory())} total, {_readable_size(get_free_memory())} free")
    lines.append("")

    try:
        import sysconfig
        lines.append("=== Python Info ===")
        lines.append(f"Version: {sys.version}")
        lines.append(f"Platform: {sys.platform}")
        lines.append(f"Prefix: {sys.prefix}")
        lines.append("")
    except ImportError:
        pass

    return "\n".join(lines)


def dump_system_info_to(writer) -> None:
    """Write system information to ``writer`` (any object with a ``write`` method)."""
    writer.write(dump_system_info())


def get_env_all() -> dict[str, str]:
    """Return all environment variables as a dict."""
    return dict(os.environ)


def get_cpu_cores() -> int:
    """Return the number of logical CPU cores."""
    return os.cpu_count() or 0


# ── Info cache ──────────────────────────────────────────────────────────────

_cached_os_info: OsInfo | None = None
_cached_host_info: HostInfo | None = None
_cached_user_info: UserInfo | None = None
_cached_runtime_info: RuntimeInfo | None = None


def reset_info_cache() -> None:
    global _cached_os_info, _cached_host_info, _cached_user_info, _cached_runtime_info, _cached_python_info
    _cached_os_info = None
    _cached_host_info = None
    _cached_user_info = None
    _cached_runtime_info = None
    _cached_python_info = None


def _cached_get_os_info() -> OsInfo:
    global _cached_os_info
    if _cached_os_info is None:
        _cached_os_info = get_os_info()
    return _cached_os_info


def _cached_get_host_info() -> HostInfo:
    global _cached_host_info
    if _cached_host_info is None:
        _cached_host_info = get_host_info()
    return _cached_host_info


def _cached_get_user_info() -> UserInfo:
    global _cached_user_info
    if _cached_user_info is None:
        _cached_user_info = get_user_info()
    return _cached_user_info


def _cached_get_runtime_info() -> RuntimeInfo:
    global _cached_runtime_info
    if _cached_runtime_info is None:
        _cached_runtime_info = get_runtime_info()
    return _cached_runtime_info


# ── New* constructors (Go compat: always create fresh instances) ────────────

def new_host_info() -> HostInfo:
    """Create a fresh HostInfo instance (never cached)."""
    return get_host_info()


def new_os_info() -> OsInfo:
    """Create a fresh OsInfo instance (never cached)."""
    return get_os_info()


def new_user_info() -> UserInfo:
    """Create a fresh UserInfo instance (never cached)."""
    return get_user_info()


def new_runtime_info() -> RuntimeInfo:
    """Create a fresh RuntimeInfo instance (never cached)."""
    return get_runtime_info()


# ── System* cached accessors (Go compat: singleton cache) ───────────────────

def system_host_info() -> HostInfo:
    """Return cached HostInfo (singleton, cleared by reset_info_cache)."""
    return _cached_get_host_info()


def system_os_info() -> OsInfo:
    """Return cached OsInfo (singleton, cleared by reset_info_cache)."""
    return _cached_get_os_info()


def system_user_info() -> UserInfo:
    """Return cached UserInfo (singleton, cleared by reset_info_cache)."""
    return _cached_get_user_info()


def system_runtime_info() -> RuntimeInfo:
    """Return cached RuntimeInfo (singleton, cleared by reset_info_cache)."""
    return _cached_get_runtime_info()


# ── Short aliases (Go compat naming) ─────────────────────────────────────────

def env(key: str) -> str:
    """Short alias for ``get(key, quiet=True)``."""
    return get(key, quiet=True)


def env_or_default(key: str, default: str) -> str:
    """Short alias for ``get_or_default``."""
    return get_or_default(key, default)


def env_int(key: str, default: int = 0) -> int:
    """Short alias for ``get_int``."""
    return get_int(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    """Short alias for ``get_bool``."""
    return get_bool(key, default)


def current_pid() -> int:
    """Short alias for ``get_current_pid``."""
    return get_current_pid()


def total_memory() -> int:
    """Short alias for ``get_total_memory``."""
    return get_total_memory()


def free_memory() -> int:
    """Short alias for ``get_free_memory``."""
    return get_free_memory()


def max_memory() -> int:
    """Short alias for ``get_max_memory``."""
    return get_max_memory()


def total_goroutine_count() -> int:
    """Short alias for ``get_goroutine_count``."""
    return get_goroutine_count()


# ── PythonInfo type (GoInfo equivalent) ──────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PythonInfo:
    """Python runtime metadata (knifer-go GoInfo equivalent)."""

    version: str
    implementation: str
    compiler: str
    prefix: str
    executable: str
    num_cpu: int

    def __str__(self) -> str:
        return (
            f"Python Version:       {self.version}\n"
            f"Python Implementation: {self.implementation}\n"
            f"Python Compiler:       {self.compiler}\n"
            f"Python Prefix:        {self.prefix}\n"
            f"Python Executable:    {self.executable}\n"
            f"Num CPU:             {self.num_cpu}\n"
        )


def new_python_info() -> PythonInfo:
    """Create a fresh PythonInfo instance."""
    return PythonInfo(
        version=sys.version,
        implementation=platform.python_implementation(),
        compiler=platform.python_compiler(),
        prefix=sys.prefix,
        executable=sys.executable,
        num_cpu=os.cpu_count() or 0,
    )


def get_python_info() -> PythonInfo:
    """Return cached PythonInfo (singleton, cleared by reset_info_cache)."""
    global _cached_python_info
    if _cached_python_info is None:
        _cached_python_info = new_python_info()
    return _cached_python_info


_cached_python_info: PythonInfo | None = None


# ── Sys* short aliases ───────────────────────────────────────────────────────

def sys_host_info() -> HostInfo:
    """Short alias for ``system_host_info``."""
    return system_host_info()


def sys_os_info() -> OsInfo:
    """Short alias for ``system_os_info``."""
    return system_os_info()


def sys_user_info() -> UserInfo:
    """Short alias for ``system_user_info``."""
    return system_user_info()


def sys_runtime_info() -> RuntimeInfo:
    """Short alias for ``system_runtime_info``."""
    return system_runtime_info()


def sys_python_info() -> PythonInfo:
    """Short alias for ``get_python_info``."""
    return get_python_info()
