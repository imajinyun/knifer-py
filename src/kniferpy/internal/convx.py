from __future__ import annotations

from collections.abc import Callable
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


# ========== String ==========


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


def to_str_default(value: Any, default: str) -> str:
    try:
        return to_str(value)
    except Exception:
        return default


def to_str_e(value: Any) -> tuple[str, Exception | None]:
    try:
        return to_str(value), None
    except Exception as e:
        return "", e


# ========== Int ==========


def to_int_e(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        import math
        if math.isnan(value) or math.isinf(value):
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


def to_int_default(value: Any, default: int) -> int:
    return to_int(value, default)


def to_int_e_ok(value: Any) -> tuple[int, bool]:
    try:
        return to_int_e(value), True
    except ValidationError:
        return 0, False


# ========== Int64 ==========


def to_int64_e(value: Any) -> int:
    return to_int_e(value)


def to_int64(value: Any, default: int = 0) -> int:
    return to_int(value, default)


def to_int64_default(value: Any, default: int) -> int:
    return to_int(value, default)


def to_int64_e_ok(value: Any) -> tuple[int, bool]:
    return to_int_e_ok(value)


# ========== Float ==========


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


def to_float_default(value: Any, default: float) -> float:
    return to_float(value, default)


def to_float_e_ok(value: Any) -> tuple[float, bool]:
    try:
        return to_float_e(value), True
    except ValidationError:
        return 0.0, False


# ========== Float64 ==========


def to_float64_e(value: Any) -> float:
    return to_float_e(value)


def to_float64(value: Any, default: float = 0.0) -> float:
    return to_float(value, default)


def to_float64_default(value: Any, default: float) -> float:
    return to_float(value, default)


def to_float64_e_ok(value: Any) -> tuple[float, bool]:
    return to_float_e_ok(value)


# ========== Bool ==========


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


def to_bool_default(value: Any, default: bool) -> bool:
    return to_bool(value, default)


def to_bool_e_ok(value: Any) -> tuple[bool, bool]:
    try:
        return to_bool_e(value), True
    except ValidationError:
        return False, False


# ========== Bytes ==========


def to_bytes(value: Any, *, encoding: str = "utf-8") -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return to_str(value).encode(encoding)


def to_bytes_default(value: Any, default: bytes, *, encoding: str = "utf-8") -> bytes:
    try:
        return to_bytes(value, encoding=encoding)
    except Exception:
        return default


def to_bytes_e_ok(value: Any, *, encoding: str = "utf-8") -> tuple[bytes, bool]:
    try:
        return to_bytes(value, encoding=encoding), True
    except Exception:
        return b"", False


# ========== Generic conversion with options ==========


def to_int64_with_options(value: Any, default: int = 0, **kwargs: Any) -> int:
    return to_int64(value, default)


def to_float64_with_options(value: Any, default: float = 0.0, **kwargs: Any) -> float:
    return to_float64(value, default)


def to_bool_with_options(value: Any, default: bool = False, **kwargs: Any) -> bool:
    return to_bool(value, default)


def to_bytes_with_options(
    value: Any, *, encoding: str = "utf-8", **kwargs: Any
) -> bytes:
    return to_bytes(value, encoding=encoding)