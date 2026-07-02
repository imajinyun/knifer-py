from __future__ import annotations

_MASK32 = 0xFFFFFFFF
_MASK64 = 0xFFFFFFFFFFFFFFFF


def _i32(x: int) -> int:
    """Wrap x to a signed 32-bit integer (Java/Go int semantics)."""
    x &= _MASK32
    return x - 0x100000000 if x >= 0x80000000 else x


def _i64(x: int) -> int:
    """Wrap x to a signed 64-bit integer."""
    x &= _MASK64
    return x - 0x10000000000000000 if x >= 0x8000000000000000 else x


def _chars(s: str) -> list[int]:
    return [ord(ch) for ch in s]


def additive_hash(s: str, prime: int) -> int:
    """Additive hash modulo prime. Non-positive prime falls back to 31."""
    if prime <= 0:
        prime = 31
    h = len(s.encode("utf-8"))
    for c in _chars(s):
        h += c
    return h % prime


def fnv_hash(s: str) -> int:
    """32-bit FNV-1 hash over the UTF-8 bytes of s (matches hash/fnv New32)."""
    h = 2166136261
    for b in s.encode("utf-8"):
        h = (h * 16777619) & _MASK32
        h ^= b
    return h & _MASK32


def rs_hash(s: str) -> int:
    """RS hash algorithm."""
    b = 378551
    a = 63689
    h = 0
    for c in _chars(s):
        h = _i32(h * a + c)
        a = _i32(a * b)
    return h & 0x7FFFFFFF


def js_hash(s: str) -> int:
    """JS hash algorithm."""
    h = 1315423911
    for c in _chars(s):
        h = _i32(h ^ ((h << 5) + c + (h >> 2)))
    if h < 0:
        h = _i32(-h)
    return h & 0x7FFFFFFF


def pjw_hash(s: str) -> int:
    """PJW hash algorithm."""
    bits_in_unsigned_int = 32
    three_quarters = (bits_in_unsigned_int * 3) // 4
    one_eighth = bits_in_unsigned_int // 8
    high_bits = _i32(_MASK32 << (bits_in_unsigned_int - one_eighth))
    h = 0
    for c in _chars(s):
        h = _i32((h << one_eighth) + c)
        test = _i32(h & high_bits)
        if test != 0:
            h = _i32((h ^ (test >> three_quarters)) & (~high_bits))
    return h & 0x7FFFFFFF


def elf_hash(s: str) -> int:
    """ELF hash algorithm."""
    h = 0
    mask = _i32(0xF0000000)
    for c in _chars(s):
        h = _i32((h << 4) + c)
        x = _i32(h & mask)
        if x != 0:
            h = _i32(h ^ (x >> 24))
            h = _i32(h & ~x)
    return h & 0x7FFFFFFF


def bkdr_hash(s: str) -> int:
    """BKDR hash algorithm."""
    seed = 131
    h = 0
    for c in _chars(s):
        h = _i32(h * seed + c)
    return h & 0x7FFFFFFF


def sdbm_hash(s: str) -> int:
    """SDBM hash algorithm."""
    h = 0
    for c in _chars(s):
        h = _i32(c + (h << 6) + (h << 16) - h)
    return h & 0x7FFFFFFF


def djb_hash(s: str) -> int:
    """DJB hash algorithm."""
    h = 5381
    for c in _chars(s):
        h = _i32(((h << 5) + h) + c)
    return h & 0x7FFFFFFF


def ap_hash(s: str) -> int:
    """AP hash algorithm."""
    h = 0
    for i, c in enumerate(_chars(s)):
        even = ((h << 7) ^ c ^ (h >> 3)) if i & 1 == 0 else ~((h << 11) ^ c ^ (h >> 5))
        h = _i32(h ^ even)
    return h


def fnv_hash_string(s: str) -> int:
    """Improved 32-bit FNV-1 hash for strings (differs from fnv_hash)."""
    p = 16777619
    h = _i32(2166136261)
    for c in _chars(s):
        h = _i32((h ^ c) * p)
    h = _i32(h + (h << 13))
    h = _i32(h ^ ((h & _MASK32) >> 7))
    h = _i32(h + (h << 3))
    h = _i32(h ^ ((h & _MASK32) >> 17))
    h = _i32(h + (h << 5))
    if h < 0:
        h = _i32(-h)
    return h


def hf_hash(s: str) -> int:
    """HF hash algorithm."""
    h = 0
    for i, c in enumerate(_chars(s)):
        h = _i64(h + c * 3 * i)
    if h < 0:
        h = _i64(-h)
    return h


def hf_ip_hash(s: str) -> int:
    """HFIP hash algorithm."""
    chars = _chars(s)
    length = len(chars)
    h = 0
    for i in range(length):
        h = _i64(h + (chars[i % 4] ^ chars[i]))
    return h


def tianl_hash(s: str) -> int:
    """TianL hash algorithm."""
    chars = _chars(s)
    length = len(chars)
    if length == 0:
        return 0
    h = 16777216 * (length - 1) if length <= 256 else 4278190080

    def process(index: int, ch: int, acc: int) -> int:
        c = ch
        if ord("A") <= c <= ord("Z"):
            c += 32
        term = (3 * index * c * c + 5 * index * c + 7 * index + 11 * c) % 16777216
        return _i64(acc + term)

    if length <= 96:
        for i in range(1, length + 1):
            h = process(i, chars[i - 1], h)
    else:
        for i in range(1, 97):
            h = process(i, chars[i + length - 96 - 1], h)
    if h < 0:
        h = _i64(-h)
    return h


def java_default_hash(s: str) -> int:
    """Simulate Java String.hashCode."""
    h = 0
    for c in _chars(s):
        h = _i32(31 * h + c)
    return h
