from __future__ import annotations

from pathlib import Path

from kniferpy.internal import cryptox


def sha256(value: str | bytes) -> bytes:
    return cryptox.sha256(value)


def sha1_hex(value: str | bytes) -> str:
    return cryptox.sha1_hex(value)


def md5_checksum_hex(value: str | bytes) -> str:
    return cryptox.md5_checksum_hex(value)


def sha256_hex(value: str | bytes) -> str:
    return cryptox.sha256_hex(value)


def file_sha256_hex(path: str | Path, *, chunk_size: int = 1_048_576) -> str:
    return cryptox.file_sha256_hex(path, chunk_size=chunk_size)


def sha512_hex(value: str | bytes) -> str:
    return cryptox.sha512_hex(value)


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return cryptox.hmac_sha256_hex(key, value)


def verify_hmac_sha256_hex(key: str | bytes, value: str | bytes, expected_hex: str) -> bool:
    return cryptox.verify_hmac_sha256_hex(key, value, expected_hex)


def verify_sha256_hex(value: str | bytes, expected_hex: str) -> bool:
    return cryptox.verify_sha256_hex(value, expected_hex)


def verify_file_sha256_hex(path: str | Path, expected_hex: str) -> bool:
    return cryptox.verify_file_sha256_hex(path, expected_hex)


def pbkdf2_sha256_hex(
    password: str | bytes,
    salt: str | bytes,
    *,
    iterations: int = 600_000,
    dklen: int = 32,
) -> str:
    return cryptox.pbkdf2_sha256_hex(password, salt, iterations=iterations, dklen=dklen)
