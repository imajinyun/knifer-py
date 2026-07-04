"""Grouped key-value configuration parsing.

Parse ``properties``/INI-style configuration into grouped keys and read typed
values with fail-safe defaults. Supports ``[section]`` groups, ``#``/``;``
comments, ``=``/``:`` separators, quoted values, ``${var}`` / ``${group.key}``
/ ``${ENV:NAME}`` / ``${key:default}`` expansion, profile overlays, merging,
cloning, file watching, struct binding, schema validation, and remote loading
with SSRF protection.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from kniferpy.internal import confx
from kniferpy.internal.confx import (
    Conf,
    FieldRule,
    Schema,
    WatchEvent,
)

__all__ = [
    "Conf",
    "FieldRule",
    "Schema",
    "WatchEvent",
    "apply_defaults",
    "bind",
    "bind_group",
    "load",
    "load_files",
    "load_profile",
    "load_remote",
    "load_remote_safe",
    "merge",
    "new",
    "parse",
    "parse_bytes",
    "parse_by_ext",
    "parse_json",
    "parse_toml",
    "parse_yaml",
    "schema_from_struct",
    "validate_schema",
    "watch",
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


def load_remote(url: str, timeout: float = 10.0) -> Conf:
    """Load configuration from a remote URL."""
    return confx.load_remote(url, timeout)


def load_remote_safe(url: str, timeout: float = 10.0) -> Conf:
    """Load configuration from a remote URL with SSRF protection."""
    return confx.load_remote_safe(url, timeout)


def merge(*configs: Conf) -> Conf:
    """Merge configs in order; later configs override earlier ones."""
    return confx.merge(*configs)


def watch(
    path: str | Path,
    onChange: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
) -> threading.Thread:
    """Watch a file for changes via polling."""
    return confx.watch(path, onChange, interval=interval)


def bind(conf: Conf, obj: object) -> None:
    """Bind configuration values to a dataclass instance."""
    confx.bind(conf, obj)


def bind_group(conf: Conf, group: str, obj: object) -> None:
    """Bind configuration values from a group to a dataclass instance."""
    confx.bind_group(conf, group, obj)


def validate_schema(conf: Conf, schema: Schema) -> list[str]:
    """Validate a Conf against a Schema. Returns a list of error messages."""
    return confx.validate_schema(conf, schema)


def apply_defaults(conf: Conf, schema: Schema) -> Conf:
    """Apply schema defaults to missing keys."""
    return confx.apply_defaults(conf, schema)


def schema_from_struct(obj: object) -> Schema:
    """Build a Schema from a dataclass with conf metadata tags."""
    return confx.schema_from_struct(obj)


def parse_yaml(content: str) -> Conf:
    """Parse YAML content into a :class:`Conf`."""
    return confx.parse_yaml(content)


def parse_toml(content: str) -> Conf:
    """Parse TOML content into a :class:`Conf`."""
    return confx.parse_toml(content)


def parse_json(content: str) -> Conf:
    """Parse JSON content into a :class:`Conf`."""
    return confx.parse_json(content)


def parse_by_ext(content: str, ext: str) -> Conf:
    """Parse content according to file extension."""
    return confx.parse_by_ext(content, ext)