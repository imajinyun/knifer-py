from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from pathlib import Path


def to_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def sha256(value: str | bytes) -> bytes:
    return hashlib.sha256(to_bytes(value)).digest()


def sha1_hex(value: str | bytes) -> str:
    return hashlib.sha1(to_bytes(value)).hexdigest()


def md5_checksum_hex(value: str | bytes) -> str:
    return hashlib.md5(to_bytes(value)).hexdigest()


def sha256_hex(value: str | bytes) -> str:
    return hashlib.sha256(to_bytes(value)).hexdigest()


def file_sha256_hex(path: str | Path, *, chunk_size: int = 1_048_576) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha512_hex(value: str | bytes) -> str:
    return hashlib.sha512(to_bytes(value)).hexdigest()


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return hmac.new(to_bytes(key), to_bytes(value), hashlib.sha256).hexdigest()


def verify_hmac_sha256_hex(key: str | bytes, value: str | bytes, expected_hex: str) -> bool:
    actual = hmac_sha256_hex(key, value)
    return hmac.compare_digest(actual, expected_hex)


def verify_sha256_hex(value: str | bytes, expected_hex: str) -> bool:
    return hmac.compare_digest(sha256_hex(value), expected_hex)


def verify_file_sha256_hex(path: str | Path, expected_hex: str) -> bool:
    return hmac.compare_digest(file_sha256_hex(path), expected_hex)


def pbkdf2_sha256_hex(
    password: str | bytes,
    salt: str | bytes,
    *,
    iterations: int = 600_000,
    dklen: int = 32,
) -> str:
    if iterations < 100_000:
        raise ValueError("iterations must be at least 100000")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        to_bytes(password),
        to_bytes(salt),
        iterations,
        dklen=dklen,
    )
    return digest.hex()


def secure_bytes(length: int) -> bytes:
    if length <= 0:
        raise ValueError("length must be positive")
    return secrets.token_bytes(length)


def secure_token_urlsafe(length: int = 32) -> str:
    if length <= 0:
        raise ValueError("length must be positive")
    return secrets.token_urlsafe(length)


def secure_alnum(length: int = 32) -> str:
    if length <= 0:
        raise ValueError("length must be positive")
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
