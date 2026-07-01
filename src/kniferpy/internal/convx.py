from __future__ import annotations

from typing import Any

from kniferpy.verr import ValidationError

_TRUE_STRINGS = frozenset({"1", "t", "true", "y", "yes", "on"})
_FALSE_STRINGS = frozenset({"0", "f", "false", "n", "no", "off"})


def _fail(value: Any, target: str) -> ValidationError:
    return ValidationError(
        message=f"cannot convert {value!r} to {target}",
        code="knifer.conv.invalid",
        context={"value": repr(value), "target": target},
    )


def to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def to_int_e(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise _fail(value, "int")
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text, 10)
        except ValueError:
            try:
                return int(float(text))
            except ValueError as exc:
                raise _fail(value, "int") from exc
    raise _fail(value, "int")


def to_int(value: Any, default: int = 0) -> int:
    try:
        return to_int_e(value)
    except ValidationError:
        return default


def to_float_e(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError as exc:
            raise _fail(value, "float") from exc
    raise _fail(value, "float")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return to_float_e(value)
    except ValidationError:
        return default


def to_bool_e(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in _TRUE_STRINGS:
            return True
        if text in _FALSE_STRINGS:
            return False
        raise _fail(value, "bool")
    raise _fail(value, "bool")


def to_bool(value: Any, default: bool = False) -> bool:
    try:
        return to_bool_e(value)
    except ValidationError:
        return default


def to_bytes(value: Any, *, encoding: str = "utf-8") -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return to_str(value).encode(encoding)
