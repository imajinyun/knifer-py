from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")
R = TypeVar("R")


# ---------------------------------------------------------------------------
# JSON option config
# ---------------------------------------------------------------------------


class _JSONConfig:
    def __init__(self) -> None:
        self.marshal: Callable[[Any], bytes] = lambda v: json.dumps(v).encode()
        self.unmarshal: Callable[[bytes], Any] = lambda b: json.loads(b.decode())


JSONOption = Callable[[_JSONConfig], None]


def _with_set_marshal_func(marshal: Callable[[Any], bytes]) -> JSONOption:
    def apply(cfg: _JSONConfig) -> None:
        cfg.marshal = marshal

    return apply


def _with_set_unmarshal_func(unmarshal: Callable[[bytes], Any]) -> JSONOption:
    def apply(cfg: _JSONConfig) -> None:
        cfg.unmarshal = unmarshal

    return apply


def _apply_json_options(opts: list[JSONOption]) -> _JSONConfig:
    cfg = _JSONConfig()
    for opt in opts:
        opt(cfg)
    return cfg


# ---------------------------------------------------------------------------
# generic Set
# ---------------------------------------------------------------------------


class Set(Generic[T]):
    """A generic hash set for comparable values."""

    def __init__(self, *items: T) -> None:
        self._data: dict[T, None] = {}
        if items:
            self.add(*items)

    def add(self, *items: T) -> None:
        for item in items:
            self._data[item] = None

    def remove(self, *items: T) -> None:
        for item in items:
            self._data.pop(item, None)

    def contains(self, item: T) -> bool:
        return item in self._data

    def sub(self, other: Set[T]) -> Set[T]:
        out: Set[T] = Set()
        for item in self._data:
            if not other.contains(item):
                out._data[item] = None
        return out

    def union(self, other: Set[T]) -> Set[T]:
        out: Set[T] = Set()
        for item in self._data:
            out._data[item] = None
        for item in other._data:
            out._data[item] = None
        return out

    def intersect(self, other: Set[T]) -> Set[T]:
        if len(other._data) < len(self._data):
            return other.intersect(self)
        out: Set[T] = Set()
        for item in self._data:
            if other.contains(item):
                out._data[item] = None
        return out

    def members(self) -> list[T]:
        return list(self._data.keys())

    def equal(self, other: Set[T]) -> bool:
        return self._data == other._data

    def __str__(self) -> str:
        return f"set{self.members()}"

    def __repr__(self) -> str:
        return self.__str__()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __contains__(self, item: T) -> bool:
        return self.contains(item)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Set):
            return False
        return self.equal(other)

    def __or__(self, other: Set[T]) -> Set[T]:
        return self.union(other)

    def __and__(self, other: Set[T]) -> Set[T]:
        return self.intersect(other)

    def __sub__(self, other: Set[T]) -> Set[T]:
        return self.sub(other)

    def to_json(self, opts: list[JSONOption] | None = None) -> str:
        if opts is None:
            opts = []
        cfg = _apply_json_options(opts)
        return cfg.marshal(self.members()).decode()

    @classmethod
    def from_json(cls, data: str, opts: list[JSONOption] | None = None) -> Set[T]:
        if opts is None:
            opts = []
        cfg = _apply_json_options(opts)
        items = cfg.unmarshal(data.encode())
        return cls(*items)

    def to_yaml(self) -> Any:
        """Return a YAML-serializable representation (list of members)."""
        try:
            import yaml  # type: ignore[import-untyped]

            return yaml.safe_dump(self.members(), default_flow_style=False)
        except ImportError:
            return self.members()

    @classmethod
    def from_yaml(cls, data: str) -> Set[T]:
        """Parse a YAML sequence into a Set."""
        try:
            import yaml

            items = yaml.safe_load(data)
        except ImportError:
            items = json.loads(data)
        if not isinstance(items, list):
            items = [items]
        return cls(*items)

    def to_slice(self) -> list[T]:
        return self.members()

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def size(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()

    def add_all(self, *items: T) -> None:
        self.add(*items)

    def remove_all(self, *items: T) -> None:
        self.remove(*items)

    def contains_all(self, *items: T) -> bool:
        return all(self.contains(i) for i in items)

    def is_subset(self, other: Set[T]) -> bool:
        return all(other.contains(i) for i in self._data)

    def is_superset(self, other: Set[T]) -> bool:
        return all(other.contains(i) for i in self._data)

    def symmetric_difference(self, other: Set[T]) -> Set[T]:
        return self.union(other).sub(self.intersect(other))

    def for_each(self, fn: Callable[[T], None]) -> None:
        for item in self._data:
            fn(item)

    def filter(self, fn: Callable[[T], bool]) -> Set[T]:
        out: Set[T] = Set()
        for item in self._data:
            if fn(item):
                out._data[item] = None
        return out

    def map(self, fn: Callable[[T], U]) -> Set[U]:
        out: Set[U] = Set()
        for item in self._data:
            out._data[fn(item)] = None
        return out

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        result = initial
        for item in self._data:
            result = fn(result, item)
        return result

    def clone(self) -> Set[T]:
        return Set(*self._data.keys())

    def difference(self, other: Set[T]) -> Set[T]:
        return self.sub(other)

    # ── JSON / YAML marshal (Go compat) ──────────────────────────────────────

    def marshal_json(self, opts: list[JSONOption] | None = None) -> bytes:
        """Encode the set as a JSON array."""
        cfg = _apply_json_options(opts or [])
        return cfg.marshal(self.members())

    def unmarshal_json(self, data: bytes | str, opts: list[JSONOption] | None = None) -> None:
        """Decode a JSON array into the set."""
        cfg = _apply_json_options(opts or [])
        items = cfg.unmarshal(data if isinstance(data, bytes) else data.encode())
        if isinstance(items, list):
            self.add(*items)

    def marshal_yaml(self) -> list[T]:
        """Encode the set as a YAML sequence."""
        return self.members()

    def unmarshal_yaml(self, items: list[T]) -> None:
        """Decode a YAML sequence into the set."""
        if isinstance(items, list):
            self.add(*items)


# ---------------------------------------------------------------------------
# typed aliases and constructors
# ---------------------------------------------------------------------------


def new(*items: T) -> Set[T]:
    return Set(*items)


def new_int(*items: int) -> Set[int]:
    return Set(*items)


def new_int32(*items: int) -> Set[int]:
    return Set(*items)


def new_int64(*items: int) -> Set[int]:
    return Set(*items)


def new_uint(*items: int) -> Set[int]:
    return Set(*items)


def new_uint32(*items: int) -> Set[int]:
    return Set(*items)


def new_uint64(*items: int) -> Set[int]:
    return Set(*items)


def new_string(*items: str) -> Set[str]:
    return Set(*items)
