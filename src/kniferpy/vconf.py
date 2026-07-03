"""Grouped key-value configuration parsing.

Parse ``properties``/INI-style configuration into grouped keys and read typed
values with fail-safe defaults. Supports ``[section]`` groups, ``#``/``;``
comments, ``=``/``:`` separators, quoted values, ``${var}`` / ``${group.key}``
/ ``${ENV:NAME}`` / ``${key:default}`` expansion, profile overlays, merging,
and cloning.

Only the pure text-parsing core is ported. The remote loaders (``LoadRemote``),
file watching, schema validation, struct binding, and full YAML/TOML parsing
from knifer-go are intentionally omitted; use :mod:`kniferpy.vjson`,
``configparser``, or a YAML/TOML library alongside this facade when needed.
"""

from __future__ import annotations

from pathlib import Path

from kniferpy.internal import confx
from kniferpy.internal.confx import Conf

__all__ = [
    "Conf",
    "load",
    "load_files",
    "load_profile",
    "merge",
    "new",
    "parse",
    "parse_bytes",
]


def new() -> Conf:
    """Create an empty :class:`Conf`."""
    return confx.new()


def parse(content: str) -> Conf:
    """Parse properties/INI text into a :class:`Conf`."""
    return confx.parse(content)


def parse_bytes(content: bytes) -> Conf:
    """Parse UTF-8 properties/INI bytes into a :class:`Conf`."""
    return confx.parse_bytes(content)


def load(path: str | Path) -> Conf:
    """Read and parse a properties/INI file from ``path``."""
    return confx.load(path)


def load_files(*paths: str | Path) -> Conf:
    """Load multiple files and merge them in order (later overrides earlier)."""
    return confx.load_files(*paths)


def load_profile(path: str | Path, profile: str) -> Conf:
    """Load a file and apply profile-specific overrides."""
    return confx.load_profile(path, profile)


def merge(*configs: Conf) -> Conf:
    """Merge configs in order; later configs override earlier ones."""
    return confx.merge(*configs)
