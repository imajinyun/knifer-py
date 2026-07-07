from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import string
import struct
import time as _time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

try:
    from argon2.low_level import Type, hash_secret_raw, verify_secret
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as exc:  # pragma: no cover - exercised with import hooks
    from kniferpy.internal.optionalx import require_extra

    raise require_extra(exc.name or "cryptography", "crypto", exc) from exc

from kniferpy.verr import CryptoError, ValidationError

# ── Error sentinels (Go compat) ──────────────────────────────────────────────

ErrInvalidKey = CryptoError
ErrInvalidIV = CryptoError
ErrInvalidCipherText = CryptoError
ErrInvalidSM2Signature = CryptoError
ErrInvalidOTP = CryptoError
ErrInvalidPasswordHash = CryptoError
ErrInvalidJWK = CryptoError

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


def sha384(data: bytes) -> bytes:
    return _digest(data, "sha384")


def sha512(data: bytes) -> bytes:
    return _digest(data, "sha512")


def sha256_hex_bytes(data: bytes) -> str:
    return _digest_hex(data, "sha256")


def sha512_hex_bytes(data: bytes) -> str:
    return _digest_hex(data, "sha512")


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
        return verify_secret(encoded.encode("utf-8"), password, Type.ID)
    except Exception:
        return False


# ── Generic digest / HMAC ────────────────────────────────────────────────────


def digest(data: bytes, algorithm: str) -> bytes:
    return _digest(data, algorithm)


def digest_hex(data: bytes, algorithm: str) -> str:
    return _digest_hex(data, algorithm)


def hmac_hex(algorithm: str, key: bytes, data: bytes) -> str:
    return hmac.new(key, data, algorithm).hexdigest()


def hmac_bytes(algorithm: str, key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, algorithm).digest()


def hmac_equal(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


def constant_time_equal(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


# ── RSA key generation ───────────────────────────────────────────────────────


def gen_rsa_key(bits: int = 2048) -> rsa.RSAPrivateKey:
    if bits < 2048:
        raise CryptoError("RSA key size must be at least 2048 bits", code="crypto.invalid_key_size")
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


# ── RSA OAEP encrypt/decrypt ─────────────────────────────────────────────────


def rsa_encrypt_oaep(
    plain: bytes,
    pub: rsa.RSAPublicKey,
    label: bytes = b"",
    *,
    hash_algorithm: hashes.HashAlgorithm | None = None,
) -> bytes:
    algo = hash_algorithm or hashes.SHA256()
    return pub.encrypt(
        plain,
        padding.OAEP(mgf=padding.MGF1(algorithm=algo), algorithm=algo, label=label),
    )


def rsa_decrypt_oaep(
    cipher_text: bytes,
    priv: rsa.RSAPrivateKey,
    label: bytes = b"",
    *,
    hash_algorithm: hashes.HashAlgorithm | None = None,
) -> bytes:
    algo = hash_algorithm or hashes.SHA256()
    return priv.decrypt(
        cipher_text,
        padding.OAEP(mgf=padding.MGF1(algorithm=algo), algorithm=algo, label=label),
    )


# ── RSA PSS sign/verify ──────────────────────────────────────────────────────


def rsa_sign_pss(
    priv: rsa.RSAPrivateKey,
    digest: bytes,
    *,
    hash_algorithm: hashes.HashAlgorithm | None = None,
) -> bytes:
    algo = hash_algorithm or hashes.SHA256()
    return priv.sign(
        digest,
        padding.PSS(mgf=padding.MGF1(algo), salt_length=padding.PSS.MAX_LENGTH),
        algo,
    )


def rsa_verify_pss(
    pub: rsa.RSAPublicKey,
    digest: bytes,
    sig: bytes,
    *,
    hash_algorithm: hashes.HashAlgorithm | None = None,
) -> bool:
    algo = hash_algorithm or hashes.SHA256()
    try:
        pub.verify(
            sig,
            digest,
            padding.PSS(mgf=padding.MGF1(algo), salt_length=padding.PSS.MAX_LENGTH),
            algo,
        )
        return True
    except Exception:
        return False


# ── RSA sign/verify with data (digest internally) ─────────────────────────────


def sign_sha256_with_rsa(data: bytes, priv: rsa.RSAPrivateKey) -> bytes:
    digest = hashlib.sha256(data).digest()
    return rsa_sign_pss(priv, digest, hash_algorithm=hashes.SHA256())


def verify_sha256_with_rsa(data: bytes, sig: bytes, pub: rsa.RSAPublicKey) -> bool:
    digest = hashlib.sha256(data).digest()
    return rsa_verify_pss(pub, digest, sig, hash_algorithm=hashes.SHA256())


# ── PEM serialization ────────────────────────────────────────────────────────


def private_key_to_pem(priv: rsa.RSAPrivateKey) -> bytes:
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


def public_key_to_pem(pub: rsa.RSAPublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def parse_rsa_private_key_pem(data: bytes) -> rsa.RSAPrivateKey:
    key = serialization.load_pem_private_key(data, password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise CryptoError("PEM data is not an RSA private key", code="crypto.invalid_pem")
    return key


def parse_rsa_public_key_pem(data: bytes) -> rsa.RSAPublicKey:
    key = serialization.load_pem_public_key(data)
    if not isinstance(key, rsa.RSAPublicKey):
        raise CryptoError("PEM data is not an RSA public key", code="crypto.invalid_pem")
    return key


def private_key_to_pkcs8_pem(priv: rsa.RSAPrivateKey) -> bytes:
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def public_key_to_pkcs1_pem(pub: rsa.RSAPublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1,
    )


# ── JWK ──────────────────────────────────────────────────────────────────────


def rsa_public_key_to_jwk(pub: rsa.RSAPublicKey, kid: str = "") -> dict[str, Any]:
    nums = pub.public_numbers()
    jwk: dict[str, Any] = {
        "kty": "RSA",
        "n": _b64url_encode(nums.n.to_bytes((nums.n.bit_length() + 7) // 8, "big")),
        "e": _b64url_encode(nums.e.to_bytes((nums.e.bit_length() + 7) // 8, "big")),
    }
    if kid:
        jwk["kid"] = kid
    return jwk


def rsa_private_key_to_jwk(priv: rsa.RSAPrivateKey, kid: str = "") -> dict[str, Any]:
    priv_nums = priv.private_numbers()
    pub_nums = priv_nums.public_numbers
    jwk: dict[str, Any] = {
        "kty": "RSA",
        "n": _b64url_encode(pub_nums.n.to_bytes((pub_nums.n.bit_length() + 7) // 8, "big")),
        "e": _b64url_encode(pub_nums.e.to_bytes((pub_nums.e.bit_length() + 7) // 8, "big")),
        "d": _b64url_encode(priv_nums.d.to_bytes((priv_nums.d.bit_length() + 7) // 8, "big")),
        "p": _b64url_encode(priv_nums.p.to_bytes((priv_nums.p.bit_length() + 7) // 8, "big")),
        "q": _b64url_encode(priv_nums.q.to_bytes((priv_nums.q.bit_length() + 7) // 8, "big")),
        "dp": _b64url_encode(
            priv_nums.dmp1.to_bytes((priv_nums.dmp1.bit_length() + 7) // 8, "big")
        ),
        "dq": _b64url_encode(
            priv_nums.dmq1.to_bytes((priv_nums.dmq1.bit_length() + 7) // 8, "big")
        ),
        "qi": _b64url_encode(
            priv_nums.iqmp.to_bytes((priv_nums.iqmp.bit_length() + 7) // 8, "big")
        ),
    }
    if kid:
        jwk["kid"] = kid
    return jwk


def jwk_to_rsa_public_key(jwk: dict[str, Any]) -> rsa.RSAPublicKey:
    n = int.from_bytes(_b64url_decode(str(jwk["n"])), "big")
    e = int.from_bytes(_b64url_decode(str(jwk["e"])), "big")
    return rsa.RSAPublicNumbers(e, n).public_key()


def jwk_to_rsa_private_key(jwk: dict[str, Any]) -> rsa.RSAPrivateKey:
    n = int.from_bytes(_b64url_decode(str(jwk["n"])), "big")
    e = int.from_bytes(_b64url_decode(str(jwk["e"])), "big")
    d = int.from_bytes(_b64url_decode(str(jwk["d"])), "big")
    p = int.from_bytes(_b64url_decode(str(jwk["p"])), "big")
    q = int.from_bytes(_b64url_decode(str(jwk["q"])), "big")
    dmp1 = int.from_bytes(_b64url_decode(str(jwk["dp"])), "big")
    dmq1 = int.from_bytes(_b64url_decode(str(jwk["dq"])), "big")
    iqmp = int.from_bytes(_b64url_decode(str(jwk["qi"])), "big")
    pub_nums = rsa.RSAPublicNumbers(e, n)
    return rsa.RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, pub_nums).private_key()


def marshal_jwk(jwk: dict[str, Any]) -> bytes:
    return json.dumps(jwk, separators=(",", ":")).encode("utf-8")


def parse_jwk(data: bytes) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(data.decode("utf-8")))


def marshal_jwks(keys: list[dict[str, Any]]) -> bytes:
    return json.dumps({"keys": keys}, separators=(",", ":")).encode("utf-8")


def parse_jwks(data: bytes) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(data.decode("utf-8")))


def select_jwk_by_key_id(jwks: dict[str, Any], kid: str) -> dict[str, Any]:
    for key in cast(list[dict[str, Any]], jwks.get("keys", [])):
        if key.get("kid") == kid:
            return key
    raise CryptoError(f"JWK with kid={kid!r} not found", code="crypto.jwk_not_found")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


# ── Sign params ──────────────────────────────────────────────────────────────


def sign_params(
    params: dict[str, Any],
    digest_hex_fn: Callable[[bytes], str],
    separator: str = "&",
    key_value_separator: str = "=",
    ignore_nil: bool = False,
    *other_params: str,
) -> str:
    keys = sorted(params.keys())
    parts: list[str] = []
    for key in keys:
        val = params[key]
        if ignore_nil and val is None:
            continue
        parts.append(f"{key}{key_value_separator}{val}")
    if other_params:
        parts.extend(other_params)
    raw = separator.join(parts)
    return digest_hex_fn(raw.encode("utf-8"))


def sign_params_sha256(params: dict[str, Any], *other_params: str) -> str:
    return sign_params(
        params,
        lambda data: hashlib.sha256(data).hexdigest(),
        "&",
        "=",
        False,
        *other_params,
    )


# ── Additional random helpers ────────────────────────────────────────────────


def gen_aes_key(size: int = 32) -> bytes:
    if size not in (16, 24, 32):
        raise CryptoError("AES key must be 16, 24, or 32 bytes", code="crypto.invalid_key_size")
    return secrets.token_bytes(size)


# ── Validation ───────────────────────────────────────────────────────────────


def validate_aes_key(key: bytes) -> None:
    _validate_aes_key(key)


def validate_aes_iv(iv: bytes) -> None:
    if len(iv) != 16:
        raise CryptoError(
            f"AES IV must be 16 bytes, got {len(iv)}",
            code="crypto.invalid_iv",
        )


def validate_aes_gcm_nonce(nonce: bytes) -> None:
    _validate_aes_nonce(nonce)


def validate_sm4_key(key: bytes) -> None:
    if len(key) != 16:
        raise CryptoError(
            f"SM4 key must be 16 bytes, got {len(key)}",
            code="crypto.invalid_key",
        )


def validate_sm4_iv(iv: bytes) -> None:
    if len(iv) != 16:
        raise CryptoError(
            f"SM4 IV must be 16 bytes, got {len(iv)}",
            code="crypto.invalid_iv",
        )


# ── Generic PBKDF2 (any hash) ────────────────────────────────────────────────


def pbkdf2(
    password: str | bytes,
    salt: str | bytes,
    *,
    iterations: int = 600_000,
    key_len: int = 32,
    hash_name: str = "sha256",
) -> bytes:
    """Generic PBKDF2 key derivation with any hash algorithm."""
    if iterations < 100_000:
        raise ValidationError("iterations must be at least 100000", code="crypto.pbkdf2_iterations")
    return hashlib.pbkdf2_hmac(
        hash_name,
        to_bytes(password),
        to_bytes(salt),
        iterations,
        dklen=key_len,
    )


def pbkdf2_sha256(
    password: str | bytes,
    salt: str | bytes,
    *,
    iterations: int = 600_000,
    key_len: int = 32,
) -> bytes:
    """PBKDF2-SHA256 returning raw bytes (Go compat)."""
    return pbkdf2(password, salt, iterations=iterations, key_len=key_len, hash_name="sha256")


# ── Password hash introspection ──────────────────────────────────────────────


class PasswordHashInfo:
    """Introspection for Argon2id password hash strings."""

    __slots__ = (
        "algorithm",
        "version",
        "memory",
        "iterations",
        "parallelism",
        "salt_length",
        "key_length",
    )

    def __init__(
        self,
        algorithm: str = "",
        version: int = 0,
        memory: int = 0,
        iterations: int = 0,
        parallelism: int = 0,
        salt_length: int = 0,
        key_length: int = 0,
    ) -> None:
        self.algorithm = algorithm
        self.version = version
        self.memory = memory
        self.iterations = iterations
        self.parallelism = parallelism
        self.salt_length = salt_length
        self.key_length = key_length


def parse_password_hash(encoded: str) -> PasswordHashInfo:
    """Parse an Argon2id encoded hash string for introspection."""
    if not encoded.startswith("$argon2id$"):
        return PasswordHashInfo()
    parts = encoded.split("$")
    # $argon2id$v=19$m=65536,t=3,p=4$salt$hash
    info = PasswordHashInfo(algorithm="argon2id")
    for part in parts:
        if part.startswith("v="):
            info.version = int(part[2:])
        elif "," in part and "=" in part:
            for kv in part.split(","):
                k, _, v = kv.partition("=")
                if k == "m":
                    info.memory = int(v)
                elif k == "t":
                    info.iterations = int(v)
                elif k == "p":
                    info.parallelism = int(v)
    if len(parts) >= 5:
        info.salt_length = len(base64.b64decode(parts[4] + "=="))
    if len(parts) >= 6:
        info.key_length = len(base64.b64decode(parts[5] + "=="))
    return info


# ── X.509 certificate parsing ────────────────────────────────────────────────


def parse_x509_certificate_pem(data: bytes) -> Any:
    """Parse a PEM-encoded X.509 certificate."""
    from cryptography import x509

    return x509.load_pem_x509_certificate(data)


def public_key_from_certificate_pem(data: bytes) -> Any:
    """Extract the public key from a PEM-encoded X.509 certificate."""
    cert = parse_x509_certificate_pem(data)
    return cert.public_key()


# ── OTP clock injection ──────────────────────────────────────────────────────

_otp_clock: Callable[[], float] | None = None


def set_otp_clock(clock: Callable[[], float] | None) -> None:
    """Set a custom clock for OTP (for deterministic testing)."""
    global _otp_clock
    _otp_clock = clock


def _otp_now() -> float:
    return _otp_clock() if _otp_clock is not None else _time.time()


def totp_now_with_options(
    secret: str | bytes,
    *,
    digits: int = 6,
    step: int = 30,
) -> str:
    """Generate TOTP using the injectable clock."""
    now = int(_otp_now())
    return totp(to_bytes(secret), now, digits=digits, step=step)


def totp_verify_now_with_options(
    secret: str | bytes,
    code: str,
    *,
    digits: int = 6,
    step: int = 30,
    window: int = 1,
) -> bool:
    """Verify TOTP using the injectable clock."""
    now = int(_otp_now())
    return totp_verify(code, to_bytes(secret), now, digits=digits, step=step, window=window)


# ── Random with options (Go compat) ──────────────────────────────────────────


def secure_bytes_with_options(
    length: int, *, reader: Callable[[int], bytes] | None = None
) -> bytes:
    """Generate secure random bytes with optional custom reader."""
    if reader is not None:
        return reader(length)
    return secrets.token_bytes(length)


def gen_aes_key_with_options(
    size: int = 32, *, reader: Callable[[int], bytes] | None = None
) -> bytes:
    """Generate an AES key with optional custom reader."""
    if size not in (16, 24, 32):
        raise CryptoError("AES key must be 16, 24, or 32 bytes", code="crypto.invalid_key_size")
    if reader is not None:
        return reader(size)
    return secrets.token_bytes(size)


# ── Go-compat random_bytes ───────────────────────────────────────────────────


def random_bytes(length: int) -> bytes:
    """Generate n cryptographically secure random bytes (Go compat)."""
    return secrets.token_bytes(length)


def random_bytes_with_options(
    length: int, *, reader: Callable[[int], bytes] | None = None
) -> bytes:
    """Generate n random bytes with optional custom reader (Go compat)."""
    if reader is not None:
        return reader(length)
    return secrets.token_bytes(length)


# ── SM3 (Chinese national cryptography standard) ─────────────────────────────


def sm3(data: bytes) -> bytes:
    """Return the SM3 digest bytes of data."""
    from gmssl.sm3 import sm3_hash  # type: ignore[import-untyped]

    return bytes.fromhex(sm3_hash(list(data)))


def sm3_hex(data: bytes) -> str:
    """Return the SM3 digest in lower-case hex form."""
    from gmssl.sm3 import sm3_hash

    return cast(str, sm3_hash(list(data)))


def sm3_new() -> Any:
    """Return a new SM3 hash object (Go compat)."""
    from gmssl.sm3 import sm3_hash

    return sm3_hash


def sm3_equal(a: bytes, b: bytes) -> bool:
    """Compare two SM3 digest values in constant time."""
    return hmac.compare_digest(a, b)


def hmac_sm3_bytes(key: bytes, data: bytes) -> bytes:
    """Return HMAC-SM3 digest bytes."""

    from gmssl.sm3 import sm3_hash

    # Use a simple HMAC-SM3 implementation
    block_size = 64
    if len(key) > block_size:
        key = bytes.fromhex(sm3_hash(list(key)))
    if len(key) < block_size:
        key = key + b"\x00" * (block_size - len(key))
    o_key_pad = bytes(k ^ 0x5C for k in key)
    i_key_pad = bytes(k ^ 0x36 for k in key)
    inner = bytes.fromhex(sm3_hash(list(i_key_pad + data)))
    return bytes.fromhex(sm3_hash(list(o_key_pad + inner)))


def hmac_sm3_hex(key: bytes, data: bytes) -> str:
    """Return HMAC-SM3 in lower-case hex form."""
    return hmac_sm3_bytes(key, data).hex()


# ── SM4 (Chinese national cryptography standard) ─────────────────────────────


def _sm4_pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - len(data) % block_size
    return data + bytes([pad_len] * pad_len)


def _sm4_pkcs7_unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16:
        raise CryptoError("invalid PKCS#7 padding", code="crypto.invalid_padding")
    return data[:-pad_len]


def gen_sm4_key() -> bytes:
    """Return a random 16-byte SM4 key."""
    return secrets.token_bytes(16)


def gen_sm4_key_with_options(*, reader: Callable[[int], bytes] | None = None) -> bytes:
    """Return a random SM4 key with optional custom reader."""
    if reader is not None:
        return reader(16)
    return secrets.token_bytes(16)


def sm4_encrypt_ecb(plain: bytes, key: bytes) -> bytes:
    """Encrypt plain data using SM4-ECB with PKCS#7 padding."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import ECB

    cipher = Cipher(SM4(key), ECB())
    encryptor = cipher.encryptor()
    padded = _sm4_pkcs7_pad(plain)
    return encryptor.update(padded) + encryptor.finalize()


def sm4_decrypt_ecb(cipher_text: bytes, key: bytes) -> bytes:
    """Decrypt SM4-ECB data with PKCS#7 padding."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import ECB

    cipher = Cipher(SM4(key), ECB())
    decryptor = cipher.decryptor()
    padded = decryptor.update(cipher_text) + decryptor.finalize()
    return _sm4_pkcs7_unpad(padded)


def sm4_encrypt_cbc(plain: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt plain data using SM4-CBC with PKCS#7 padding."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import CBC

    validate_sm4_key(key)
    validate_sm4_iv(iv)
    cipher = Cipher(SM4(key), CBC(iv))
    encryptor = cipher.encryptor()
    padded = _sm4_pkcs7_pad(plain)
    return encryptor.update(padded) + encryptor.finalize()


def sm4_decrypt_cbc(cipher_text: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt SM4-CBC data with PKCS#7 padding."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import CBC

    validate_sm4_key(key)
    validate_sm4_iv(iv)
    cipher = Cipher(SM4(key), CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(cipher_text) + decryptor.finalize()
    return _sm4_pkcs7_unpad(padded)


def sm4_encrypt_gcm(plain: bytes, key: bytes, nonce: bytes, additional_data: bytes) -> bytes:
    """Encrypt plain data using SM4-GCM."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import GCM

    validate_sm4_key(key)
    validate_aes_gcm_nonce(nonce)
    cipher = Cipher(SM4(key), GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(additional_data)
    cipher_text = encryptor.update(plain) + encryptor.finalize()
    return cipher_text + encryptor.tag


def sm4_decrypt_gcm(cipher_text: bytes, key: bytes, nonce: bytes, additional_data: bytes) -> bytes:
    """Decrypt SM4-GCM data."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import GCM

    validate_sm4_key(key)
    validate_aes_gcm_nonce(nonce)
    tag = cipher_text[-16:]
    cipher_data = cipher_text[:-16]
    cipher = Cipher(SM4(key), GCM(nonce, tag))
    decryptor = cipher.decryptor()
    decryptor.authenticate_additional_data(additional_data)
    return decryptor.update(cipher_data) + decryptor.finalize()


def sm4_seal_gcm(plain: bytes, key: bytes, additional_data: bytes) -> tuple[bytes, bytes]:
    """Encrypt plain data using SM4-GCM and a freshly generated nonce."""
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import SM4
    from cryptography.hazmat.primitives.ciphers.modes import GCM

    validate_sm4_key(key)
    nonce = secrets.token_bytes(12)
    cipher = Cipher(SM4(key), GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(additional_data)
    cipher_text = encryptor.update(plain) + encryptor.finalize()
    return nonce, cipher_text + encryptor.tag


# ── SM2 (Chinese national cryptography standard) ─────────────────────────────


def gen_sm2_key() -> tuple[Any, Any]:
    """Generate an SM2 private/public key pair."""
    from gmssl.sm2 import CryptSM2  # type: ignore[import-untyped]

    sm2_crypt = CryptSM2(private_key=None, public_key=None)
    sm2_crypt.generate_key()
    return sm2_crypt._private_key, sm2_crypt._public_key


def sm2_encrypt(plain: bytes, pub_key: str) -> bytes:
    """Encrypt plain data using SM2 public key encryption."""
    from gmssl.sm2 import CryptSM2

    sm2_crypt = CryptSM2(private_key=None, public_key=pub_key)
    return cast(bytes, sm2_crypt.encrypt(plain))


def sm2_decrypt(cipher_text: bytes, priv_key: str) -> bytes:
    """Decrypt SM2 ciphertext."""
    from gmssl.sm2 import CryptSM2

    sm2_crypt = CryptSM2(private_key=priv_key, public_key=None)
    return cast(bytes, sm2_crypt.decrypt(cipher_text))


def sm2_sign(data: bytes, priv_key: str) -> bytes:
    """Sign data using SM2 with the default user ID."""
    from gmssl.sm2 import CryptSM2

    sm2_crypt = CryptSM2(private_key=priv_key, public_key=None)
    return cast(bytes, sm2_crypt.sign_with_sm3(data))


def sm2_verify(data: bytes, sig: bytes, pub_key: str) -> bool:
    """Verify an SM2 signature using the default user ID."""
    from gmssl.sm2 import CryptSM2

    sm2_crypt = CryptSM2(private_key=None, public_key=pub_key)
    return cast(bool, sm2_crypt.verify_with_sm3(sig, data))


def sm2_private_key_to_pem(priv_key: Any) -> bytes:
    """Encode an SM2 private key as PKCS#8 PEM."""
    from gmssl.func import sm2_private_key_to_pem as _to_pem  # type: ignore[import-untyped]

    return cast(str, _to_pem(priv_key)).encode()


def sm2_public_key_to_pem(pub_key: Any) -> bytes:
    """Encode an SM2 public key as PKIX PEM."""
    from gmssl.func import sm2_public_key_to_pem as _to_pem

    return cast(str, _to_pem(pub_key)).encode()


def parse_sm2_private_key_pem(data: bytes) -> Any:
    """Parse a PKCS#8 SM2 private key PEM."""
    from gmssl.func import pem_to_sm2_private_key

    return pem_to_sm2_private_key(data.decode())


def parse_sm2_public_key_pem(data: bytes) -> Any:
    """Parse a PKIX SM2 public key PEM."""
    from gmssl.func import pem_to_sm2_public_key

    return pem_to_sm2_public_key(data.decode())


# ── Go-compat sign/verify with RSA options ───────────────────────────────────


def sign_with_rsa_options(
    data: bytes, priv: rsa.RSAPrivateKey, *, hash_alg: str = "sha256", pss: bool = False
) -> bytes:
    """Hash data and sign it with configurable RSA options (Go compat)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, utils

    hash_map = {
        "sha256": hashes.SHA256(),
        "sha384": hashes.SHA384(),
        "sha512": hashes.SHA512(),
    }
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    pad: Any
    if pss:
        pad = padding.PSS(mgf=padding.MGF1(chosen_hash), salt_length=padding.PSS.MAX_LENGTH)
    else:
        pad = padding.PKCS1v15()

    return priv.sign(data, pad, utils.Prehashed(chosen_hash))


def verify_with_rsa_options(
    data: bytes, sig: bytes, pub: rsa.RSAPublicKey, *, hash_alg: str = "sha256", pss: bool = False
) -> bool:
    """Hash data and verify an RSA signature with configurable options (Go compat)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, utils

    hash_map = {
        "sha256": hashes.SHA256(),
        "sha384": hashes.SHA384(),
        "sha512": hashes.SHA512(),
    }
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    pad: Any
    if pss:
        pad = padding.PSS(mgf=padding.MGF1(chosen_hash), salt_length=padding.PSS.MAX_LENGTH)
    else:
        pad = padding.PKCS1v15()

    try:
        pub.verify(sig, data, pad, utils.Prehashed(chosen_hash))
        return True
    except Exception:
        return False
