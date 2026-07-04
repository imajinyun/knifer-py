from __future__ import annotations

from pathlib import Path
from typing import Any

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

# Parse
parse = jsonx.loads
parse_obj = jsonx.parse_obj
parse_array = jsonx.parse_array

# Serialize
dumps = jsonx.dumps
to_json_str = jsonx.to_json_str
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

# Validation
is_json = jsonx.is_json
is_json_obj = jsonx.is_json_obj
is_json_array = jsonx.is_json_array
is_valid = jsonx.is_valid

# File I/O
read = jsonx.read
read_obj = jsonx.read_obj
write = jsonx.write

# Bean conversion
to_bean = jsonx.to_bean
to_list = jsonx.to_list

# Format
format_json_str = jsonx.format_json_str

# Config
new_config = jsonx.new_config

# XML conversion
xml_to_json = jsonx.xml_to_json
json_to_xml = jsonx.json_to_xml

# Safe path access
get_by_path_or = jsonx.get_by_path_or

__all__ = [
    "Config",
    "JSONArray",
    "JSONError",
    "JSONObject",
    "Null",
    "is_null",
    "new_json_array",
    "new_json_object",
    "parse",
    "parse_obj",
    "parse_array",
    "dumps",
    "to_json_str",
    "quote",
    "get_path",
    "put_by_path",
    "get_str",
    "get_int",
    "get_float",
    "get_bool",
    "get_list",
    "get_dict",
    "has_path",
    "is_json",
    "is_json_obj",
    "is_json_array",
    "is_valid",
    "read",
    "read_obj",
    "write",
    "to_bean",
    "to_list",
    "format_json_str",
    "new_config",
    "xml_to_json",
    "json_to_xml",
    "get_by_path_or",
]