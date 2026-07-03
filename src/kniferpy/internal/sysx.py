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
