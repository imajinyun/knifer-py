from __future__ import annotations

from kniferpy.internal import codecx

# ── Base32 Encoding ──────────────────────────────────────────────────────────

BASE32_STD_ENCODING = "std"
BASE32_HEX_ENCODING = "hex"

# ── Base58 Alphabet ──────────────────────────────────────────────────────────

BASE58_BITCOIN_ALPHABET = "bitcoin"
BASE58_FLICKR_ALPHABET = "flickr"

# ── Base64 ───────────────────────────────────────────────────────────────────


def base64_encode(data: bytes) -> str:
    return codecx.base64_encode(data)


def base64_encode_with_encoding(data: bytes, encoding: object | None = None) -> str:
    return codecx.base64_encode_with_encoding(data, encoding)


def base64_encode_str(value: str) -> str:
    return codecx.base64_encode_str(value)


def base64_decode(value: str) -> bytes:
    return codecx.base64_decode(value)


def base64_decode_with_encoding(value: str, encoding: object | None = None) -> bytes:
    return codecx.base64_decode_with_encoding(value, encoding)


def base64_decode_str(value: str) -> str:
    return codecx.base64_decode_str(value)


def base64_url_encode(data: bytes) -> str:
    return codecx.base64_url_encode(data)


def base64_url_decode(value: str) -> bytes:
    return codecx.base64_url_decode(value)


def base64_raw_url_encode(data: bytes) -> str:
    return codecx.base64_raw_url_encode(data)


def base64_raw_url_decode(value: str) -> bytes:
    return codecx.base64_raw_url_decode(value)


# ── Hex ──────────────────────────────────────────────────────────────────────


def hex_encode(data: bytes) -> str:
    return codecx.hex_encode(data)


def hex_encode_str(value: str) -> str:
    return codecx.hex_encode_str(value)


def hex_decode(value: str) -> bytes:
    return codecx.hex_decode(value)


def hex_decode_str(value: str) -> str:
    return codecx.hex_decode_str(value)


# ── Base32 ───────────────────────────────────────────────────────────────────


def base32_encode(data: bytes) -> str:
    return codecx.base32_encode(data)


def base32_encode_with_encoding(data: bytes, encoding: str) -> str:
    return codecx.base32_encode_with_encoding(data, encoding)


def base32_decode(value: str) -> bytes:
    return codecx.base32_decode(value)


def base32_decode_with_encoding(value: str, encoding: str) -> bytes:
    return codecx.base32_decode_with_encoding(value, encoding)


# ── Base58 ───────────────────────────────────────────────────────────────────


def base58_encode(data: bytes) -> str:
    return codecx.base58_encode(data)


def base58_encode_with_alphabet(data: bytes, alphabet: str) -> str:
    return codecx.base58_encode_with_alphabet(data, alphabet)


def base58_decode(value: str) -> bytes:
    return codecx.base58_decode(value)


def base58_decode_with_alphabet(value: str, alphabet: str) -> bytes:
    return codecx.base58_decode_with_alphabet(value, alphabet)


# ── Base62 ───────────────────────────────────────────────────────────────────


def base62_encode(data: bytes) -> str:
    return codecx.base62_encode(data)


def base62_decode(value: str) -> bytes:
    return codecx.base62_decode(value)


# ── Morse ────────────────────────────────────────────────────────────────────


def morse_encode(value: str) -> str:
    return codecx.morse_encode(value)


def morse_decode(value: str) -> str:
    return codecx.morse_decode(value)


# ── ROT ──────────────────────────────────────────────────────────────────────


def rot13(value: str) -> str:
    return codecx.rot13(value)


def rot47(value: str) -> str:
    return codecx.rot47(value)


def rotn(value: str, n: int) -> str:
    return codecx.rotn(value, n)