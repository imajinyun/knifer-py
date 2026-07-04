from __future__ import annotations

from typing import Any

from kniferpy.internal import convx


to_str = convx.to_str
to_str_default = convx.to_str_default
to_str_e = convx.to_str_e

to_int = convx.to_int
to_int_e = convx.to_int_e
to_int_default = convx.to_int_default
to_int_e_ok = convx.to_int_e_ok

to_int64 = convx.to_int64
to_int64_e = convx.to_int64_e
to_int64_default = convx.to_int64_default
to_int64_e_ok = convx.to_int64_e_ok
to_int64_with_options = convx.to_int64_with_options

to_float = convx.to_float
to_float_e = convx.to_float_e
to_float_default = convx.to_float_default
to_float_e_ok = convx.to_float_e_ok

to_float64 = convx.to_float64
to_float64_e = convx.to_float64_e
to_float64_default = convx.to_float64_default
to_float64_e_ok = convx.to_float64_e_ok
to_float64_with_options = convx.to_float64_with_options

to_bool = convx.to_bool
to_bool_e = convx.to_bool_e
to_bool_default = convx.to_bool_default
to_bool_e_ok = convx.to_bool_e_ok
to_bool_with_options = convx.to_bool_with_options

to_bytes = convx.to_bytes
to_bytes_default = convx.to_bytes_default
to_bytes_e_ok = convx.to_bytes_e_ok
to_bytes_with_options = convx.to_bytes_with_options

__all__ = [
    "to_str",
    "to_str_default",
    "to_str_e",
    "to_int",
    "to_int_e",
    "to_int_default",
    "to_int_e_ok",
    "to_int64",
    "to_int64_e",
    "to_int64_default",
    "to_int64_e_ok",
    "to_int64_with_options",
    "to_float",
    "to_float_e",
    "to_float_default",
    "to_float_e_ok",
    "to_float64",
    "to_float64_e",
    "to_float64_default",
    "to_float64_e_ok",
    "to_float64_with_options",
    "to_bool",
    "to_bool_e",
    "to_bool_default",
    "to_bool_e_ok",
    "to_bool_with_options",
    "to_bytes",
    "to_bytes_default",
    "to_bytes_e_ok",
    "to_bytes_with_options",
]