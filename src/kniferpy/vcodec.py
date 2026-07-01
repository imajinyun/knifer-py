from __future__ import annotations

import base64
import binascii
import codecs


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def base64_encode_str(value: str, *, encoding: str = "utf-8") -> str:
    return base64_encode(value.encode(encoding))


def base64_decode(value: str) -> bytes:
    return base64.b64decode(value, validate=True)


def base64_decode_str(value: str, *, encoding: str = "utf-8") -> str:
    return base64_decode(value).decode(encoding)


def base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def base64_url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value)


def hex_encode(data: bytes) -> str:
    return binascii.hexlify(data).decode("ascii")


def hex_encode_str(value: str, *, encoding: str = "utf-8") -> str:
    return hex_encode(value.encode(encoding))


def hex_decode(value: str) -> bytes:
    return binascii.unhexlify(value)


def hex_decode_str(value: str, *, encoding: str = "utf-8") -> str:
    return hex_decode(value).decode(encoding)


def rot13(value: str) -> str:
    return codecs.encode(value, "rot_13")
