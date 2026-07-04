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
    IntMap,
    LongMap,
)
from kniferpy.internal.hashx import (
    ap_hash,
    bkdr_hash,
    djb_hash,
    elf_hash,
    fnv_hash_string,
    hf_hash,
    hf_ip_hash,
    java_default_hash,
    js_hash,
    pjw_hash,
    rs_hash,
    sdbm_hash,
    tianl_hash,
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
    "IntMap",
    "LongMap",
    "ap_hash",
    "bkdr_hash",
    "djb_hash",
    "elf_hash",
    "fnv_hash_string",
    "hf_hash",
    "hf_ip_hash",
    "init_from_file_with_options",
    "init_from_reader",
    "java_default_hash",
    "js_hash",
    "new_bit_set_bloom_filter",
    "new_bit_set_bloom_filter_e",
    "new_bitmap_bloom_filter",
    "new_bitmap_bloom_filter_e",
    "new_bitmap_bloom_filter_with_filters",
    "new_bitmap_bloom_filter_with_filters_e",
    "new_default_filter",
    "new_default_bloom_filter",
    "new_elf_filter",
    "new_fnv_filter",
    "new_func_filter",
    "new_func_filter_e",
    "new_func_filter_with_machine_num",
    "new_func_filter_with_machine_num_e",
    "new_hf_filter",
    "new_hf_ip_filter",
    "new_int_map",
    "new_js_filter",
    "new_long_map",
    "new_pjw_filter",
    "new_rs_filter",
    "new_sdbm_filter",
    "new_tianl_filter",
    "pjw_hash",
    "rs_hash",
    "sdbm_hash",
    "tianl_hash",
    # Bloom-prefixed hash aliases (Go compat)
    "BloomRSHash",
    "BloomJSHash",
    "BloomPJWHash",
    "BloomELFHash",
    "BloomBKDRHash",
    "BloomSDBMHash",
    "BloomDJBHash",
    "BloomFNVHash",
]


def new_func_filter(
    max_value: int,
    hash_func: HashFunc | None = None,
    *,
    machine_num: int = DEFAULT_MACHINE_NUM,
) -> FuncFilter:
    return blfx.new_func_filter(max_value, hash_func, machine_num=machine_num)


def new_func_filter_e(
    max_value: int,
    hash_func: HashFunc | None = None,
    *,
    machine_num: int = DEFAULT_MACHINE_NUM,
) -> tuple[FuncFilter, None]:
    return blfx.new_func_filter_e(max_value, hash_func, machine_num=machine_num)


def new_func_filter_with_machine_num(
    max_value: int,
    machine_num: int,
    hash_func: HashFunc | None = None,
) -> FuncFilter:
    return blfx.new_func_filter_with_machine_num(max_value, machine_num, hash_func)


def new_func_filter_with_machine_num_e(
    max_value: int,
    machine_num: int,
    hash_func: HashFunc | None = None,
) -> tuple[FuncFilter, None]:
    return blfx.new_func_filter_with_machine_num_e(max_value, machine_num, hash_func)


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


def new_bit_set_bloom_filter_e(c: int, n: int, k: int) -> tuple[BitSetBloomFilter, None]:
    return blfx.new_bit_set_bloom_filter_e(c, n, k)


def new_bitmap_bloom_filter(m: int) -> BitMapBloomFilter:
    return blfx.new_bitmap_bloom_filter(m)


def new_bitmap_bloom_filter_e(m: int) -> tuple[BitMapBloomFilter, None]:
    return blfx.new_bitmap_bloom_filter_e(m)


def new_bitmap_bloom_filter_with_filters(m: int, *filters: BloomFilter) -> BitMapBloomFilter:
    return blfx.new_bitmap_bloom_filter_with_filters(m, *filters)


def new_bitmap_bloom_filter_with_filters_e(m: int, *filters: BloomFilter) -> tuple[BitMapBloomFilter, None]:
    return blfx.new_bitmap_bloom_filter_with_filters_e(m, *filters)


def new_int_map(size: int) -> IntMap:
    return blfx.new_int_map(size)


def new_long_map(size: int) -> LongMap:
    return blfx.new_long_map(size)


def init_from_file_with_options(bloom: BitSetBloomFilter, path: str, opts: list | None = None) -> None:
    blfx.init_from_file_with_options(bloom, path, opts)


def init_from_reader(bloom: BitSetBloomFilter, reader: list[str]) -> None:
    blfx.init_from_reader(bloom, reader)


def new_default_bloom_filter(max_value: int) -> FuncFilter:
    return blfx.new_default_filter(max_value)


# ── Bloom-prefixed hash aliases (Go compat) ────────────────────────────────────

BloomRSHash = rs_hash
BloomJSHash = js_hash
BloomPJWHash = pjw_hash
BloomELFHash = elf_hash
BloomBKDRHash = bkdr_hash
BloomSDBMHash = sdbm_hash
BloomDJBHash = djb_hash
BloomFNVHash = fnv_hash_string