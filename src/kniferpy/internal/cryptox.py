from __future__ import annotations

import hashlib
import hmac
import secrets
import string
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type, verify_secret

from kniferpy.verr import CryptoError

# ── helpers ─────────────────────────────────────────────────────────────────


def to_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


# ── SHA-family digests ──────────────────────────────────────────────────────


def _digest(data: bytes, algorithm: str) -> bytes:
    return hashlib.new(algorithm, data).digest()


def _digest_hex(data: bytes, algorithm: str) -> str:
    return hashlib.new(algorithm, data).hexdigest()


def sha224(data: bytes) -> bytes:
    return _digest(data, "sha224")


def sha224_hex(data: bytes) -> str:
    return _digest_hex(data, "sha224")


def sha256(value: str | bytes) -> bytes:
    return hashlib.sha256(to_bytes(value)).digest()


def sha1_hex(value: str | bytes) -> str:
    return hashlib.sha1(to_bytes(value)).hexdigest()


def md5_checksum_hex(value: str | bytes) -> str:
    return hashlib.md5(to_bytes(value)).hexdigest()


def sha256_hex(value: str | bytes) -> str:
    return hashlib.sha256(to_bytes(value)).hexdigest()


def sha384_hex(data: bytes) -> str:
    return _digest_hex(data, "sha384")


def sha512_hex(value: str | bytes) -> str:
    return hashlib.sha512(to_bytes(value)).hexdigest()


def file_sha256_hex(path: str | Path, *, chunk_size: int = 1_048_576) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ── HMAC ────────────────────────────────────────────────────────────────────


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return hmac.new(to_bytes(key), to_bytes(value), hashlib.sha256).hexdigest()


def hmac_sha384_hex(key: str | bytes, value: str | bytes) -> str:
    return hmac.new(to_bytes(key), to_bytes(value), hashlib.sha384).hexdigest()


def hmac_sha512_hex(key: str | bytes, value: str | bytes) -> str:
    return hmac.new(to_bytes(key), to_bytes(value), hashlib.sha512).hexdigest()


def verify_hmac_sha256_hex(key: str | bytes, value: str | bytes, expected_hex: str) -> bool:
    actual = hmac_sha256_hex(key, value)
    return hmac.compare_digest(actual, expected_hex)


def verify_sha256_hex(value: str | bytes, expected_hex: str) -> bool:
    return hmac.compare_digest(sha256_hex(value), expected_hex)


def verify_file_sha256_hex(path: str | Path, expected_hex: str) -> bool:
    return hmac.compare_digest(file_sha256_hex(path), expected_hex)


# ── PBKDF2 ──────────────────────────────────────────────────────────────────


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


# ── AES-GCM ─────────────────────────────────────────────────────────────────

_AES_KEY_SIZES = {16, 24, 32}


def _validate_aes_key(key: bytes) -> None:
    if len(key) not in _AES_KEY_SIZES:
        raise CryptoError(
            f"AES key must be 16, 24, or 32 bytes, got {len(key)}",
            code="crypto.invalid_aes_key",
        )


def _validate_aes_nonce(nonce: bytes) -> None:
    if len(nonce) < 12:
        raise CryptoError(
            f"AES-GCM nonce must be at least 12 bytes, got {len(nonce)}",
            code="crypto.invalid_nonce",
        )


def aes_encrypt_gcm(
    plaintext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    _validate_aes_key(key)
    _validate_aes_nonce(nonce)
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(nonce, plaintext, associated_data)


def aes_decrypt_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    _validate_aes_key(key)
    _validate_aes_nonce(nonce)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except Exception as exc:
        raise CryptoError(
            "AES-GCM decryption failed",
            code="crypto.decrypt_failed",
            context={"detail": str(exc)},
        ) from exc


def aes_seal_gcm(
    plaintext: bytes,
    key: bytes,
    associated_data: bytes | None = None,
) -> tuple[bytes, bytes]:
    _validate_aes_key(key)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext


def aes_open_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    return aes_decrypt_gcm(ciphertext, key, nonce, associated_data)


# ── secure random ───────────────────────────────────────────────────────────


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


# ── OTP (HOTP / TOTP) ───────────────────────────────────────────────────────


def _hotp(secret: bytes, counter: int, digits: int = 6) -> str:
    counter_bytes = struct.pack(">Q", counter)
    h = hmac.new(secret, counter_bytes, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    binary = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10**digits)).zfill(digits)


def generate_otp_secret(size: int = 20) -> bytes:
    if size <= 0:
        raise ValueError("size must be positive")
    return secrets.token_bytes(size)


def otp_secret_base32(secret: bytes) -> str:
    import base64

    return base64.b32encode(secret).decode("ascii").rstrip("=")


def parse_otp_secret_base32(secret: str) -> bytes:
    import base64

    padding = 8 - (len(secret) % 8)
    if padding != 8:
        secret += "=" * padding
    return base64.b32decode(secret.upper())


def hotp(secret: bytes, counter: int, *, digits: int = 6) -> str:
    if digits < 6 or digits > 8:
        raise CryptoError("OTP digits must be 6, 7, or 8", code="crypto.invalid_otp")
    return _hotp(secret, counter, digits=digits)


def hotp_verify(code: str, secret: bytes, counter: int, *, digits: int = 6) -> bool:
    return hmac.compare_digest(code, hotp(secret, counter, digits=digits))


def totp(secret: bytes, t: float, *, digits: int = 6, step: int = 30) -> str:
    counter = int(t) // step
    return hotp(secret, counter, digits=digits)


def totp_now(secret: bytes, *, digits: int = 6, step: int = 30) -> str:
    import time

    return totp(secret, time.time(), digits=digits, step=step)


def totp_verify(
    code: str,
    secret: bytes,
    t: float,
    *,
    digits: int = 6,
    step: int = 30,
    window: int = 1,
) -> bool:
    for offset in range(-window, window + 1):
        counter = int(t) // step + offset
        if hmac.compare_digest(code, hotp(secret, counter, digits=digits)):
            return True
    return False


def totp_verify_now(
    code: str,
    secret: bytes,
    *,
    digits: int = 6,
    step: int = 30,
    window: int = 1,
) -> bool:
    import time

    return totp_verify(code, secret, time.time(), digits=digits, step=step, window=window)


def otp_auth_url(issuer: str, account: str, secret: bytes, *, digits: int = 6) -> str:
    b32 = otp_secret_base32(secret)
    from urllib.parse import quote

    encoded_issuer = quote(issuer)
    encoded_account = quote(account)
    return (
        f"otpauth://totp/{encoded_issuer}:{encoded_account}"
        f"?secret={b32}&issuer={encoded_issuer}&algorithm=SHA1&digits={digits}&period=30"
    )


# ── Argon2id password hashing ───────────────────────────────────────────────

_DEFAULT_ARGON2_MEMORY = 64 * 1024  # 64 MiB
_DEFAULT_ARGON2_ITERATIONS = 3
_DEFAULT_ARGON2_PARALLELISM = 4
_DEFAULT_ARGON2_KEY_LENGTH = 32
_DEFAULT_ARGON2_SALT_LENGTH = 16


def hash_password_argon2id(
    password: bytes,
    *,
    memory: int = _DEFAULT_ARGON2_MEMORY,
    iterations: int = _DEFAULT_ARGON2_ITERATIONS,
    parallelism: int = _DEFAULT_ARGON2_PARALLELISM,
    key_length: int = _DEFAULT_ARGON2_KEY_LENGTH,
    salt_length: int = _DEFAULT_ARGON2_SALT_LENGTH,
) -> str:
    import base64

    salt = secrets.token_bytes(salt_length)
    raw = hash_secret_raw(
        password,
        salt,
        time_cost=iterations,
        memory_cost=memory,
        parallelism=parallelism,
        hash_len=key_length,
        type=Type.ID,
    )
    return (
        f"$argon2id$v=19$m={memory},t={iterations},p={parallelism}"
        f"${base64.b64encode(salt).decode('ascii').rstrip('=')}"
        f"${base64.b64encode(raw).decode('ascii').rstrip('=')}"
    )


def verify_password_argon2id(encoded: str, password: bytes) -> bool:
    try:
        return verify_secret(encoded, password, Type.ID)
    except Exception:
        return False