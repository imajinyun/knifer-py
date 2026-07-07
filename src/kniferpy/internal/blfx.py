from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, Protocol

from kniferpy.internal import hashx
from kniferpy.verr import ValidationError

# Machine word size constants (mirror knifer-go internal/bloomfilter).
MACHINE_32 = 32
MACHINE_64 = 64
DEFAULT_MACHINE_NUM = MACHINE_32

_MAX_VALUE_LIMIT = 0x7FFFFFFF

HashFunc = Callable[[str], int]


class BloomFilter(Protocol):
    """Structural type for Bloom filters exposing ``add`` and ``contains``."""

    def add(self, value: str) -> bool: ...

    def contains(self, value: str) -> bool: ...


class _BitMap:
    """Word-array bitmap mirroring knifer-go IntMap/LongMap semantics."""

    __slots__ = ("_machine", "_words")

    def __init__(self, capacity: int, machine: int) -> None:
        self._words = [0] * capacity
        self._machine = machine

    def add(self, i: int) -> None:
        self._words[i // self._machine] |= 1 << (i & (self._machine - 1))

    def contains(self, i: int) -> bool:
        return (self._words[i // self._machine] >> (i & (self._machine - 1))) & 1 == 1

    def remove(self, i: int) -> None:
        self._words[i // self._machine] &= ~(1 << (i & (self._machine - 1)))


class FuncFilter:
    """Bloom filter backed by a single custom hash function."""

    __slots__ = ("_bm", "_hash_func", "_size")

    def __init__(
        self,
        max_value: int,
        hash_func: HashFunc | None = None,
        *,
        machine_num: int = DEFAULT_MACHINE_NUM,
    ) -> None:
        if max_value < 1 or max_value > _MAX_VALUE_LIMIT:
            raise ValidationError(
                f"vblf: max value must be between 1 and {_MAX_VALUE_LIMIT}",
                code="blf.invalid_max_value",
            )
        if machine_num not in (MACHINE_32, MACHINE_64):
            raise ValidationError(
                f"vblf: machine number must be {MACHINE_32} or {MACHINE_64}",
                code="blf.invalid_machine_num",
            )
        capacity = (max_value + machine_num - 1) // machine_num
        self._bm = _BitMap(capacity, machine_num)
        self._size = max_value
        self._hash_func = hash_func if hash_func is not None else hashx.java_default_hash

    def _hash(self, value: str) -> int:
        # Go computes abs(hash % size); abs(h) % size is identical for size > 0.
        return abs(self._hash_func(value)) % self._size

    def contains(self, value: str) -> bool:
        return self._bm.contains(self._hash(value))

    def add(self, value: str) -> bool:
        h = self._hash(value)
        if self._bm.contains(h):
            return False
        self._bm.add(h)
        return True


# ----- Convenience filters based on specific hash algorithms ----------------


def new_func_filter(
    max_value: int,
    hash_func: HashFunc | None = None,
    *,
    machine_num: int = DEFAULT_MACHINE_NUM,
) -> FuncFilter:
    return FuncFilter(max_value, hash_func, machine_num=machine_num)


def new_default_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.java_default_hash)


def new_elf_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.elf_hash)


def new_fnv_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.fnv_hash_string)


def new_hf_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.hf_hash)


def new_hf_ip_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.hf_ip_hash)


def new_js_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.js_hash)


def new_pjw_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.pjw_hash)


def new_rs_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.rs_hash)


def new_sdbm_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.sdbm_hash)


def new_tianl_filter(max_value: int) -> FuncFilter:
    return FuncFilter(max_value, hashx.tianl_hash)


# ----- BitSet based Bloom filter --------------------------------------------

_BITSET_HASHES: tuple[HashFunc, ...] = (
    hashx.rs_hash,
    hashx.js_hash,
    hashx.elf_hash,
    hashx.bkdr_hash,
    hashx.ap_hash,
    hashx.djb_hash,
    hashx.sdbm_hash,
    hashx.pjw_hash,
)


class BitSetBloomFilter:
    """Fixed-size bitset Bloom filter using a fixed order of hash algorithms."""

    __slots__ = ("_added_elements", "_bit_set_size", "_bits", "_hash_function_number")

    def __init__(self, c: int, n: int, k: int) -> None:
        if c <= 0:
            raise ValidationError("vblf: parameter c must be positive", code="blf.invalid_capacity")
        if n <= 0:
            raise ValidationError("vblf: parameter n must be positive", code="blf.invalid_expected")
        if k < 1 or k > 8:
            raise ValidationError(
                "vblf: hash function number must be between 1 and 8",
                code="blf.invalid_hash_number",
            )
        size = c * k
        self._bits = bytearray((size + 7) // 8)
        self._bit_set_size = size
        self._added_elements = n
        self._hash_function_number = k

    def _set_bit(self, pos: int) -> None:
        self._bits[pos >> 3] |= 1 << (pos & 7)

    def _get_bit(self, pos: int) -> bool:
        return (self._bits[pos >> 3] >> (pos & 7)) & 1 == 1

    def _positions(self, value: str) -> list[int]:
        size = self._bit_set_size
        return [abs(_BITSET_HASHES[i](value)) % size for i in range(self._hash_function_number)]

    def add(self, value: str) -> bool:
        if self.contains(value):
            return False
        for pos in self._positions(value):
            self._set_bit(pos)
        return True

    def contains(self, value: str) -> bool:
        return all(self._get_bit(pos) for pos in self._positions(value))

    def false_positive_probability(self) -> float:
        k = self._hash_function_number
        return math.pow(
            1 - math.exp(-float(k) * float(self._added_elements) / float(self._bit_set_size)),
            float(k),
        )

    def init_from_lines(self, lines: Iterable[str]) -> None:
        for line in lines:
            self.add(line.rstrip("\r\n"))

    def init_from_file(self, path: str | Path, *, encoding: str = "utf-8") -> None:
        with Path(path).open(encoding=encoding) as handle:
            self.init_from_lines(handle)


# ----- BitMap based composite Bloom filter ----------------------------------


class BitMapBloomFilter:
    """Composite Bloom filter aggregating several filters (five by default)."""

    __slots__ = ("_filters",)

    def __init__(self, m: int, filters: Iterable[BloomFilter] | None = None) -> None:
        provided = list(filters) if filters is not None else []
        if m < 5 and not provided:
            raise ValidationError(
                "vblf: bitmap size m must be at least 5 when using default filters",
                code="blf.invalid_bitmap_size",
            )
        self._filters = provided if provided else _default_bitmap_filters(m)

    def add(self, value: str) -> bool:
        changed = False
        for f in self._filters:
            if f.add(value):
                changed = True
        return changed

    def contains(self, value: str) -> bool:
        return all(f.contains(value) for f in self._filters)


def _default_bitmap_filters(m: int) -> list[BloomFilter]:
    size = (m // 5) * 1024 * 1024 * 8
    return [
        new_default_filter(size),
        new_elf_filter(size),
        new_js_filter(size),
        new_pjw_filter(size),
        new_sdbm_filter(size),
    ]


def new_bit_set_bloom_filter(c: int, n: int, k: int) -> BitSetBloomFilter:
    return BitSetBloomFilter(c, n, k)


def new_bitmap_bloom_filter(m: int) -> BitMapBloomFilter:
    return BitMapBloomFilter(m)


def new_bitmap_bloom_filter_with_filters(m: int, *filters: BloomFilter) -> BitMapBloomFilter:
    return BitMapBloomFilter(m, filters)


# --- Error-returning variants (E-style, always succeed for Python) -------------


def new_bit_set_bloom_filter_e(c: int, n: int, k: int) -> tuple[BitSetBloomFilter, None]:
    return BitSetBloomFilter(c, n, k), None


def new_bitmap_bloom_filter_e(m: int) -> tuple[BitMapBloomFilter, None]:
    return BitMapBloomFilter(m), None


def new_bitmap_bloom_filter_with_filters_e(
    m: int, *filters: BloomFilter
) -> tuple[BitMapBloomFilter, None]:
    return BitMapBloomFilter(m, filters), None


def new_func_filter_e(
    max_value: int,
    hash_func: HashFunc | None = None,
    *,
    machine_num: int = DEFAULT_MACHINE_NUM,
) -> tuple[FuncFilter, None]:
    return FuncFilter(max_value, hash_func, machine_num=machine_num), None


def new_func_filter_with_machine_num(
    max_value: int,
    machine_num: int,
    hash_func: HashFunc | None = None,
) -> FuncFilter:
    return FuncFilter(max_value, hash_func, machine_num=machine_num)


def new_func_filter_with_machine_num_e(
    max_value: int,
    machine_num: int,
    hash_func: HashFunc | None = None,
) -> tuple[FuncFilter, None]:
    return FuncFilter(max_value, hash_func, machine_num=machine_num), None


# --- IntMap / LongMap ----------------------------------------------------------


class IntMap:
    __slots__ = ("_ints",)

    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValidationError("vblf: IntMap size must be positive", code="blf.invalid_size")
        self._ints = [0] * size

    def add(self, i: int) -> None:
        idx = i % len(self._ints)
        self._ints[idx] |= 1 << (i & 31)

    def contains(self, i: int) -> bool:
        idx = i % len(self._ints)
        return (self._ints[idx] >> (i & 31)) & 1 == 1

    def remove(self, i: int) -> None:
        idx = i % len(self._ints)
        self._ints[idx] &= ~(1 << (i & 31))


class LongMap:
    __slots__ = ("_longs",)

    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValidationError("vblf: LongMap size must be positive", code="blf.invalid_size")
        self._longs = [0] * size

    def add(self, i: int) -> None:
        idx = i % len(self._longs)
        self._longs[idx] |= 1 << (i & 63)

    def contains(self, i: int) -> bool:
        idx = i % len(self._longs)
        return (self._longs[idx] >> (i & 63)) & 1 == 1

    def remove(self, i: int) -> None:
        idx = i % len(self._longs)
        self._longs[idx] &= ~(1 << (i & 63))


def new_int_map(size: int) -> IntMap:
    return IntMap(size)


def new_long_map(size: int) -> LongMap:
    return LongMap(size)


# --- File-based init -----------------------------------------------------------

_FileOption = Callable[["_BloomFileConfig"], None]


class _BloomFileConfig:
    __slots__ = ("open_file",)

    def __init__(self) -> None:
        self.open_file: Callable[[str], Any] | None = None


def _default_open_file(path: str) -> Any:
    return open(path, encoding="utf-8")  # noqa: SIM115


def with_open_file(open_file: Callable[[str], Any]) -> _FileOption:
    def _apply(cfg: _BloomFileConfig) -> None:
        if open_file is not None:
            cfg.open_file = open_file

    return _apply


def _apply_file_options(opts: Sequence[_FileOption]) -> _BloomFileConfig:
    cfg = _BloomFileConfig()
    for opt in opts or []:
        if opt is not None:
            opt(cfg)
    return cfg


def init_from_file_with_options(
    bloom: BitSetBloomFilter,
    path: str,
    opts: Sequence[_FileOption] | None = None,
) -> None:
    cfg = _apply_file_options(opts or [])
    opener = cfg.open_file or _default_open_file
    with opener(path) as f:
        bloom.init_from_lines(f)


def init_from_reader(
    bloom: BitSetBloomFilter,
    reader: Iterable[str],
) -> None:
    bloom.init_from_lines(reader)
