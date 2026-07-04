from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from kniferpy.internal import objx

T = TypeVar("T")
R = TypeVar("R")

__all__ = [
    "CodecOption",
    "Decoder",
    "Encoder",
    "Option",
    "apply",
    "accept",
    "clone",
    "clone_by_stream",
    "clone_by_stream_with_options",
    "clone_if_possible",
    "clone_if_possible_with_options",
    "clone_with_options",
    "compare",
    "compare_none",
    "contains",
    "default_if_none",
    "default_if_none_apply",
    "default_if_none_func",
    "deserialize",
    "deserialize_to",
    "deserialize_to_with_options",
    "deserialize_with_options",
    "empty_count",
    "equal",
    "equals",
    "has_empty",
    "has_none",
    "has_null",
    "is_all_empty",
    "is_all_not_empty",
    "is_basic_type",
    "is_empty",
    "is_nil",
    "is_not_empty",
    "is_not_nil",
    "is_not_null",
    "is_not_none",
    "is_null",
    "is_none",
    "is_valid_if_number",
    "length",
    "must_deserialize",
    "not_equal",
    "register",
    "register_name",
    "serialize",
    "serialize_or_nil",
    "serialize_or_nil_with_options",
    "serialize_with_options",
    "to_string",
    "type_name",
    "type_of",
    "validate_accepted_types",
    "with_decoder_factory",
    "with_encoder_factory",
]

# ── Go-compat type aliases ────────────────────────────────────────────────────

Option = Callable[[Any], None]
"""Functional option for object serialization (Go compat)."""

Encoder = Callable[[Any], None]
"""Functional option for serialization encoder (Go compat)."""

Decoder = Callable[[Any], None]
"""Functional option for deserialization decoder (Go compat)."""

CodecOption = Callable[[Any], None]
"""Functional option for per-call codec configuration (Go compat)."""


def equal(a: object, b: object) -> bool:
    return objx.equal(a, b)


def not_equal(a: object, b: object) -> bool:
    return objx.not_equal(a, b)


def length(v: object) -> int:
    return objx.length(v)


def contains(obj: object, element: object) -> bool:
    return objx.contains(obj, element)


def is_none(v: object) -> bool:
    return objx.is_none(v)


def is_not_none(v: object) -> bool:
    return objx.is_not_none(v)


def is_empty(v: object) -> bool:
    return objx.is_empty(v)


def is_not_empty(v: object) -> bool:
    return objx.is_not_empty(v)


def default_if_none(value: T | None, default: T) -> T:
    return objx.default_if_none(value, default)


def default_if_none_func(value: T | None, supplier: Callable[[], T]) -> T:
    return objx.default_if_none_func(value, supplier)


def default_if_none_apply(source: T | None, handle: Callable[[T], R], default: R) -> R:
    return objx.default_if_none_apply(source, handle, default)


def apply(source: T | None, handle: Callable[[T], R]) -> R | None:
    return objx.apply(source, handle)


def accept(source: T | None, consumer: Callable[[T], None]) -> None:
    objx.accept(source, consumer)


def is_basic_type(obj: object) -> bool:
    return objx.is_basic_type(obj)


def is_valid_if_number(obj: object) -> bool:
    return objx.is_valid_if_number(obj)


def compare(a: object, b: object) -> int:
    return objx.compare(a, b)


def compare_none(a: object, b: object, none_greater: bool) -> int:
    return objx.compare_none(a, b, none_greater)


def type_of(obj: object) -> type | None:
    return objx.type_of(obj)


def type_name(obj: object) -> str:
    return objx.type_name(obj)


def to_string(obj: object) -> str:
    return objx.to_string(obj)


def empty_count(*values: object) -> int:
    return objx.empty_count(*values)


def has_none(*values: object) -> bool:
    return objx.has_none(*values)


def has_empty(*values: object) -> bool:
    return objx.has_empty(*values)


def is_all_empty(*values: object) -> bool:
    return objx.is_all_empty(*values)


def is_all_not_empty(*values: object) -> bool:
    return objx.is_all_not_empty(*values)


def equals(a: object, b: object) -> bool:
    return objx.equals(a, b)


def is_null(v: object) -> bool:
    return objx.is_null(v)


def is_not_null(v: object) -> bool:
    return objx.is_not_null(v)


def is_nil(v: object) -> bool:
    return objx.is_nil(v)


def is_not_nil(v: object) -> bool:
    return objx.is_not_nil(v)


def has_null(*values: object) -> bool:
    return objx.has_null(*values)


# ── Clone / serialize / deserialize / register ────────────────────────────


def clone(src: T) -> T:
    """Deep copy through pickle serialization."""
    return objx.clone(src)


def clone_if_possible(src: T) -> T:
    """Return cloned value, or src on failure."""
    return objx.clone_if_possible(src)


def clone_by_stream(src: T) -> T:
    """Deep copy through pickle serialization (alias of clone)."""
    return objx.clone_by_stream(src)


def serialize(obj: T) -> bytes:
    """Encode obj to bytes using the configured encoder."""
    return objx.serialize(obj)


def serialize_or_nil(obj: T) -> bytes | None:
    """Encode obj to bytes, returning None on failure."""
    return objx.serialize_or_nil(obj)


def deserialize(data: bytes, out_type: type, *accepted_types: type) -> object:
    """Decode data into an object, optionally validating accepted types."""
    return objx.deserialize(data, out_type, accepted_types)


def deserialize_to(data: bytes, *accepted_types: type) -> T:
    """Decode data into a new value."""
    return objx.deserialize_to(data, accepted_types)


def must_deserialize(data: bytes, *accepted_types: type) -> T:
    """Decode data or raise."""
    return objx.must_deserialize(data, accepted_types)


def register(value: type) -> None:
    """Record a concrete type for type-registry encoding."""
    objx.register(value)


def register_name(name: str, value: type) -> None:
    """Record a concrete type with a custom name."""
    objx.register_name(name, value)


def validate_accepted_types(value: object, *accepted_types: type) -> None:
    """Check whether value only contains built-in safe types plus accepted types."""
    objx.validate_accepted_types(value, *accepted_types)


def with_encoder_factory(factory: Callable[[], Callable[[object], bytes]]) -> None:
    """Set the encoder factory for serialization."""
    objx.with_encoder_factory(factory)


def with_decoder_factory(factory: Callable[[], Callable[[bytes], object]]) -> None:
    """Set the decoder factory for deserialization."""
    objx.with_decoder_factory(factory)


# ── WithOptions aliases (Go compat) ──────────────────────────────────────────

clone_with_options = clone
clone_if_possible_with_options = clone_if_possible
clone_by_stream_with_options = clone_by_stream
serialize_with_options = serialize
serialize_or_nil_with_options = serialize_or_nil
deserialize_with_options = deserialize
deserialize_to_with_options = deserialize_to
