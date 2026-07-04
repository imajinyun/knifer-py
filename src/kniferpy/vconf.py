"""Configuration parsing, merging, binding, and validation.

Parse properties/INI, YAML, TOML, and JSON. Load local files or remote URLs,
apply profile overrides, bind to dataclasses, and validate with schemas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from kniferpy.internal import confx
from kniferpy.internal.confx import (
    Conf,
    ConfError,
    FieldRule,
    LoadOptions,
    Schema,
    WatchEvent,
    apply_defaults,
    base64_decrypt,
    bind,
    bind_group,
    bind_group_with_options,
    bind_with_options,
    load,
    load_files,
    load_files_with_options,
    load_profile,
    load_remote,
    load_remote_safe,
    load_with_options,
    merge,
    new,
    parse,
    parse_bytes,
    parse_by_ext,
    parse_by_ext_with_options,
    parse_json,
    parse_toml,
    parse_toml_with_options,
    parse_yaml,
    parse_yaml_full,
    parse_yaml_full_with_options,
    schema_from_struct,
    validate_schema,
    validate_struct,
    validate_struct_with_options,
    watch,
    watch_with_options,
)

# ── Go-compat type alias ───────────────────────────────────────────────────────

LoadOption = Callable[[Any], None]
"""Functional option for configuration loading (Go compat)."""

__all__ = [
    # Types
    "Conf",
    "ConfError",
    "FieldRule",
    "LoadOptions",
    "LoadOption",
    "Schema",
    "WatchEvent",
    # Type constants
    "TypeString",
    "TypeBool",
    "TypeInt",
    "TypeFloat",
    "TypeList",
    "DefaultMaxBytes",
    # Core functions
    "new",
    "parse",
    "parse_bytes",
    "parse_by_ext",
    "parse_by_ext_with_options",
    "parse_yaml",
    "parse_yaml_full",
    "parse_yaml_full_with_options",
    "parse_toml",
    "parse_toml_with_options",
    "parse_json",
    "load",
    "load_with_options",
    "load_files",
    "load_files_with_options",
    "load_profile",
    "load_remote",
    "load_remote_safe",
    "merge",
    "watch",
    "watch_with_options",
    # Binding
    "bind",
    "bind_with_options",
    "bind_group",
    "bind_group_with_options",
    # Schema
    "schema_from_struct",
    "validate_schema",
    "validate_struct",
    "validate_struct_with_options",
    "apply_defaults",
    # Utilities
    "base64_decrypt",
]