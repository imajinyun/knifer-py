from __future__ import annotations

from kniferpy.internal import hashx

__all__ = [
    "additive_hash",
    "fnv_hash",
    "fnv_hash_string",
    "rs_hash",
    "js_hash",
    "pjw_hash",
    "elf_hash",
    "bkdr_hash",
    "sdbm_hash",
    "djb_hash",
    "ap_hash",
    "hf_hash",
    "hf_ip_hash",
    "tianl_hash",
    "java_default_hash",
]


def additive_hash(s: str, prime: int) -> int:
    return hashx.additive_hash(s, prime)


def fnv_hash(s: str) -> int:
    return hashx.fnv_hash(s)


def fnv_hash_string(s: str) -> int:
    return hashx.fnv_hash_string(s)


def rs_hash(s: str) -> int:
    return hashx.rs_hash(s)


def js_hash(s: str) -> int:
    return hashx.js_hash(s)


def pjw_hash(s: str) -> int:
    return hashx.pjw_hash(s)


def elf_hash(s: str) -> int:
    return hashx.elf_hash(s)


def bkdr_hash(s: str) -> int:
    return hashx.bkdr_hash(s)


def sdbm_hash(s: str) -> int:
    return hashx.sdbm_hash(s)


def djb_hash(s: str) -> int:
    return hashx.djb_hash(s)


def ap_hash(s: str) -> int:
    return hashx.ap_hash(s)


def hf_hash(s: str) -> int:
    return hashx.hf_hash(s)


def hf_ip_hash(s: str) -> int:
    return hashx.hf_ip_hash(s)


def tianl_hash(s: str) -> int:
    return hashx.tianl_hash(s)


def java_default_hash(s: str) -> int:
    return hashx.java_default_hash(s)
