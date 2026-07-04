from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kniferpy.verr import DecodeError, JSONError


# ========== Null ==========


class _NullType:
    _instance: _NullType | None = None

    def __new__(cls) -> _NullType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "null"

    def __bool__(self) -> bool:
        return False


Null: Any = _NullType()


def is_null(v: Any) -> bool:
    return v is None or v is Null


# ========== Config ==========


class Config:
    def __init__(
        self,
        *,
        ignore_null_value: bool = False,
        ignore_case: bool = False,
        ignore_error: bool = False,
        date_format: str = "",
        indent_factor: int = 0,
    ) -> None:
        self.ignore_null_value = ignore_null_value
        self.ignore_case = ignore_case
        self.ignore_error = ignore_error
        self.date_format = date_format
        self.indent_factor = indent_factor

    def clone(self) -> Config:
        return Config(
            ignore_null_value=self.ignore_null_value,
            ignore_case=self.ignore_case,
            ignore_error=self.ignore_error,
            date_format=self.date_format,
            indent_factor=self.indent_factor,
        )


# ========== JSONObject ==========


class JSONObject:
    def __init__(self, cfg: Config | None = None) -> None:
        self._cfg = cfg or Config()
        self._keys: list[str] = []
        self._values: dict[str, Any] = {}
        self._key_map: dict[str, str] = {}

    def config(self) -> Config:
        return self._cfg

    def len(self) -> int:
        return len(self._keys)

    def keys(self) -> list[str]:
        return list(self._keys)

    def has(self, key: str) -> bool:
        if self._cfg.ignore_case:
            return key.lower() in self._key_map
        return key in self._values

    def _normalize_key(self, key: str) -> str:
        if self._cfg.ignore_case:
            lower = key.lower()
            if lower in self._key_map:
                return self._key_map[lower]
            self._key_map[lower] = key
        return key

    def get(self, key: str) -> tuple[Any, bool]:
        if self._cfg.ignore_case:
            lower = key.lower()
            if lower in self._key_map:
                v = self._values.get(self._key_map[lower])
                return v, v is not None or self._key_map[lower] in self._values
            return None, False
        if key in self._values:
            return self._values[key], True
        return None, False

    def get_or_default(self, key: str, default: Any = None) -> Any:
        v, ok = self.get(key)
        return v if ok else default

    def is_null(self, key: str) -> bool:
        v, ok = self.get(key)
        return ok and is_null(v)

    def set(self, key: str, value: Any) -> JSONObject:
        norm = self._normalize_key(key)
        if norm not in self._values:
            self._keys.append(norm)
        self._values[norm] = value
        return self

    def put(self, key: str, value: Any) -> JSONObject:
        return self.set(key, value)

    def remove(self, key: str) -> bool:
        if self._cfg.ignore_case:
            lower = key.lower()
            if lower in self._key_map:
                original = self._key_map.pop(lower)
                self._keys.remove(original)
                self._values.pop(original, None)
                return True
            return False
        if key in self._values:
            self._keys.remove(key)
            self._values.pop(key, None)
            return True
        return False

    def for_each(self, fn: Callable[[str, Any], bool]) -> None:
        for k in self._keys:
            if not fn(k, self._values.get(k)):
                break

    def to_map(self) -> dict[str, Any]:
        return {k: self._values[k] for k in self._keys}

    def get_string(self, key: str) -> str:
        v, _ = self.get(key)
        if isinstance(v, str):
            return v
        if self._cfg.ignore_error:
            return ""
        return ""

    def get_string_or(self, key: str, default: str) -> str:
        v, ok = self.get(key)
        if ok and isinstance(v, str):
            return v
        return default

    def get_int(self, key: str) -> int:
        v, _ = self.get(key)
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        if isinstance(v, float):
            return int(v)
        return 0

    def get_int_or(self, key: str, default: int) -> int:
        v, ok = self.get(key)
        if ok and isinstance(v, int) and not isinstance(v, bool):
            return v
        return default

    def get_int64(self, key: str) -> int:
        return self.get_int(key)

    def get_int64_or(self, key: str, default: int) -> int:
        return self.get_int_or(key, default)

    def get_float64(self, key: str) -> float:
        v, _ = self.get(key)
        if isinstance(v, int | float) and not isinstance(v, bool):
            return float(v)
        return 0.0

    def get_float64_or(self, key: str, default: float) -> float:
        v, ok = self.get(key)
        if ok and isinstance(v, int | float) and not isinstance(v, bool):
            return float(v)
        return default

    def get_bool(self, key: str) -> bool:
        v, _ = self.get(key)
        if isinstance(v, bool):
            return v
        return False

    def get_bool_or(self, key: str, default: bool) -> bool:
        v, ok = self.get(key)
        if ok and isinstance(v, bool):
            return v
        return default

    def get_json_object(self, key: str) -> JSONObject | None:
        v, ok = self.get(key)
        if ok and isinstance(v, JSONObject):
            return v
        if ok and isinstance(v, dict):
            return _from_dict(v, self._cfg)
        return None

    def get_json_array(self, key: str) -> JSONArray | None:
        v, ok = self.get(key)
        if ok and isinstance(v, JSONArray):
            return v
        if ok and isinstance(v, list):
            return _list_from(v, self._cfg)
        return None

    def get_by_path(self, path: str) -> Any:
        return get_path(self.to_map(), path)

    def put_by_path(self, path: str, value: Any) -> None:
        # Implement via internal dict manipulation
        _put_by_path_internal(self._values, self._keys, self._key_map, self._cfg, path, value)

    def to_string(self) -> str:
        return dumps(self.to_map(), pretty=False)

    def to_string_pretty(self) -> str:
        return dumps(self.to_map(), pretty=True)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return self.to_string()


def _put_by_path_internal(
    values: dict[str, Any],
    keys: list[str],
    key_map: dict[str, str],
    cfg: Config,
    path: str,
    value: Any,
) -> None:
    parts = path.split(".")
    if len(parts) == 1:
        obj = JSONObject(cfg)
        for k in keys:
            obj._values[k] = values.get(k)
            obj._keys.append(k)
        obj.set(parts[0], value)
        # Copy back
        keys.clear()
        key_map.clear()
        values.clear()
        for k in obj._keys:
            keys.append(k)
            values[k] = obj._values[k]
            if cfg.ignore_case:
                key_map[k.lower()] = k
        return
    # Nested path
    first = parts[0]
    rest = ".".join(parts[1:])
    if first not in values:
        from kniferpy.verr import JSONError as _JSONError

        raise _JSONError(f"path not found: {first}", code="json.path_not_found")
    child = values[first]
    if isinstance(child, dict):
        child_obj = _from_dict(child, cfg)
        child_obj.put_by_path(rest, value)
        values[first] = child_obj.to_map()
    elif isinstance(child, JSONObject):
        child.put_by_path(rest, value)
    else:
        raise _JSONError(f"cannot put into non-object at {first}", code="json.not_object")


def _from_dict(d: dict[str, Any], cfg: Config | None = None) -> JSONObject:
    obj = JSONObject(cfg)
    for k, v in d.items():
        obj.set(k, v)
    return obj


def _list_from(lst: list[Any], cfg: Config | None = None) -> JSONArray:
    arr = JSONArray(cfg)
    for v in lst:
        arr.add(v)
    return arr


# ========== JSONArray ==========


class JSONArray:
    def __init__(self, cfg: Config | None = None) -> None:
        self._cfg = cfg or Config()
        self._values: list[Any] = []

    def config(self) -> Config:
        return self._cfg

    def len(self) -> int:
        return len(self._values)

    def get(self, i: int) -> tuple[Any, bool]:
        if 0 <= i < len(self._values):
            return self._values[i], True
        return None, False

    def get_or_default(self, i: int, default: Any = None) -> Any:
        v, ok = self.get(i)
        return v if ok else default

    def is_null(self, i: int) -> bool:
        v, ok = self.get(i)
        return ok and is_null(v)

    def add(self, value: Any) -> JSONArray:
        self._values.append(value)
        return self

    def add_all(self, *values: Any) -> JSONArray:
        for v in values:
            self._values.append(v)
        return self

    def set(self, i: int, value: Any) -> JSONArray:
        if 0 <= i < len(self._values):
            self._values[i] = value
        return self

    def insert(self, i: int, value: Any) -> JSONArray:
        self._values.insert(i, value)
        return self

    def remove(self, i: int) -> bool:
        if 0 <= i < len(self._values):
            self._values.pop(i)
            return True
        return False

    def range(self, fn: Callable[[int, Any], bool]) -> None:
        for i, v in enumerate(self._values):
            if not fn(i, v):
                break

    def to_slice(self) -> list[Any]:
        return list(self._values)

    def join(self, sep: str) -> str:
        return sep.join(str(v) for v in self._values)

    def get_string(self, i: int) -> str:
        v, ok = self.get(i)
        if ok and isinstance(v, str):
            return v
        return ""

    def get_string_or(self, i: int, default: str) -> str:
        v, ok = self.get(i)
        if ok and isinstance(v, str):
            return v
        return default

    def get_int(self, i: int) -> int:
        v, ok = self.get(i)
        if ok and isinstance(v, int) and not isinstance(v, bool):
            return v
        return 0

    def get_int64(self, i: int) -> int:
        return self.get_int(i)

    def get_int64_or(self, i: int, default: int) -> int:
        v, ok = self.get(i)
        if ok and isinstance(v, int) and not isinstance(v, bool):
            return v
        return default

    def get_float64(self, i: int) -> float:
        v, ok = self.get(i)
        if ok and isinstance(v, int | float) and not isinstance(v, bool):
            return float(v)
        return 0.0

    def get_float64_or(self, i: int, default: float) -> float:
        v, ok = self.get(i)
        if ok and isinstance(v, int | float) and not isinstance(v, bool):
            return float(v)
        return default

    def get_bool(self, i: int) -> bool:
        v, ok = self.get(i)
        if ok and isinstance(v, bool):
            return v
        return False

    def get_bool_or(self, i: int, default: bool) -> bool:
        v, ok = self.get(i)
        if ok and isinstance(v, bool):
            return v
        return default

    def get_json_object(self, i: int) -> JSONObject | None:
        v, ok = self.get(i)
        if ok and isinstance(v, JSONObject):
            return v
        if ok and isinstance(v, dict):
            return _from_dict(v, self._cfg)
        return None

    def get_json_array(self, i: int) -> JSONArray | None:
        v, ok = self.get(i)
        if ok and isinstance(v, JSONArray):
            return v
        if ok and isinstance(v, list):
            return _list_from(v, self._cfg)
        return None

    def get_by_path(self, path: str) -> Any:
        return get_path(self._values, path)

    def put_by_path(self, path: str, value: Any) -> None:
        parts = path.split(".")
        if len(parts) == 1 and parts[0].isdigit():
            idx = int(parts[0])
            if 0 <= idx < len(self._values):
                self._values[idx] = value
            return
        first = parts[0]
        rest = ".".join(parts[1:])
        if first.isdigit():
            idx = int(first)
            if 0 <= idx < len(self._values):
                child = self._values[idx]
                if isinstance(child, dict):
                    child_obj = _from_dict(child, self._cfg)
                    child_obj.put_by_path(rest, value)
                    self._values[idx] = child_obj.to_map()
                elif isinstance(child, JSONObject):
                    child.put_by_path(rest, value)
                elif isinstance(child, list):
                    child_arr = _list_from(child, self._cfg)
                    child_arr.put_by_path(rest, value)
                    self._values[idx] = child_arr.to_slice()
                elif isinstance(child, JSONArray):
                    child.put_by_path(rest, value)

    def to_string(self) -> str:
        return dumps(self._values, pretty=False)

    def to_string_pretty(self) -> str:
        return dumps(self._values, pretty=True)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return self.to_string()


# ========== Parse / Serialize ==========


def loads(value: str | bytes | bytearray) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise JSONError(str(exc), code="json.invalid") from exc


def dumps(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def to_json_str(v: Any, *, pretty: bool = False, indent: int = 0) -> str:
    if indent > 0:
        return json.dumps(v, ensure_ascii=False, indent=indent, sort_keys=True)
    return dumps(v, pretty=pretty)


def quote(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


# ========== Path access ==========


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


def put_by_path(obj: Any, path: str, value: Any) -> Any:
    parts = path.split(".")
    if isinstance(obj, dict):
        _put_by_path_dict(obj, parts, value)
    elif isinstance(obj, list):
        _put_by_path_list(obj, parts, value)
    return obj


def _put_by_path_dict(d: dict[str, Any], parts: list[str], value: Any) -> None:
    current = d
    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        if not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _put_by_path_list(lst: list[Any], parts: list[str], value: Any) -> None:
    if not parts or not parts[0].isdigit():
        return
    idx = int(parts[0])
    if len(parts) == 1:
        if 0 <= idx < len(lst):
            lst[idx] = value
        return
    if idx >= len(lst):
        return
    child = lst[idx]
    if isinstance(child, dict):
        _put_by_path_dict(child, parts[1:], value)
    elif isinstance(child, list):
        _put_by_path_list(child, parts[1:], value)


# ========== Typed getters ==========


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


# ========== Validation ==========


def is_valid(value: str | bytes | bytearray) -> bool:
    return is_json(value)


def is_json(s: str) -> bool:
    try:
        json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return False
    return True


def is_json_obj(s: str) -> bool:
    try:
        v = json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return False
    return isinstance(v, dict)


def is_json_array(s: str) -> bool:
    try:
        v = json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return False
    return isinstance(v, list)


# ========== File I/O ==========


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
        raise JSONError("JSON value is not an object", code="json.not_object")
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


# ========== Bean conversion ==========


def to_bean(src: Any, dst: type) -> Any:
    if isinstance(src, dict):
        return _dict_to_bean(src, dst)
    if isinstance(src, str):
        try:
            parsed = json.loads(src)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return _dict_to_bean(parsed, dst)
        return None
    return None


def _dict_to_bean(d: dict[str, Any], dst: type) -> Any:
    import dataclasses
    import inspect

    try:
        hints = {}
        for cls in dst.__mro__:
            if hasattr(cls, "__annotations__"):
                hints.update(cls.__annotations__)
        kwargs: dict[str, Any] = {}
        for field_name, field_type in hints.items():
            if field_name in d:
                kwargs[field_name] = d[field_name]
        return dst(**kwargs)
    except (TypeError, ValueError):
        return None


def to_list(src: Any, item_type: type) -> list[Any]:
    result: list[Any] = []
    if isinstance(src, list):
        for item in src:
            if isinstance(item, dict):
                bean = to_bean(item, item_type)
                if bean is not None:
                    result.append(bean)
            else:
                result.append(item)
    return result


# ========== Format ==========


def format_json_str(raw: str, *, indent: int = 2) -> str:
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    return json.dumps(parsed, ensure_ascii=False, indent=indent, sort_keys=True)


# ========== ParseObj / ParseArray ==========


def parse_obj(value: str | bytes | bytearray) -> dict[str, Any]:
    parsed = loads(value)
    if not isinstance(parsed, dict):
        raise JSONError("JSON value is not an object", code="json.not_object")
    return parsed


def parse_array(value: str | bytes | bytearray) -> list[Any]:
    parsed = loads(value)
    if not isinstance(parsed, list):
        raise JSONError("JSON value is not an array", code="json.not_array")
    return parsed


# ========== New constructors ==========


def new_json_object(cfg: Config | None = None) -> JSONObject:
    return JSONObject(cfg)


def new_json_array(cfg: Config | None = None) -> JSONArray:
    return JSONArray(cfg)


def new_config(**kwargs: Any) -> Config:
    return Config(**kwargs)


# ========== XML to JSON / JSON to XML ==========


def xml_to_json(xml_str: str) -> dict[str, Any]:
    """Parse XML string into a JSON object."""
    from kniferpy.internal.xmlx import to_map as xml_to_map
    return xml_to_map(xml_str)


def json_to_xml(data: dict[str, Any], root_tag: str = "root", *, pretty: bool = False) -> str:
    """Serialize a JSON value to an XML string."""
    from kniferpy.internal.xmlx import to_xml as xml_to_xml_str
    return xml_to_xml_str(data, root_tag, pretty=pretty)


# ========== GetByPathOr ==========


def to_pretty_str(v: Any) -> str:
    """Serialize to pretty-printed JSON string."""
    return dumps(v, pretty=True)


def to_str_indent(v: Any, indent: int = 2) -> str:
    """Serialize to JSON string with specified indent."""
    return to_json_str(v, indent=indent)


def to_str_with_config(v: Any, cfg: Config) -> str:
    """Serialize to JSON string using Config."""
    return to_json_str(v, indent=cfg.indent)


def new_json_error(format_str: str, *args: Any) -> JSONError:
    """Create a JSONError with formatted message."""
    return JSONError(format_str % args)


def wrap_json_error(cause: Exception, format_str: str, *args: Any) -> JSONError:
    """Create a JSONError wrapping an existing exception."""
    return JSONError(format_str % args)


def get_by_path_or(data: Any, path: str, default: Any = None) -> Any:
    """Get value by JSON path expression with a default fallback."""
    result = get_by_path(data, path)
    return result if result is not None else default