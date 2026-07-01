from __future__ import annotations

from pathlib import Path
from typing import Any

from kniferpy.internal import jsonx
from kniferpy.verr import DecodeError


def parse(value: str | bytes | bytearray) -> Any:
    return jsonx.loads(value)


def parse_obj(value: str | bytes | bytearray) -> dict[str, Any]:
    parsed = parse(value)
    if not isinstance(parsed, dict):
        raise DecodeError("JSON value is not an object", code="json.not_object")
    return parsed


def parse_array(value: str | bytes | bytearray) -> list[Any]:
    parsed = parse(value)
    if not isinstance(parsed, list):
        raise DecodeError("JSON value is not an array", code="json.not_array")
    return parsed


def dumps(value: Any) -> str:
    return jsonx.dumps(value)


def dumps_pretty(value: Any) -> str:
    return jsonx.dumps(value, pretty=True)


def get_path(obj: Any, path: str, *, default: Any = None) -> Any:
    return jsonx.get_path(obj, path, default=default)


def get_str(obj: Any, path: str, *, default: str | None = None) -> str | None:
    return jsonx.get_str(obj, path, default=default)


def get_int(obj: Any, path: str, *, default: int | None = None) -> int | None:
    return jsonx.get_int(obj, path, default=default)


def get_float(obj: Any, path: str, *, default: float | None = None) -> float | None:
    return jsonx.get_float(obj, path, default=default)


def get_bool(obj: Any, path: str, *, default: bool | None = None) -> bool | None:
    return jsonx.get_bool(obj, path, default=default)


def get_list(obj: Any, path: str, *, default: list[Any] | None = None) -> list[Any] | None:
    return jsonx.get_list(obj, path, default=default)


def get_dict(
    obj: Any,
    path: str,
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return jsonx.get_dict(obj, path, default=default)


def has_path(obj: Any, path: str) -> bool:
    return jsonx.has_path(obj, path)


def is_valid(value: str | bytes | bytearray) -> bool:
    return jsonx.is_valid(value)


def read(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> Any:
    return jsonx.read(path, encoding=encoding, max_bytes=max_bytes)


def read_obj(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = 1_048_576,
) -> dict[str, Any]:
    return jsonx.read_obj(path, encoding=encoding, max_bytes=max_bytes)


def write(
    path: str | Path,
    value: Any,
    *,
    pretty: bool = True,
    encoding: str = "utf-8",
) -> None:
    jsonx.write(path, value, pretty=pretty, encoding=encoding)
