from __future__ import annotations

import math
import pickle
from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T")
R = TypeVar("R")

_SIZED = (str, bytes, bytearray, list, tuple, dict, set, frozenset, range)
_CONTAINERS = (list, tuple, set, frozenset)
_BASIC_TYPES = (bool, int, float, complex, str)


def equal(a: object, b: object) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(a == b)


def not_equal(a: object, b: object) -> bool:
    return not equal(a, b)


def length(v: object) -> int:
    if v is None:
        return 0
    try:
        return len(v)  # type: ignore[arg-type]
    except TypeError:
        return -1


def contains(obj: object, element: object) -> bool:
    if obj is None:
        return False
    if isinstance(obj, str):
        if element is None:
            return False
        return str(element) in obj
    if isinstance(obj, dict):
        return any(equal(value, element) for value in obj.values())
    if isinstance(obj, _CONTAINERS):
        return any(equal(item, element) for item in obj)
    return False


def is_none(v: object) -> bool:
    return v is None


def is_not_none(v: object) -> bool:
    return v is not None


def is_empty(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, _SIZED):
        return len(v) == 0
    try:
        return len(v) == 0  # type: ignore[arg-type]
    except TypeError:
        return False


def is_not_empty(v: object) -> bool:
    return not is_empty(v)


def default_if_none(value: T | None, default: T) -> T:
    return value if value is not None else default


def default_if_none_func(value: T | None, supplier: Callable[[], T]) -> T:
    return value if value is not None else supplier()


def default_if_none_apply(source: T | None, handle: Callable[[T], R], default: R) -> R:
    return handle(source) if source is not None else default


def apply(source: T | None, handle: Callable[[T], R]) -> R | None:
    return handle(source) if source is not None else None


def accept(source: T | None, consumer: Callable[[T], None]) -> None:
    if source is not None:
        consumer(source)


def is_basic_type(obj: object) -> bool:
    return isinstance(obj, _BASIC_TYPES)


def is_valid_if_number(obj: object) -> bool:
    if isinstance(obj, bool):
        return True
    if isinstance(obj, float):
        return not (math.isnan(obj) or math.isinf(obj))
    return True


def compare(a: object, b: object) -> int:
    return compare_none(a, b, True)


def compare_none(a: object, b: object, none_greater: bool) -> int:
    if a is None and b is None:
        return 0
    if a is None:
        return 1 if none_greater else -1
    if b is None:
        return -1 if none_greater else 1
    if a < b:  # type: ignore[operator]
        return -1
    if a > b:  # type: ignore[operator]
        return 1
    return 0


def type_of(obj: object) -> type | None:
    return None if obj is None else type(obj)


def type_name(obj: object) -> str:
    return "" if obj is None else type(obj).__name__


def to_string(obj: object) -> str:
    return "null" if obj is None else str(obj)


def empty_count(*values: object) -> int:
    return sum(1 for value in values if is_empty(value))


def has_none(*values: object) -> bool:
    return any(value is None for value in values)


def has_empty(*values: object) -> bool:
    return any(is_empty(value) for value in values)


def is_all_empty(*values: object) -> bool:
    return all(is_empty(value) for value in values)


def is_all_not_empty(*values: object) -> bool:
    return all(is_not_empty(value) for value in values)


def is_null(v: object) -> bool:
    return v is None


def is_not_null(v: object) -> bool:
    return v is not None


def has_null(*values: object) -> bool:
    return any(v is None for v in values)


def equals(a: object, b: object) -> bool:
    return equal(a, b)


def is_nil(v: object) -> bool:
    return v is None


def is_not_nil(v: object) -> bool:
    return v is not None


# ---------------------------------------------------------------------------
# Clone / serialize / deserialize / register (mirrors Go vobj gob-based API)
# ---------------------------------------------------------------------------

_CODEC_CONFIG: dict[str, Callable[[], Callable[..., object]]] = {}


def _default_encoder() -> Callable[[object], bytes]:
    return pickle.dumps


def _default_decoder() -> Callable[[bytes], object]:
    return pickle.loads


def with_encoder_factory(factory: Callable[[], Callable[[object], bytes]]) -> None:
    _CODEC_CONFIG["encoder_factory"] = factory


def with_decoder_factory(factory: Callable[[], Callable[[bytes], object]]) -> None:
    _CODEC_CONFIG["decoder_factory"] = factory


def _get_encoder() -> Callable[[object], bytes]:
    factory = _CODEC_CONFIG.get("encoder_factory")
    return cast(Callable[[object], bytes], factory()) if factory else _default_encoder()


def _get_decoder() -> Callable[[bytes], object]:
    factory = _CODEC_CONFIG.get("decoder_factory")
    return cast(Callable[[bytes], object], factory()) if factory else _default_decoder()


def clone(src: T) -> T:
    """Deep copy through pickle serialization."""
    return cast(T, _get_decoder()(_get_encoder()(src)))


def clone_if_possible(src: T) -> T:
    """Return cloned value, or src on failure."""
    try:
        return clone(src)
    except Exception:
        return src


def clone_by_stream(src: T) -> T:
    """Deep copy through pickle serialization (alias of clone)."""
    return clone(src)


def serialize(obj: T) -> bytes:
    """Encode obj to bytes using the configured encoder."""
    return _get_encoder()(obj)


def serialize_or_nil(obj: T) -> bytes | None:
    """Encode obj to bytes, returning None on failure."""
    try:
        return serialize(obj)
    except Exception:
        return None


def deserialize(data: bytes, out_type: type, accepted_types: tuple[type, ...] = ()) -> object:
    """Decode data into an object, optionally validating accepted types."""
    obj = _get_decoder()(data)
    if accepted_types:
        validate_accepted_types(obj, *accepted_types)
    return obj


def deserialize_to(data: bytes, accepted_types: tuple[type, ...] = ()) -> object:
    """Decode data into a new value."""
    return deserialize(data, object, accepted_types)


def must_deserialize(data: bytes, accepted_types: tuple[type, ...] = ()) -> object:
    """Decode data or raise."""
    return deserialize(data, object, accepted_types)


_REGISTERED_TYPES: dict[str, type] = {}


def register(value: type) -> None:
    """Record a concrete type for type-registry encoding."""
    _REGISTERED_TYPES[value.__name__] = value


def register_name(name: str, value: type) -> None:
    """Record a concrete type with a custom name."""
    _REGISTERED_TYPES[name] = value


def validate_accepted_types(value: object, *accepted_types: type) -> None:
    """Check whether value only contains built-in safe types plus accepted types."""
    _check_type(value, accepted_types)


def _check_type(value: object, accepted_types: tuple[type, ...]) -> None:
    from kniferpy.verr import SecurityError

    SAFE = (bool, int, float, complex, str, bytes, bytearray, type(None))
    if isinstance(value, (dict,)):
        if not all(isinstance(k, SAFE) for k in value):
            raise SecurityError("unsafe key type in deserialized data", code="knifer.unsafe_type")
        for v in value.values():
            _check_type(v, accepted_types)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            _check_type(v, accepted_types)
    elif isinstance(value, SAFE + accepted_types):
        pass
    else:
        raise SecurityError(
            f"unsafe type in deserialized data: {type(value).__name__}",
            code="knifer.unsafe_type",
        )
