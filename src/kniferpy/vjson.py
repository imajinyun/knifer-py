from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from kniferpy.internal import jsonx
from kniferpy.internal.jsonx import (
    Config,
    JSONArray,
    JSONObject,
    Null,
    is_null,
    new_json_array,
    new_json_object,
)
from kniferpy.verr import JSONError

# ── Go-compat type alias ───────────────────────────────────────────────────────

JSONOption = Callable[[Any], None]
"""Functional option for JSON parsing/serialization (Go compat)."""

# Parse
parse = jsonx.loads
parse_obj = jsonx.parse_obj
parse_array = jsonx.parse_array
parse_with_options = jsonx.parse_with_options
parse_with_config = jsonx.parse_with_config
parse_obj_with_options = jsonx.parse_obj_with_options
parse_obj_with_config = jsonx.parse_obj_with_config
parse_array_with_options = jsonx.parse_array_with_options
parse_array_with_config = jsonx.parse_array_with_config

# Serialize
dumps = jsonx.dumps
to_json_str = jsonx.to_json_str
to_pretty_str = jsonx.to_pretty_str
to_str_indent = jsonx.to_str_indent
to_str_with_config = jsonx.to_str_with_config
to_str = jsonx.to_str
to_pretty_str_with_config = jsonx.to_pretty_str_with_config
quote = jsonx.quote

# Path access
get_path = jsonx.get_path
put_by_path = jsonx.put_by_path
get_str = jsonx.get_str
get_int = jsonx.get_int
get_float = jsonx.get_float
get_bool = jsonx.get_bool
get_list = jsonx.get_list
get_dict = jsonx.get_dict
has_path = jsonx.has_path
get_by_path_or = jsonx.get_by_path_or

# Validation
is_json = jsonx.is_json
is_json_with_options = jsonx.is_json_with_options
is_json_obj = jsonx.is_json_obj
is_obj = jsonx.is_obj
is_obj_with_options = jsonx.is_obj_with_options
is_json_array = jsonx.is_json_array
is_array = jsonx.is_array
is_array_with_options = jsonx.is_array_with_options
is_valid = jsonx.is_valid

# File I/O
read = jsonx.read
read_obj = jsonx.read_obj
write = jsonx.write

# Bean conversion
to_bean = jsonx.to_bean
to_bean_with_options = jsonx.to_bean_with_options
to_list = jsonx.to_list
to_list_with_options = jsonx.to_list_with_options

# Format
format_json_str = jsonx.format_json_str
format_json = jsonx.format_json
format_json_with_options = jsonx.format_json_with_options

# Config / constructors
new_config = jsonx.new_config
create_config = jsonx.create_config
new_object_with_config = jsonx.new_object_with_config
new_array_with_config = jsonx.new_array_with_config

# Error constructors
new_json_error = jsonx.new_json_error
wrap_json_error = jsonx.wrap_json_error

# XML conversion
xml_to_json = jsonx.xml_to_json
xml_to_json_with_options = jsonx.xml_to_json_with_options
json_to_xml = jsonx.json_to_xml
to_xml = jsonx.to_xml
to_xml_with_options = jsonx.to_xml_with_options

__all__ = [
    # Types
    "Config",
    "JSONArray",
    "JSONError",
    "JSONObject",
    "Null",
    # Sentinel checks
    "is_null",
    # Constructors
    "new_json_array",
    "new_json_object",
    "new_object_with_config",
    "new_array_with_config",
    "new_config",
    "create_config",
    # Parse
    "parse",
    "parse_obj",
    "parse_array",
    "parse_with_options",
    "parse_with_config",
    "parse_obj_with_options",
    "parse_obj_with_config",
    "parse_array_with_options",
    "parse_array_with_config",
    # Serialize
    "dumps",
    "to_json_str",
    "to_pretty_str",
    "to_str_indent",
    "to_str_with_config",
    "to_str",
    "to_pretty_str_with_config",
    "quote",
    # Go-compat type alias
    "JSONOption",
    # Path access
    "get_path",
    "put_by_path",
    "get_str",
    "get_int",
    "get_float",
    "get_bool",
    "get_list",
    "get_dict",
    "has_path",
    "get_by_path_or",
    # Validation
    "is_json",
    "is_json_with_options",
    "is_json_obj",
    "is_obj",
    "is_obj_with_options",
    "is_json_array",
    "is_array",
    "is_array_with_options",
    "is_valid",
    # File I/O
    "read",
    "read_obj",
    "write",
    # Bean conversion
    "to_bean",
    "to_bean_with_options",
    "to_list",
    "to_list_with_options",
    # Format
    "format_json_str",
    "format_json",
    "format_json_with_options",
    # Error constructors
    "new_json_error",
    "wrap_json_error",
    # XML conversion
    "xml_to_json",
    "xml_to_json_with_options",
    "json_to_xml",
    "to_xml",
    "to_xml_with_options",
]