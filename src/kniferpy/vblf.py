from __future__ import annotations

from kniferpy.internal import blfx
from kniferpy.internal.blfx import (
    DEFAULT_MACHINE_NUM,
    MACHINE_32,
    MACHINE_64,
    BitMapBloomFilter,
    BitSetBloomFilter,
    BloomFilter,
    FuncFilter,
    HashFunc,
)

__all__ = [
    "DEFAULT_MACHINE_NUM",
    "MACHINE_32",
    "MACHINE_64",
    "BitMapBloomFilter",
    "BitSetBloomFilter",
    "BloomFilter",
    "FuncFilter",
    "HashFunc",
    "new_bit_set_bloom_filter",
    "new_bitmap_bloom_filter",
    "new_bitmap_bloom_filter_with_filters",
    "new_default_filter",
    "new_elf_filter",
    "new_fnv_filter",
    "new_func_filter",
    "new_hf_filter",
    "new_hf_ip_filter",
    "new_js_filter",
    "new_pjw_filter",
    "new_rs_filter",
    "new_sdbm_filter",
    "new_tianl_filter",
]


def new_func_filter(
    max_value: int,
    hash_func: HashFunc | None = None,
    *,
    machine_num: int = DEFAULT_MACHINE_NUM,
) -> FuncFilter:
    return blfx.new_func_filter(max_value, hash_func, machine_num=machine_num)


def new_default_filter(max_value: int) -> FuncFilter:
    return blfx.new_default_filter(max_value)


def new_elf_filter(max_value: int) -> FuncFilter:
    return blfx.new_elf_filter(max_value)


def new_fnv_filter(max_value: int) -> FuncFilter:
    return blfx.new_fnv_filter(max_value)


def new_hf_filter(max_value: int) -> FuncFilter:
    return blfx.new_hf_filter(max_value)


def new_hf_ip_filter(max_value: int) -> FuncFilter:
    return blfx.new_hf_ip_filter(max_value)


def new_js_filter(max_value: int) -> FuncFilter:
    return blfx.new_js_filter(max_value)


def new_pjw_filter(max_value: int) -> FuncFilter:
    return blfx.new_pjw_filter(max_value)


def new_rs_filter(max_value: int) -> FuncFilter:
    return blfx.new_rs_filter(max_value)


def new_sdbm_filter(max_value: int) -> FuncFilter:
    return blfx.new_sdbm_filter(max_value)


def new_tianl_filter(max_value: int) -> FuncFilter:
    return blfx.new_tianl_filter(max_value)


def new_bit_set_bloom_filter(c: int, n: int, k: int) -> BitSetBloomFilter:
    return blfx.new_bit_set_bloom_filter(c, n, k)


def new_bitmap_bloom_filter(m: int) -> BitMapBloomFilter:
    return blfx.new_bitmap_bloom_filter(m)


def new_bitmap_bloom_filter_with_filters(m: int, *filters: BloomFilter) -> BitMapBloomFilter:
    return blfx.new_bitmap_bloom_filter_with_filters(m, *filters)
