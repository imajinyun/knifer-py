"""Configuration parsing, merging, binding, and validation.

Parse properties/INI, YAML, TOML, and JSON. Load local files or remote URLs,
apply profile overrides, bind to dataclasses, and validate with schemas.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal import confx  # noqa: F401
from kniferpy.internal.confx import (
    Conf,
    ConfError,
    DefaultMaxBytes,
    FieldRule,
    LoadOptions,
    Schema,
    TypeBool,
    TypeFloat,
    TypeInt,
    TypeList,
    TypeString,
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
    parse_by_ext,
    parse_by_ext_with_options,
    parse_bytes,
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

# ── Go-compat type aliases ───────────────────────────────────────────────────────

LoadOption = Callable[[Any], None]
DecryptFunc = Callable[[Any], None]
ExpandOption = Callable[[Any], None]
ValueOption = Callable[[Any], None]
BindOption = Callable[[Any], None]
DecodeHookFunc = Callable[[Any], None]
SchemaOption = Callable[[Any], None]
ParseOption = Callable[[Any], None]
WatchOptions = Callable[[Any], None]
WatchTicker = Callable[[Any], None]
WatchTickerFactory = Callable[[Any], None]

# ── Go-compat *WithOptions aliases ─────────────────────────────────────────────

load_remote_with_options = load_remote
load_remote_safe_with_options = load_remote_safe
load_profile_with_options = load_profile

__all__ = [
    # Types
    "Conf",
    "ConfError",
    "FieldRule",
    "LoadOptions",
    "LoadOption",
    "Schema",
    "WatchEvent",
    # Go-compat type aliases
    "DecryptFunc",
    "ExpandOption",
    "ValueOption",
    "BindOption",
    "DecodeHookFunc",
    "SchemaOption",
    "ParseOption",
    "WatchOptions",
    "WatchTicker",
    "WatchTickerFactory",
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
    # Go-compat *WithOptions aliases
    "load_remote_with_options",
    "load_remote_safe_with_options",
    "load_profile_with_options",
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
