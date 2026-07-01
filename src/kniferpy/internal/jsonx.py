from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kniferpy.verr import DecodeError


def loads(value: str | bytes | bytearray) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise DecodeError(str(exc), code="json.invalid", context={"position": exc.pos}) from exc


def dumps(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def get_path(obj: Any, path: str, *, default: Any = None) -> Any:
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return default
            index = int(part)
            if index >= len(current):
                return default
            current = current[index]
            continue
        return default
    return current


def get_str(obj: Any, path: str, *, default: str | None = None) -> str | None:
    value = get_path(obj, path, default=default)
    return value if isinstance(value, str) else default


def get_int(obj: Any, path: str, *, default: int | None = None) -> int | None:
    value = get_path(obj, path, default=default)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def get_float(obj: Any, path: str, *, default: float | None = None) -> float | None:
    value = get_path(obj, path, default=default)
    if isinstance(value, bool):
        return default
    return float(value) if isinstance(value, int | float) else default


def get_bool(obj: Any, path: str, *, default: bool | None = None) -> bool | None:
    value = get_path(obj, path, default=default)
    return value if isinstance(value, bool) else default


def get_list(obj: Any, path: str, *, default: list[Any] | None = None) -> list[Any] | None:
    value = get_path(obj, path, default=default)
    return value if isinstance(value, list) else default


def get_dict(
    obj: Any,
    path: str,
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    value = get_path(obj, path, default=default)
    return value if isinstance(value, dict) else default


def has_path(obj: Any, path: str) -> bool:
    missing = object()
    return get_path(obj, path, default=missing) is not missing


def is_valid(value: str | bytes | bytearray) -> bool:
    try:
        loads(value)
    except DecodeError:
        return False
    return True


def read(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> Any:
    from kniferpy.internal import filex

    return loads(filex.read_text(path, encoding=encoding, max_bytes=max_bytes))


def read_obj(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = 1_048_576,
) -> dict[str, Any]:
    parsed = read(path, encoding=encoding, max_bytes=max_bytes)
    if not isinstance(parsed, dict):
        raise DecodeError("JSON value is not an object", code="json.not_object")
    return parsed


def write(
    path: str | Path,
    value: Any,
    *,
    pretty: bool = True,
    encoding: str = "utf-8",
) -> None:
    from kniferpy.internal import filex

    filex.write_text(path, dumps(value, pretty=pretty), encoding=encoding)
