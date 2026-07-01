from __future__ import annotations

from typing import Any

from kniferpy.internal import convx


def to_str(value: Any) -> str:
    return convx.to_str(value)


def to_int(value: Any, default: int = 0) -> int:
    return convx.to_int(value, default)


def to_int_e(value: Any) -> int:
    return convx.to_int_e(value)


def to_float(value: Any, default: float = 0.0) -> float:
    return convx.to_float(value, default)


def to_float_e(value: Any) -> float:
    return convx.to_float_e(value)


def to_bool(value: Any, default: bool = False) -> bool:
    return convx.to_bool(value, default)


def to_bool_e(value: Any) -> bool:
    return convx.to_bool_e(value)


def to_bytes(value: Any, *, encoding: str = "utf-8") -> bytes:
    return convx.to_bytes(value, encoding=encoding)
