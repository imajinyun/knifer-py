from __future__ import annotations

from pathlib import Path

from kniferpy.internal import cryptox


# ── SHA digests ─────────────────────────────────────────────────────────────


def sha224(data: bytes) -> bytes:
    return cryptox.sha224(data)


def sha224_hex(data: bytes) -> str:
    return cryptox.sha224_hex(data)


def sha256(value: str | bytes) -> bytes:
    return cryptox.sha256(value)


def sha1_hex(value: str | bytes) -> str:
    return cryptox.sha1_hex(value)


def md5_checksum_hex(value: str | bytes) -> str:
    return cryptox.md5_checksum_hex(value)


def sha256_hex(value: str | bytes) -> str:
    return cryptox.sha256_hex(value)


def sha384_hex(data: bytes) -> str:
    return cryptox.sha384_hex(data)


def sha512_hex(value: str | bytes) -> str:
    return cryptox.sha512_hex(value)


def file_sha256_hex(path: str | Path, *, chunk_size: int = 1_048_576) -> str:
    return cryptox.file_sha256_hex(path, chunk_size=chunk_size)


# ── HMAC ────────────────────────────────────────────────────────────────────


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return cryptox.hmac_sha256_hex(key, value)


def hmac_sha384_hex(key: str | bytes, value: str | bytes) -> str:
    return cryptox.hmac_sha384_hex(key, value)


def hmac_sha512_hex(key: str | bytes, value: str | bytes) -> str:
    return cryptox.hmac_sha512_hex(key, value)


def verify_hmac_sha256_hex(key: str | bytes, value: str | bytes, expected_hex: str) -> bool:
    return cryptox.verify_hmac_sha256_hex(key, value, expected_hex)


def verify_sha256_hex(value: str | bytes, expected_hex: str) -> bool:
    return cryptox.verify_sha256_hex(value, expected_hex)


def verify_file_sha256_hex(path: str | Path, expected_hex: str) -> bool:
    return cryptox.verify_file_sha256_hex(path, expected_hex)


# ── PBKDF2 ──────────────────────────────────────────────────────────────────


def pbkdf2_sha256_hex(
    password: str | bytes,
    salt: str | bytes,
    *,
    iterations: int = 600_000,
    dklen: int = 32,
) -> str:
    return cryptox.pbkdf2_sha256_hex(password, salt, iterations=iterations, dklen=dklen)


# ── AES-GCM ─────────────────────────────────────────────────────────────────


def aes_encrypt_gcm(
    plaintext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    return cryptox.aes_encrypt_gcm(plaintext, key, nonce, associated_data)


def aes_decrypt_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    return cryptox.aes_decrypt_gcm(ciphertext, key, nonce, associated_data)


def aes_seal_gcm(
    plaintext: bytes,
    key: bytes,
    associated_data: bytes | None = None,
) -> tuple[bytes, bytes]:
    return cryptox.aes_seal_gcm(plaintext, key, associated_data)


def aes_open_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    return cryptox.aes_open_gcm(ciphertext, key, nonce, associated_data)


# ── secure random ───────────────────────────────────────────────────────────


def secure_bytes(length: int) -> bytes:
    return cryptox.secure_bytes(length)


def secure_token_urlsafe(length: int = 32) -> str:
    return cryptox.secure_token_urlsafe(length)


def secure_alnum(length: int = 32) -> str:
    return cryptox.secure_alnum(length)


# ── OTP ─────────────────────────────────────────────────────────────────────


def generate_otp_secret(size: int = 20) -> bytes:
    return cryptox.generate_otp_secret(size)


def otp_secret_base32(secret: bytes) -> str:
    return cryptox.otp_secret_base32(secret)


def parse_otp_secret_base32(secret: str) -> bytes:
    return cryptox.parse_otp_secret_base32(secret)


def hotp(secret: bytes, counter: int, *, digits: int = 6) -> str:
    return cryptox.hotp(secret, counter, digits=digits)


def hotp_verify(code: str, secret: bytes, counter: int, *, digits: int = 6) -> bool:
    return cryptox.hotp_verify(code, secret, counter, digits=digits)


def totp(secret: bytes, t: float, *, digits: int = 6, step: int = 30) -> str:
    return cryptox.totp(secret, t, digits=digits, step=step)


def totp_now(secret: bytes, *, digits: int = 6, step: int = 30) -> str:
    return cryptox.totp_now(secret, digits=digits, step=step)


def totp_verify(
    code: str,
    secret: bytes,
    t: float,
    *,
    digits: int = 6,
    step: int = 30,
    window: int = 1,
) -> bool:
    return cryptox.totp_verify(code, secret, t, digits=digits, step=step, window=window)


def totp_verify_now(
    code: str,
    secret: bytes,
    *,
    digits: int = 6,
    step: int = 30,
    window: int = 1,
) -> bool:
    return cryptox.totp_verify_now(code, secret, digits=digits, step=step, window=window)


def otp_auth_url(issuer: str, account: str, secret: bytes, *, digits: int = 6) -> str:
    return cryptox.otp_auth_url(issuer, account, secret, digits=digits)


# ── Argon2id password hashing ───────────────────────────────────────────────


def hash_password_argon2id(
    password: bytes,
    *,
    memory: int = 64 * 1024,
    iterations: int = 3,
    parallelism: int = 4,
    key_length: int = 32,
    salt_length: int = 16,
) -> str:
    return cryptox.hash_password_argon2id(
        password,
        memory=memory,
        iterations=iterations,
        parallelism=parallelism,
        key_length=key_length,
        salt_length=salt_length,
    )


def verify_password_argon2id(encoded: str, password: bytes) -> bool:
    return cryptox.verify_password_argon2id(encoded, password)