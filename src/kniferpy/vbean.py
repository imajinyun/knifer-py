"""Struct/map property mapping between dataclasses, objects, and dicts.

Copy matching properties between mappings, dataclasses, and plain objects with
tag/alias name matching and optional weak type conversion (string/number/bool
coercion, recursive dataclass/list/dict assignment). Field aliases come from
dataclass field ``metadata`` under the configured tag names, where a value may
be a Go-style tag string (``"name,alias=a|b"``, ``"-"`` to omit) or a list of
alias strings.

Use :func:`to_map`/:func:`fill_map` to materialize properties as a dict,
:func:`copy`/:func:`copy_properties` to copy between trusted values,
:func:`decode`/:func:`decode_result` when weak conversion is expected, and
:func:`merge`/:func:`merge_result` to apply several sources left to right.

Only the direct property-mapping core is ported. knifer-go's reflection-based
method/constructor discovery (``vref``), functional constructor options, and the
pluggable numeric/bool parser injection are intentionally omitted; pass an
:class:`Options` value and, when needed, a ``decode_hook`` for custom
conversions. Prefer :mod:`kniferpy.vjson` for JSON round-tripping.
"""

from __future__ import annotations

from typing import Any

from kniferpy.internal import beanx
from kniferpy.internal.beanx import DecodeHook, Options, Result

__all__ = [
    "DecodeHook",
    "Options",
    "Result",
    "compose_decode_hook",
    "copy",
    "copy_properties",
    "decode",
    "decode_result",
    "fill_map",
    "merge",
    "merge_result",
    "new_options",
    "string_to_datetime_hook",
    "string_to_timedelta_hook",
    "to_map",
    "to_struct",
]


def new_options() -> Options:
    """Return default mapping options (weak, case-insensitive)."""
    return beanx.new_options()


def to_map(src: Any, options: Options | None = None) -> dict[str, Any]:
    """Convert a mapping, dataclass, or object to ``dict[str, Any]`` (shallow)."""
    return beanx.to_map(src, options)


def fill_map(src: Any, dst: dict[str, Any], options: Options | None = None) -> None:
    """Copy properties from ``src`` into an existing dict."""
    beanx.fill_map(src, dst, options)


def copy_properties(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy matching properties from ``src`` into ``dst``."""
    beanx.copy_properties(src, dst, options)


def copy(src: Any, dst: Any, options: Options | None = None) -> None:
    """Alias of :func:`copy_properties`."""
    beanx.copy(src, dst, options)


def to_struct(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy properties from ``src`` into a dataclass or object ``dst``."""
    beanx.to_struct(src, dst, options)


def decode(src: Any, dst: Any, options: Options | None = None) -> None:
    """Copy matching properties applying weak type conversion."""
    beanx.decode(src, dst, options)


def decode_result(src: Any, dst: Any, options: Options | None = None) -> Result:
    """Copy matching properties and report mapping metadata."""
    return beanx.decode_result(src, dst, options)


def merge(dst: Any, *sources: Any, options: Options | None = None) -> None:
    """Copy one or more sources into ``dst`` from left to right."""
    beanx.merge(dst, *sources, options=options)


def merge_result(dst: Any, *sources: Any, options: Options | None = None) -> Result:
    """Copy sources into ``dst`` left to right and report aggregate metadata."""
    return beanx.merge_result(dst, *sources, options=options)


def compose_decode_hook(*hooks: DecodeHook | None) -> DecodeHook:
    """Chain decode hooks from left to right."""
    return beanx.compose_decode_hook(*hooks)


def string_to_datetime_hook(fmt: str) -> DecodeHook:
    """Convert ``str`` values to :class:`~datetime.datetime` using ``fmt``."""
    return beanx.string_to_datetime_hook(fmt)


def string_to_timedelta_hook() -> DecodeHook:
    """Convert ``str`` values to :class:`~datetime.timedelta`.

    Supports formats like ``"1h30m"``, ``"2d"``, ``"30s"``.
    """
    return beanx.string_to_timedelta_hook()
