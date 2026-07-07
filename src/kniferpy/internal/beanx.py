from __future__ import annotations

import dataclasses
import types
import typing
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from kniferpy.internal import convx
from kniferpy.verr import ValidationError

# A hook transforms a source value before assignment. It receives the source
# type (or None for a None value), the destination type (a concrete type or a
# typing construct), and the value, and returns the transformed value.
DecodeHook = Callable[[type | None, Any, Any], Any]

_NONE_TYPE = type(None)


@dataclass(frozen=True)
class Options:
    """Controls how properties are matched and converted between values.

    Field aliases are read from dataclass field ``metadata`` under the
    configured ``tag_names``; a metadata value may be a Go-style tag string
    (``"name,alias=a|b"`` or ``"-"`` to omit) or a list of alias strings.
    """

    tag_names: tuple[str, ...] = ("bean", "json", "alias")
    weakly_typed: bool = True
    case_insensitive: bool = True
    ignore_empty: bool = False
    ignore_zero: bool = False
    strict_unused: bool = False
    decode_hook: DecodeHook | None = None


@dataclass
class Result:
    """Reports which source properties were consumed, skipped, or left unused."""

    matched: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    unused: list[str] = field(default_factory=list)

    def sort(self) -> None:
        self.matched.sort()
        self.skipped.sort()
        self.unused.sort()


def new_options() -> Options:
    """Return default mapping options (weak, case-insensitive)."""
    return Options()


# --- Errors -------------------------------------------------------------------


def _invalid(message: str) -> ValidationError:
    return ValidationError(message=message, code="knifer.bean.invalid_input")


def _convert_error(message: str, cause: BaseException | None = None) -> ValidationError:
    context = {"cause": str(cause)} if cause is not None else {}
    return ValidationError(message=message, code="knifer.bean.convert", context=context)


# --- Property model -----------------------------------------------------------


@dataclass
class _Property:
    name: str
    aliases: tuple[str, ...]
    value: Any


@dataclass
class _Field:
    attr: str
    name: str
    aliases: tuple[str, ...]
    type: Any


def _split_aliases(text: str) -> list[str]:
    parts: list[str] = []
    for chunk in text.replace(";", "|").split("|"):
        trimmed = chunk.strip()
        if trimmed:
            parts.append(trimmed)
    return parts


def _unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _resolve_field_names(
    f: dataclasses.Field[Any], cfg: Options
) -> tuple[str, tuple[str, ...], bool]:
    """Return ``(name, aliases, omit)`` for a dataclass field using tag metadata."""
    name = f.name
    aliases = [f.name]
    for tag in cfg.tag_names:
        raw = f.metadata.get(tag)
        if not raw:
            continue
        if isinstance(raw, str):
            parts = raw.split(",")
            primary = parts[0].strip()
            if primary == "-":
                return "", (), True
            if primary:
                name = primary
                aliases.append(primary)
            for part in parts[1:]:
                part = part.strip()
                for prefix in ("alias=", "aliases="):
                    if part.startswith(prefix):
                        aliases.extend(_split_aliases(part[len(prefix) :]))
        elif isinstance(raw, (list, tuple)):
            aliases.extend(str(item) for item in raw)
    return name, _unique([name, *aliases]), False


def _type_hints(cls: type) -> dict[str, Any]:
    try:
        return typing.get_type_hints(cls)
    except Exception:
        return {}


def _collect_properties(src: Any, cfg: Options) -> list[_Property]:
    if src is None:
        raise _invalid("bean: src is None")
    if isinstance(src, Mapping):
        return [_Property(str(k), (str(k),), v) for k, v in src.items()]
    if dataclasses.is_dataclass(src) and not isinstance(src, type):
        props: list[_Property] = []
        for f in dataclasses.fields(src):
            name, aliases, omit = _resolve_field_names(f, cfg)
            if omit:
                continue
            props.append(_Property(name, aliases, getattr(src, f.name)))
        return props
    if isinstance(src, (str, bytes, int, float, bool)):
        raise _invalid(f"bean: unsupported src type {type(src).__name__}")
    if hasattr(src, "__dict__"):
        return [_Property(k, (k,), v) for k, v in vars(src).items() if not k.startswith("_")]
    raise _invalid(f"bean: unsupported src type {type(src).__name__}")


def _target_fields(dst: Any, cfg: Options) -> list[_Field]:
    if dataclasses.is_dataclass(dst) and not isinstance(dst, type):
        hints = _type_hints(type(dst))
        fields: list[_Field] = []
        for f in dataclasses.fields(dst):
            name, aliases, omit = _resolve_field_names(f, cfg)
            if omit:
                continue
            fields.append(_Field(f.name, name, aliases, hints.get(f.name)))
        return fields
    hints = _type_hints(type(dst))
    names: list[str] = []
    seen: set[str] = set()
    for source in (hints.keys(), vars(dst).keys() if hasattr(dst, "__dict__") else ()):
        for attr in source:
            if attr.startswith("_") or attr in seen:
                continue
            seen.add(attr)
            names.append(attr)
    return [_Field(attr, attr, (attr,), hints.get(attr)) for attr in names]


# --- Matching helpers ---------------------------------------------------------


def _normalize(name: str, cfg: Options) -> str:
    name = name.strip()
    return name.lower() if cfg.case_insensitive else name


def _property_index(props: list[_Property], cfg: Options) -> dict[str, _Property]:
    index: dict[str, _Property] = {}
    for prop in props:
        for alias in _unique([prop.name, *prop.aliases]):
            index[_normalize(alias, cfg)] = prop
    return index


def _lookup(
    index: dict[str, _Property], aliases: tuple[str, ...], cfg: Options
) -> _Property | None:
    for alias in aliases:
        prop = index.get(_normalize(alias, cfg))
        if prop is not None:
            return prop
    return None


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, dict, set, frozenset)):
        return len(value) == 0
    return False


def _is_zero(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, dict, set, frozenset)):
        return len(value) == 0
    return not value


def _should_skip(value: Any, cfg: Options) -> bool:
    if cfg.ignore_empty and _is_empty(value):
        return True
    return bool(cfg.ignore_zero and _is_zero(value))


# --- Value conversion ---------------------------------------------------------


def _is_assignable(value: Any, target: type) -> bool:
    # bool is a subclass of int in Python; keep numeric coercion weak like Go.
    if target in (int, float) and isinstance(value, bool):
        return False
    try:
        return isinstance(value, target)
    except TypeError:
        return False


def _convert(value: Any, target: Any, cfg: Options) -> Any:
    origin = typing.get_origin(target)

    # Unwrap Optional[...] / X | None.
    if origin is typing.Union or origin is types.UnionType:
        args = typing.get_args(target)
        non_none = [a for a in args if a is not _NONE_TYPE]
        if value is None:
            return None
        if len(non_none) == 1:
            target = non_none[0]
            origin = typing.get_origin(target)
        else:
            return value

    if cfg.decode_hook is not None:
        to_type = target if isinstance(target, type) else (origin if origin is not None else target)
        value = cfg.decode_hook(type(value) if value is not None else None, to_type, value)
        origin = typing.get_origin(target)

    if target is None or target is Any:
        return value
    if value is None:
        return None

    if origin in (list, tuple, set, frozenset):
        return _convert_seq(value, target, origin, cfg)
    if origin is dict:
        return _convert_map(value, target, cfg)
    if not isinstance(target, type):
        return value

    if dataclasses.is_dataclass(target) and not isinstance(value, target):
        return _to_dataclass(value, target, cfg)
    if _is_assignable(value, target):
        return value
    if not cfg.weakly_typed:
        raise _convert_error(f"cannot assign {type(value).__name__} to {target.__name__}")

    try:
        if target is str:
            return convx.to_str(value)
        if target is bool:
            return convx.to_bool_e(value)
        if target is int:
            return convx.to_int_e(value)
        if target is float:
            return convx.to_float_e(value)
        if target is bytes:
            return convx.to_bytes(value)
    except (ValidationError, ValueError, TypeError) as exc:
        raise _convert_error(f"cannot convert to {target.__name__}", exc) from exc
    raise _convert_error(f"cannot assign {type(value).__name__} to {target.__name__}")


def _convert_seq(value: Any, target: Any, origin: Any, cfg: Options) -> Any:
    if not isinstance(value, (list, tuple, set, frozenset)):
        raise _convert_error(f"cannot assign {type(value).__name__} to {origin.__name__}")
    args = typing.get_args(target)
    if origin is tuple and args and args[-1] is not Ellipsis and len(args) == len(value):
        return tuple(_convert(item, arg, cfg) for item, arg in zip(value, args))
    elem_type: Any = None
    if args:
        elem_type = args[0]
    converted = [_convert(item, elem_type, cfg) for item in value]
    if origin is tuple:
        return tuple(converted)
    if origin is set:
        return set(converted)
    if origin is frozenset:
        return frozenset(converted)
    return converted


def _convert_map(value: Any, target: Any, cfg: Options) -> Any:
    if not isinstance(value, Mapping):
        is_dataclass_instance = dataclasses.is_dataclass(value) and not isinstance(value, type)
        if is_dataclass_instance or hasattr(value, "__dict__"):
            value = to_map(value, cfg)
        else:
            raise _convert_error(f"cannot assign {type(value).__name__} to dict")
    args = typing.get_args(target)
    key_type: Any = args[0] if len(args) >= 1 else None
    val_type: Any = args[1] if len(args) >= 2 else None
    return {_convert(k, key_type, cfg): _convert(v, val_type, cfg) for k, v in value.items()}


def _to_dataclass(value: Any, target: type, cfg: Options) -> Any:
    instance: Any = object.__new__(target)
    _copy_result(value, instance, cfg)
    return instance


# --- Core copy / fill ---------------------------------------------------------


def _fill_map_result(src: Any, dst: dict[str, Any], cfg: Options) -> Result:
    props = _collect_properties(src, cfg)
    result = Result()
    for prop in props:
        if _should_skip(prop.value, cfg):
            result.skipped.append(prop.name)
            continue
        dst[prop.name] = prop.value
        result.matched.append(prop.name)
    result.sort()
    return result


def _unused(props: list[_Property], used: set[str], cfg: Options) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for prop in props:
        if _normalize(prop.name, cfg) in used or prop.name in seen:
            continue
        seen.add(prop.name)
        out.append(prop.name)
    out.sort()
    return out


def _copy_result(src: Any, dst: Any, cfg: Options) -> Result:
    if dst is None:
        raise _invalid("bean: dst is None")
    if isinstance(dst, dict):
        return _fill_map_result(src, dst, cfg)
    if isinstance(dst, (str, bytes, int, float, bool)):
        raise _invalid("bean: dst must be a dict, dataclass, or object")

    props = _collect_properties(src, cfg)
    index = _property_index(props, cfg)
    used: set[str] = set()
    result = Result()
    for target in _target_fields(dst, cfg):
        prop = _lookup(index, target.aliases, cfg)
        if prop is None:
            continue
        used.add(_normalize(prop.name, cfg))
        if _should_skip(prop.value, cfg):
            result.skipped.append(prop.name)
            continue
        try:
            converted = _convert(prop.value, target.type, cfg)
        except ValidationError as exc:
            raise ValidationError(
                message=f"bean: set field {target.attr}: {exc.message}",
                code=exc.code or "knifer.bean.convert",
                context=exc.context,
            ) from exc
        setattr(dst, target.attr, converted)
        result.matched.append(prop.name)
    result.unused = _unused(props, used, cfg)
    result.sort()
    if cfg.strict_unused and result.unused:
        raise ValidationError(
            message="bean: unused source properties: " + ", ".join(result.unused),
            code="knifer.bean.unused",
        )
    return result


# --- Public API ---------------------------------------------------------------


def to_map(src: Any, options: Options | None = None) -> dict[str, Any]:
    """Convert a mapping, dataclass, or object to ``dict[str, Any]`` (shallow)."""
    out: dict[str, Any] = {}
    _fill_map_result(src, out, options or Options())
    return out


def fill_map(src: Any, dst: dict[str, Any], options: Options | None = None) -> None:
    """Copy properties from ``src`` into an existing dict."""
    if dst is None:
        raise _invalid("bean: dst map is None")
    _fill_map_result(src, dst, options or Options())


def copy_properties(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy matching properties from ``src`` into ``dst``."""
    _copy_result(src, dst, options or Options())


def copy(src: Any, dst: Any, options: Options | None = None) -> None:
    """Alias of :func:`copy_properties`."""
    _copy_result(src, dst, options or Options())


def to_struct(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy properties from ``src`` into a dataclass or object ``dst``."""
    _copy_result(src, dst, options or Options())


def decode(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy matching properties applying weak type conversion."""
    _copy_result(src, dst, options or Options())


def decode_result(src: Any, dst: Any, options: Options | None = None) -> Result:
    """Copy matching properties and report mapping metadata."""
    return _copy_result(src, dst, options or Options())


def merge_result(dst: Any, *sources: Any, options: Options | None = None) -> Result:
    """Copy sources into ``dst`` left to right and report aggregate metadata."""
    cfg = options or Options()
    result = Result()
    for src in sources:
        partial = _copy_result(src, dst, cfg)
        result.matched.extend(partial.matched)
        result.skipped.extend(partial.skipped)
        result.unused.extend(partial.unused)
    result.sort()
    return result


def merge(dst: Any, *sources: Any, options: Options | None = None) -> None:
    """Copy one or more sources into ``dst`` from left to right."""
    merge_result(dst, *sources, options=options)


# --- Decode hooks -------------------------------------------------------------


def compose_decode_hook(*hooks: DecodeHook | None) -> DecodeHook:
    """Chain decode hooks from left to right."""

    def hook(from_type: type | None, to_type: Any, value: Any) -> Any:
        current = value
        current_type = from_type
        for h in hooks:
            if h is None:
                continue
            current = h(current_type, to_type, current)
            current_type = type(current) if current is not None else None
        return current

    return hook


def string_to_datetime_hook(fmt: str) -> DecodeHook:
    """Convert ``str`` values to :class:`~datetime.datetime` using ``fmt``."""

    def hook(from_type: type | None, to_type: Any, value: Any) -> Any:
        if from_type is str and to_type is datetime:
            return datetime.strptime(value, fmt)
        return value

    return hook


def string_to_timedelta_hook() -> DecodeHook:
    """Convert ``str`` values to :class:`~datetime.timedelta`.

    Supports formats like ``"1h30m"``, ``"2d"``, ``"30s"``, ``"1h"``, ``"90m"``.
    """

    def hook(from_type: type | None, to_type: Any, value: Any) -> Any:
        if from_type is not str or to_type is not timedelta:
            return value
        value = value.strip()
        if not value:
            return timedelta(0)
        total = timedelta()
        buf = ""
        for ch in value:
            if ch.isalpha():
                unit = ch.lower()
                if not buf:
                    return value
                num = float(buf)
                buf = ""
                if unit == "d":
                    total += timedelta(days=num)
                elif unit == "h":
                    total += timedelta(hours=num)
                elif unit == "m":
                    total += timedelta(minutes=num)
                elif unit == "s":
                    total += timedelta(seconds=num)
                elif unit == "u" or unit == "µ":
                    total += timedelta(microseconds=num)
                elif unit == "w":
                    total += timedelta(weeks=num)
                else:
                    return value
            else:
                buf += ch
        return total

    return hook
