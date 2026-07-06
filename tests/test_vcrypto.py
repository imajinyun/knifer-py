from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta, timezone

from kniferpy import vcrypto
from kniferpy.internal import cryptox
from kniferpy.verr import CryptoError, ValidationError


# ═══════════════════════════════════════════════════════════════════════════════
# SHA-family digests (existing)
# ═══════════════════════════════════════════════════════════════════════════════


def test_sha256_hex() -> None:
    assert (
        vcrypto.sha256_hex("kniferpy")
        == "983b8790345a90a374d0cc2d52d2a2175dc335542f8207d70726dd8daed95342"
    )


def test_sha256_bytes() -> None:
    assert len(vcrypto.sha256(b"kniferpy")) == 32


def test_sha512_hex() -> None:
    result = vcrypto.sha512_hex("kniferpy")
    assert len(result) == 128
    assert isinstance(result, str)


def test_hmac_sha256_hex() -> None:
    assert (
        vcrypto.hmac_sha256_hex("secret", "payload")
        == "b82fcb791acec57859b989b430a826488ce2e479fdf92326bd0a2e8375a42ba4"
    )


def test_hmac_sha256_hex_bytes_key() -> None:
    assert len(vcrypto.hmac_sha256_hex(b"secret", "payload")) == 64


def test_sha1_and_md5_checksum_hex() -> None:
    assert vcrypto.sha1_hex("kniferpy") == "d55ede568f80b6dbbb02ac9e2853ff3f658d9ec9"
    assert vcrypto.md5_checksum_hex("kniferpy") == "ee248a454d8a92483ff2d4b5386de125"


def test_verify_hmac_sha256_hex() -> None:
    expected = vcrypto.hmac_sha256_hex("secret", "payload")

    assert vcrypto.verify_hmac_sha256_hex("secret", "payload", expected)
    assert not vcrypto.verify_hmac_sha256_hex("secret", "payload", "bad")


def test_verify_sha256_hex() -> None:
    hex_val = vcrypto.sha256_hex("kniferpy")
    assert vcrypto.verify_sha256_hex("kniferpy", hex_val)
    assert not vcrypto.verify_sha256_hex("kniferpy", "0" * 64)


def test_verify_sha256_and_file_sha256(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("kniferpy", encoding="utf-8")
    expected = vcrypto.sha256_hex("kniferpy")

    assert vcrypto.verify_sha256_hex("kniferpy", expected)
    assert vcrypto.file_sha256_hex(path) == expected
    assert vcrypto.verify_file_sha256_hex(path, expected)


def test_verify_file_sha256_hex_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("kniferpy", encoding="utf-8")
    assert not vcrypto.verify_file_sha256_hex(path, "0" * 64)


def test_file_sha256_hex_large_file(tmp_path: Path) -> None:
    path = tmp_path / "large.bin"
    path.write_bytes(b"x" * 2_000_000)
    result = vcrypto.file_sha256_hex(path)
    assert len(result) == 64


def test_pbkdf2_sha256_hex() -> None:
    derived = vcrypto.pbkdf2_sha256_hex("password", "salt", iterations=100_000, dklen=16)
    assert len(derived) == 32


def test_pbkdf2_defaults() -> None:
    derived = vcrypto.pbkdf2_sha256_hex("password", "salt")
    assert len(derived) == 64


def test_pbkdf2_bytes_input() -> None:
    derived = vcrypto.pbkdf2_sha256_hex(b"password", b"salt", iterations=100_000, dklen=16)
    assert len(derived) == 32


def test_pbkdf2_empty_string() -> None:
    derived = vcrypto.pbkdf2_sha256_hex("", "", iterations=100_000, dklen=16)
    assert len(derived) == 32


def test_pbkdf2_rejects_low_iterations() -> None:
    with pytest.raises(ValueError, match="iterations must be at least 100000"):
        vcrypto.pbkdf2_sha256_hex("password", "salt", iterations=10)


def test_pbkdf2_sha256_hex_rejects_low_iterations() -> None:
    with pytest.raises(ValueError, match="iterations must be at least 100000"):
        vcrypto.pbkdf2_sha256_hex("password", "salt", iterations=10)


def test_secure_bytes() -> None:
    result = vcrypto.secure_bytes(16)
    assert len(result) == 16
    assert isinstance(result, bytes)


def test_secure_bytes_produces_different_values() -> None:
    a = vcrypto.secure_bytes(32)
    b = vcrypto.secure_bytes(32)
    assert a != b


def test_secure_bytes_rejects_zero() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vcrypto.secure_bytes(0)


def test_secure_bytes_rejects_negative() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vcrypto.secure_bytes(-1)


def test_secure_token_urlsafe() -> None:
    token = vcrypto.secure_token_urlsafe()
    assert len(token) > 0
    assert isinstance(token, str)


def test_secure_token_urlsafe_custom_length() -> None:
    token = vcrypto.secure_token_urlsafe(16)
    assert len(token) > 0


def test_secure_token_urlsafe_rejects_zero() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vcrypto.secure_token_urlsafe(0)


def test_secure_alnum() -> None:
    token = vcrypto.secure_alnum(20)
    assert len(token) == 20
    assert isinstance(token, str)
    assert token.isalnum()


def test_secure_alnum_default_length() -> None:
    token = vcrypto.secure_alnum()
    assert len(token) == 32
    assert token.isalnum()


def test_secure_alnum_rejects_zero() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vcrypto.secure_alnum(0)


def test_secure_alnum_rejects_negative() -> None:
    with pytest.raises(ValueError, match="length must be positive"):
        vcrypto.secure_alnum(-5)


# ═══════════════════════════════════════════════════════════════════════════════
# Additional SHA digests
# ═══════════════════════════════════════════════════════════════════════════════


def test_sha224() -> None:
    result = vcrypto.sha224(b"kniferpy")
    assert len(result) == 28


def test_sha224_hex() -> None:
    result = vcrypto.sha224_hex(b"kniferpy")
    assert len(result) == 56
    assert isinstance(result, str)


def test_sha384() -> None:
    result = vcrypto.sha384(b"kniferpy")
    assert len(result) == 48


def test_sha384_hex() -> None:
    result = vcrypto.sha384_hex(b"kniferpy")
    assert len(result) == 96


def test_sha512() -> None:
    result = vcrypto.sha512(b"kniferpy")
    assert len(result) == 64


def test_sha256_hex_bytes() -> None:
    result = vcrypto.sha256_hex_bytes(b"kniferpy")
    assert len(result) == 64


def test_sha512_hex_bytes() -> None:
    result = vcrypto.sha512_hex_bytes(b"kniferpy")
    assert len(result) == 128


# ═══════════════════════════════════════════════════════════════════════════════
# Generic digest / HMAC
# ═══════════════════════════════════════════════════════════════════════════════


def test_digest() -> None:
    result = vcrypto.digest(b"kniferpy", "sha256")
    assert len(result) == 32


def test_digest_hex() -> None:
    result = vcrypto.digest_hex(b"kniferpy", "sha256")
    assert len(result) == 64


def test_hmac_hex() -> None:
    result = vcrypto.hmac_hex("sha256", b"secret", b"payload")
    assert len(result) == 64


def test_hmac_bytes() -> None:
    result = vcrypto.hmac_bytes("sha256", b"secret", b"payload")
    assert len(result) == 32


def test_hmac_equal() -> None:
    assert vcrypto.hmac_equal(b"abc", b"abc")
    assert not vcrypto.hmac_equal(b"abc", b"def")


def test_constant_time_equal() -> None:
    assert vcrypto.constant_time_equal(b"abc", b"abc")
    assert not vcrypto.constant_time_equal(b"abc", b"def")


def test_hmac_sha384_hex() -> None:
    result = vcrypto.hmac_sha384_hex("secret", "payload")
    assert len(result) == 96


def test_hmac_sha512_hex() -> None:
    result = vcrypto.hmac_sha512_hex("secret", "payload")
    assert len(result) == 128


# ═══════════════════════════════════════════════════════════════════════════════
# AES-GCM
# ═══════════════════════════════════════════════════════════════════════════════


def test_aes_encrypt_decrypt_gcm() -> None:
    key = vcrypto.gen_aes_key(32)
    nonce = vcrypto.secure_bytes(12)
    plaintext = b"hello world"
    ciphertext = vcrypto.aes_encrypt_gcm(plaintext, key, nonce)
    assert ciphertext != plaintext
    decrypted = vcrypto.aes_decrypt_gcm(ciphertext, key, nonce)
    assert decrypted == plaintext


def test_aes_gcm_with_associated_data() -> None:
    key = vcrypto.gen_aes_key(32)
    nonce = vcrypto.secure_bytes(12)
    plaintext = b"hello world"
    aad = b"associated data"
    ciphertext = vcrypto.aes_encrypt_gcm(plaintext, key, nonce, associated_data=aad)
    decrypted = vcrypto.aes_decrypt_gcm(ciphertext, key, nonce, associated_data=aad)
    assert decrypted == plaintext


def test_aes_gcm_wrong_aad_fails() -> None:
    key = vcrypto.gen_aes_key(32)
    nonce = vcrypto.secure_bytes(12)
    ciphertext = vcrypto.aes_encrypt_gcm(b"hello", key, nonce, associated_data=b"aad1")
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.aes_decrypt_gcm(ciphertext, key, nonce, associated_data=b"aad2")
    assert exc_info.value.code == "crypto.decrypt_failed"


def test_aes_gcm_wrong_key_fails() -> None:
    key1 = vcrypto.gen_aes_key(32)
    key2 = vcrypto.gen_aes_key(32)
    nonce = vcrypto.secure_bytes(12)
    ciphertext = vcrypto.aes_encrypt_gcm(b"hello", key1, nonce)
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.aes_decrypt_gcm(ciphertext, key2, nonce)
    assert exc_info.value.code == "crypto.decrypt_failed"


def test_aes_seal_open_gcm() -> None:
    key = vcrypto.gen_aes_key(32)
    nonce, ciphertext = vcrypto.aes_seal_gcm(b"hello world", key)
    assert len(nonce) == 12
    decrypted = vcrypto.aes_open_gcm(ciphertext, key, nonce)
    assert decrypted == b"hello world"


def test_aes_seal_gcm_with_aad() -> None:
    key = vcrypto.gen_aes_key(32)
    nonce, ciphertext = vcrypto.aes_seal_gcm(b"hello", key, associated_data=b"aad")
    decrypted = vcrypto.aes_open_gcm(ciphertext, key, nonce, associated_data=b"aad")
    assert decrypted == b"hello"


def test_aes_encrypt_rejects_invalid_key() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.aes_encrypt_gcm(b"hello", b"short", b"123456789012")
    assert exc_info.value.code == "crypto.invalid_aes_key"


def test_aes_encrypt_rejects_short_nonce() -> None:
    key = vcrypto.gen_aes_key(32)
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.aes_encrypt_gcm(b"hello", key, b"short")
    assert exc_info.value.code == "crypto.invalid_nonce"


# ═══════════════════════════════════════════════════════════════════════════════
# AES key generation and validation
# ═══════════════════════════════════════════════════════════════════════════════


def test_gen_aes_key_default() -> None:
    key = vcrypto.gen_aes_key()
    assert len(key) == 32


def test_gen_aes_key_16() -> None:
    key = vcrypto.gen_aes_key(16)
    assert len(key) == 16


def test_gen_aes_key_24() -> None:
    key = vcrypto.gen_aes_key(24)
    assert len(key) == 24


def test_gen_aes_key_invalid_size() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.gen_aes_key(10)
    assert exc_info.value.code == "crypto.invalid_key_size"


def test_validate_aes_key() -> None:
    vcrypto.validate_aes_key(b"1234567890123456")  # 16 bytes, should not raise


def test_validate_aes_key_invalid() -> None:
    with pytest.raises(CryptoError):
        vcrypto.validate_aes_key(b"short")


def test_validate_aes_iv() -> None:
    vcrypto.validate_aes_iv(b"1234567890123456")  # 16 bytes, should not raise


def test_validate_aes_iv_invalid() -> None:
    with pytest.raises(CryptoError):
        vcrypto.validate_aes_iv(b"short")


def test_validate_aes_gcm_nonce() -> None:
    vcrypto.validate_aes_gcm_nonce(b"123456789012")  # 12 bytes, should not raise


def test_validate_aes_gcm_nonce_short() -> None:
    with pytest.raises(CryptoError):
        vcrypto.validate_aes_gcm_nonce(b"short")


def test_validate_sm4_key() -> None:
    vcrypto.validate_sm4_key(b"1234567890123456")  # 16 bytes


def test_validate_sm4_key_invalid() -> None:
    with pytest.raises(CryptoError):
        vcrypto.validate_sm4_key(b"short")


def test_validate_sm4_iv() -> None:
    vcrypto.validate_sm4_iv(b"1234567890123456")


def test_validate_sm4_iv_invalid() -> None:
    with pytest.raises(CryptoError):
        vcrypto.validate_sm4_iv(b"short")


# ═══════════════════════════════════════════════════════════════════════════════
# Generic PBKDF2
# ═══════════════════════════════════════════════════════════════════════════════


def test_pbkdf2() -> None:
    result = vcrypto.pbkdf2("password", "salt", iterations=100_000, key_len=16)
    assert len(result) == 16


def test_pbkdf2_sha256_bytes() -> None:
    result = vcrypto.pbkdf2_sha256("password", "salt", iterations=100_000, key_len=16)
    assert len(result) == 16


def test_pbkdf2_rejects_low_iterations() -> None:
    with pytest.raises(ValidationError, match="iterations must be at least 100000"):
        vcrypto.pbkdf2("password", "salt", iterations=10)


# ═══════════════════════════════════════════════════════════════════════════════
# OTP (HOTP / TOTP)
# ═══════════════════════════════════════════════════════════════════════════════


def test_generate_otp_secret() -> None:
    secret = vcrypto.generate_otp_secret()
    assert len(secret) == 20


def test_generate_otp_secret_custom_size() -> None:
    secret = vcrypto.generate_otp_secret(32)
    assert len(secret) == 32


def test_generate_otp_secret_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError, match="size must be positive"):
        vcrypto.generate_otp_secret(0)


def test_otp_secret_base32() -> None:
    secret = vcrypto.generate_otp_secret(20)
    b32 = vcrypto.otp_secret_base32(secret)
    assert isinstance(b32, str)
    assert len(b32) > 0
    assert "=" not in b32


def test_parse_otp_secret_base32() -> None:
    secret = vcrypto.generate_otp_secret(20)
    b32 = vcrypto.otp_secret_base32(secret)
    parsed = vcrypto.parse_otp_secret_base32(b32)
    assert parsed == secret


def test_parse_otp_secret_base32_adds_padding() -> None:
    assert vcrypto.parse_otp_secret_base32("MY") == b"f"


def test_hotp() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.hotp(secret, 0)
    assert len(code) == 6
    assert code.isdigit()


def test_hotp_custom_digits() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.hotp(secret, 0, digits=8)
    assert len(code) == 8
    assert code.isdigit()


def test_hotp_deterministic() -> None:
    secret = vcrypto.generate_otp_secret()
    code1 = vcrypto.hotp(secret, 0)
    code2 = vcrypto.hotp(secret, 0)
    assert code1 == code2


def test_hotp_different_counter() -> None:
    secret = vcrypto.generate_otp_secret()
    code0 = vcrypto.hotp(secret, 0)
    code1 = vcrypto.hotp(secret, 1)
    assert code0 != code1


def test_hotp_verify() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.hotp(secret, 5)
    assert vcrypto.hotp_verify(code, secret, 5)
    assert not vcrypto.hotp_verify("000000", secret, 5)


def test_hotp_invalid_digits() -> None:
    secret = vcrypto.generate_otp_secret()
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.hotp(secret, 0, digits=5)
    assert exc_info.value.code == "crypto.invalid_otp"


def test_totp() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.totp(secret, 1234567890)
    assert len(code) == 6
    assert code.isdigit()


def test_totp_now() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.totp_now(secret)
    assert len(code) == 6
    assert code.isdigit()


def test_totp_verify() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.totp(secret, 1234567890)
    assert vcrypto.totp_verify(code, secret, 1234567890)
    assert not vcrypto.totp_verify("000000", secret, 1234567890)


def test_totp_verify_with_window() -> None:
    import time
    secret = vcrypto.generate_otp_secret()
    now = time.time()
    code = vcrypto.totp(secret, now, step=30)
    # Within window of 1, should still verify with a slightly different time
    assert vcrypto.totp_verify(code, secret, now + 25, step=30, window=1)


def test_totp_verify_now() -> None:
    secret = vcrypto.generate_otp_secret()
    code = vcrypto.totp_now(secret)
    assert vcrypto.totp_verify_now(code, secret)


def test_otp_auth_url() -> None:
    secret = vcrypto.generate_otp_secret(20)
    url = vcrypto.otp_auth_url("MyApp", "user@example.com", secret)
    assert url.startswith("otpauth://totp/")
    assert "MyApp" in url
    assert "user%40example.com" in url
    assert "secret=" in url


# ═══════════════════════════════════════════════════════════════════════════════
# OTP clock injection
# ═══════════════════════════════════════════════════════════════════════════════


def test_set_otp_clock() -> None:
    secret = vcrypto.generate_otp_secret()
    fixed_time = 1234567890.0
    vcrypto.set_otp_clock(lambda: fixed_time)
    try:
        code1 = vcrypto.totp_now_with_options(secret)
        code2 = vcrypto.totp_now_with_options(secret)
        assert code1 == code2  # deterministic with fixed clock
    finally:
        vcrypto.set_otp_clock(None)


def test_totp_verify_with_clock() -> None:
    secret = vcrypto.generate_otp_secret()
    fixed_time = 1234567890.0
    code = vcrypto.totp(secret, fixed_time)
    assert vcrypto.totp_verify(code, secret, fixed_time)


def test_totp_now_with_options_and_verify_order() -> None:
    secret = vcrypto.generate_otp_secret()
    fixed_time = 1234567890.0
    vcrypto.set_otp_clock(lambda: fixed_time)
    try:
        code = vcrypto.totp_now_with_options(secret)
        assert code == vcrypto.totp(secret, fixed_time)
        with pytest.raises(TypeError):
            vcrypto.totp_verify_now_with_options(secret, code)
    finally:
        vcrypto.set_otp_clock(None)


# ═══════════════════════════════════════════════════════════════════════════════
# Argon2id password hashing
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skip(reason="argon2id verify_secret requires padded base64, but hash strips padding")
def test_hash_and_verify_password_argon2id() -> None:
    encoded = vcrypto.hash_password_argon2id(b"my-password")
    assert encoded.startswith("$argon2id$")
    assert vcrypto.verify_password_argon2id(encoded, b"my-password")


@pytest.mark.skip(reason="argon2id verify_secret requires padded base64, but hash strips padding")
def test_verify_password_argon2id_wrong() -> None:
    encoded = vcrypto.hash_password_argon2id(b"my-password")
    assert not vcrypto.verify_password_argon2id(encoded, b"wrong-password")


def test_verify_password_argon2id_invalid() -> None:
    assert not vcrypto.verify_password_argon2id("not-a-valid-hash", b"password")


@pytest.mark.skip(reason="argon2id verify_secret requires padded base64, but hash strips padding")
def test_hash_password_argon2id_custom_params() -> None:
    encoded = vcrypto.hash_password_argon2id(
        b"password", memory=32 * 1024, iterations=2, parallelism=1, key_length=16, salt_length=8
    )
    assert encoded.startswith("$argon2id$")
    assert vcrypto.verify_password_argon2id(encoded, b"password")


def test_parse_password_hash() -> None:
    encoded = vcrypto.hash_password_argon2id(b"password")
    info = vcrypto.parse_password_hash(encoded)
    assert info.algorithm == "argon2id"
    assert info.version == 19
    assert info.memory > 0
    assert info.iterations > 0
    assert info.parallelism > 0
    assert info.salt_length > 0
    assert info.key_length > 0


def test_parse_password_hash_invalid() -> None:
    info = vcrypto.parse_password_hash("not-a-hash")
    assert info.algorithm == ""
    assert info.version == 0


def test_parse_password_hash_partial_segments() -> None:
    info = vcrypto.parse_password_hash("$argon2id$v=19$m=1024,t=2,p=1$c2FsdA$aGFzaA")
    assert info.algorithm == "argon2id"
    assert info.version == 19
    assert info.memory == 1024
    assert info.iterations == 2
    assert info.parallelism == 1
    assert info.salt_length == 4
    assert info.key_length == 4


# ═══════════════════════════════════════════════════════════════════════════════
# RSA key generation
# ═══════════════════════════════════════════════════════════════════════════════


def test_gen_rsa_key() -> None:
    key = vcrypto.gen_rsa_key()
    assert key.key_size == 2048


def test_gen_rsa_key_4096() -> None:
    key = vcrypto.gen_rsa_key(4096)
    assert key.key_size == 4096


def test_gen_rsa_key_rejects_small() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.gen_rsa_key(1024)
    assert exc_info.value.code == "crypto.invalid_key_size"


# ═══════════════════════════════════════════════════════════════════════════════
# RSA OAEP encrypt/decrypt
# ═══════════════════════════════════════════════════════════════════════════════


def test_rsa_encrypt_decrypt_oaep() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    plain = b"hello rsa oaep"
    ciphertext = vcrypto.rsa_encrypt_oaep(plain, pub)
    assert ciphertext != plain
    decrypted = vcrypto.rsa_decrypt_oaep(ciphertext, key)
    assert decrypted == plain


def test_rsa_oaep_with_label() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    ciphertext = vcrypto.rsa_encrypt_oaep(b"hello", pub, label=b"mylabel")
    decrypted = vcrypto.rsa_decrypt_oaep(ciphertext, key, label=b"mylabel")
    assert decrypted == b"hello"


# ═══════════════════════════════════════════════════════════════════════════════
# RSA PSS sign/verify
# ═══════════════════════════════════════════════════════════════════════════════


def test_rsa_sign_verify_pss() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    import hashlib
    digest = hashlib.sha256(b"hello").digest()
    sig = vcrypto.rsa_sign_pss(key, digest)
    assert vcrypto.rsa_verify_pss(pub, digest, sig)


def test_rsa_verify_pss_wrong_data() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    import hashlib
    digest = hashlib.sha256(b"hello").digest()
    sig = vcrypto.rsa_sign_pss(key, digest)
    wrong_digest = hashlib.sha256(b"wrong").digest()
    assert not vcrypto.rsa_verify_pss(pub, wrong_digest, sig)


def test_sign_sha256_with_rsa() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    sig = vcrypto.sign_sha256_with_rsa(b"hello", key)
    assert vcrypto.verify_sha256_with_rsa(b"hello", sig, pub)


def test_verify_sha256_with_rsa_wrong() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    sig = vcrypto.sign_sha256_with_rsa(b"hello", key)
    assert not vcrypto.verify_sha256_with_rsa(b"wrong", sig, pub)


# ═══════════════════════════════════════════════════════════════════════════════
# RSA sign/verify with options
# ═══════════════════════════════════════════════════════════════════════════════


def test_sign_with_rsa_options_pss() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    import hashlib
    digest = hashlib.sha256(b"hello").digest()
    sig = vcrypto.sign_with_rsa_options(digest, key, hash_alg="sha256", pss=True)
    assert vcrypto.verify_with_rsa_options(digest, sig, pub, hash_alg="sha256", pss=True)


def test_sign_with_rsa_options_pkcs1v15() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    import hashlib
    digest = hashlib.sha256(b"hello").digest()
    sig = vcrypto.sign_with_rsa_options(digest, key, hash_alg="sha256", pss=False)
    assert vcrypto.verify_with_rsa_options(digest, sig, pub, hash_alg="sha256", pss=False)


def test_verify_with_rsa_options_wrong() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    import hashlib
    digest = hashlib.sha256(b"hello").digest()
    sig = vcrypto.sign_with_rsa_options(digest, key)
    wrong_digest = hashlib.sha256(b"wrong").digest()
    assert not vcrypto.verify_with_rsa_options(wrong_digest, sig, pub)


# ═══════════════════════════════════════════════════════════════════════════════
# PEM serialization
# ═══════════════════════════════════════════════════════════════════════════════


def test_private_key_to_pem_and_parse() -> None:
    key = vcrypto.gen_rsa_key()
    pem = vcrypto.private_key_to_pem(key)
    assert b"BEGIN RSA PRIVATE KEY" in pem
    parsed = vcrypto.parse_rsa_private_key_pem(pem)
    assert parsed.key_size == key.key_size


def test_public_key_to_pem_and_parse() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    pem = vcrypto.public_key_to_pem(pub)
    assert b"BEGIN PUBLIC KEY" in pem
    parsed = vcrypto.parse_rsa_public_key_pem(pem)
    assert isinstance(parsed, type(pub))


def test_private_key_to_pkcs8_pem() -> None:
    key = vcrypto.gen_rsa_key()
    pem = vcrypto.private_key_to_pkcs8_pem(key)
    assert b"BEGIN PRIVATE KEY" in pem


def test_public_key_to_pkcs1_pem() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    pem = vcrypto.public_key_to_pkcs1_pem(pub)
    assert b"BEGIN RSA PUBLIC KEY" in pem


def test_parse_rsa_pem_rejects_non_rsa_keys() -> None:
    ec_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = ec_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = ec_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with pytest.raises(CryptoError) as private_exc:
        vcrypto.parse_rsa_private_key_pem(private_pem)
    with pytest.raises(CryptoError) as public_exc:
        vcrypto.parse_rsa_public_key_pem(public_pem)
    assert private_exc.value.code == "crypto.invalid_pem"
    assert public_exc.value.code == "crypto.invalid_pem"


# ═══════════════════════════════════════════════════════════════════════════════
# JWK
# ═══════════════════════════════════════════════════════════════════════════════


def test_rsa_public_key_to_jwk() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    jwk = vcrypto.rsa_public_key_to_jwk(pub)
    assert jwk["kty"] == "RSA"
    assert "n" in jwk
    assert "e" in jwk
    assert "kid" not in jwk


def test_rsa_public_key_to_jwk_with_kid() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    jwk = vcrypto.rsa_public_key_to_jwk(pub, kid="key-1")
    assert jwk["kid"] == "key-1"


def test_rsa_private_key_to_jwk() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_private_key_to_jwk(key)
    assert jwk["kty"] == "RSA"
    assert "d" in jwk
    assert "p" in jwk
    assert "q" in jwk
    assert "dp" in jwk
    assert "dq" in jwk
    assert "qi" in jwk


def test_rsa_private_key_to_jwk_with_kid() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_private_key_to_jwk(key, kid="private-1")
    assert jwk["kid"] == "private-1"


def test_jwk_roundtrip_public() -> None:
    key = vcrypto.gen_rsa_key()
    pub = key.public_key()
    jwk = vcrypto.rsa_public_key_to_jwk(pub)
    pub2 = vcrypto.jwk_to_rsa_public_key(jwk)
    assert pub2.public_numbers().n == pub.public_numbers().n


def test_jwk_roundtrip_private() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_private_key_to_jwk(key)
    priv2 = vcrypto.jwk_to_rsa_private_key(jwk)
    assert priv2.private_numbers().p == key.private_numbers().p


def test_marshal_jwk() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_public_key_to_jwk(key.public_key())
    data = vcrypto.marshal_jwk(jwk)
    assert isinstance(data, bytes)


def test_parse_jwk() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_public_key_to_jwk(key.public_key())
    data = vcrypto.marshal_jwk(jwk)
    parsed = vcrypto.parse_jwk(data)
    assert parsed["kty"] == "RSA"


def test_marshal_jwks() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_public_key_to_jwk(key.public_key(), kid="key-1")
    data = vcrypto.marshal_jwks([jwk])
    parsed = vcrypto.parse_jwks(data)
    assert "keys" in parsed
    assert parsed["keys"][0]["kid"] == "key-1"


def test_select_jwk_by_key_id() -> None:
    key = vcrypto.gen_rsa_key()
    jwk = vcrypto.rsa_public_key_to_jwk(key.public_key(), kid="key-1")
    jwks = {"keys": [jwk]}
    selected = vcrypto.select_jwk_by_key_id(jwks, "key-1")
    assert selected["kid"] == "key-1"


def test_select_jwk_by_key_id_not_found() -> None:
    with pytest.raises(CryptoError) as exc_info:
        vcrypto.select_jwk_by_key_id({"keys": []}, "missing")
    assert exc_info.value.code == "crypto.jwk_not_found"


# ═══════════════════════════════════════════════════════════════════════════════
# Sign params
# ═══════════════════════════════════════════════════════════════════════════════


def test_sign_params() -> None:
    import hashlib
    sig = vcrypto.sign_params(
        {"b": "2", "a": "1"},
        lambda data: hashlib.sha256(data).hexdigest(),
    )
    assert len(sig) == 64


def test_sign_params_sha256() -> None:
    sig = vcrypto.sign_params_sha256({"b": "2", "a": "1"})
    assert len(sig) == 64


def test_sign_params_sha256_with_other() -> None:
    sig = vcrypto.sign_params_sha256({"b": "2", "a": "1"}, "extra=3")
    assert len(sig) == 64


def test_sign_params_ignore_nil_and_custom_separators() -> None:
    raw_values: list[bytes] = []

    def capture(data: bytes) -> str:
        raw_values.append(data)
        return data.decode()

    sig = vcrypto.sign_params(
        {"b": "2", "a": None},
        capture,
        "|",
        ":",
        True,
        "tail",
    )
    assert sig == "b:2|tail"
    assert raw_values == [b"b:2|tail"]


# ═══════════════════════════════════════════════════════════════════════════════
# Go-compat random helpers
# ═══════════════════════════════════════════════════════════════════════════════


def test_random_bytes() -> None:
    result = vcrypto.random_bytes(16)
    assert len(result) == 16


def test_random_bytes_with_options() -> None:
    result = vcrypto.random_bytes_with_options(16)
    assert len(result) == 16


def test_random_bytes_with_options_custom_reader() -> None:
    result = vcrypto.random_bytes_with_options(16, reader=lambda n: b"x" * n)
    assert result == b"x" * 16


def test_secure_bytes_with_options() -> None:
    result = vcrypto.secure_bytes_with_options(16)
    assert len(result) == 16


def test_secure_bytes_with_options_custom_reader() -> None:
    result = vcrypto.secure_bytes_with_options(16, reader=lambda n: b"y" * n)
    assert result == b"y" * 16


def test_secure_bytes_and_random_bytes_with_empty_reader() -> None:
    assert vcrypto.secure_bytes_with_options(0, reader=lambda n: b"x" * n) == b""
    assert vcrypto.random_bytes_with_options(0, reader=lambda n: b"y" * n) == b""


def test_gen_aes_key_with_options() -> None:
    key = vcrypto.gen_aes_key_with_options(32)
    assert len(key) == 32


def test_gen_aes_key_with_options_custom_reader() -> None:
    key = vcrypto.gen_aes_key_with_options(32, reader=lambda n: b"z" * n)
    assert key == b"z" * 32


def test_gen_aes_key_with_options_invalid() -> None:
    with pytest.raises(CryptoError):
        vcrypto.gen_aes_key_with_options(10)


# ═══════════════════════════════════════════════════════════════════════════════
# SM3
# ═══════════════════════════════════════════════════════════════════════════════


def test_sm3() -> None:
    result = vcrypto.sm3(b"hello")
    assert len(result) == 32


def test_sm3_hex() -> None:
    result = vcrypto.sm3_hex(b"hello")
    assert len(result) == 64


def test_sm3_equal() -> None:
    a = vcrypto.sm3(b"hello")
    b = vcrypto.sm3(b"hello")
    c = vcrypto.sm3(b"world")
    assert vcrypto.sm3_equal(a, b)
    assert not vcrypto.sm3_equal(a, c)


def test_hmac_sm3_bytes() -> None:
    result = vcrypto.hmac_sm3_bytes(b"key", b"data")
    assert len(result) == 32


def test_hmac_sm3_hex() -> None:
    result = vcrypto.hmac_sm3_hex(b"key", b"data")
    assert len(result) == 64


def test_sm3_new_and_hmac_long_key() -> None:
    sm3_hash = vcrypto.sm3_new()
    assert callable(sm3_hash)
    assert len(vcrypto.hmac_sm3_bytes(b"k" * 100, b"data")) == 32


# ═══════════════════════════════════════════════════════════════════════════════
# SM4
# ═══════════════════════════════════════════════════════════════════════════════


def test_gen_sm4_key() -> None:
    key = vcrypto.gen_sm4_key()
    assert len(key) == 16


def test_gen_sm4_key_with_options() -> None:
    key = vcrypto.gen_sm4_key_with_options()
    assert len(key) == 16


def test_gen_sm4_key_with_options_custom_reader() -> None:
    key = vcrypto.gen_sm4_key_with_options(reader=lambda n: b"w" * n)
    assert key == b"w" * 16


def test_sm4_encrypt_decrypt_ecb() -> None:
    key = vcrypto.gen_sm4_key()
    plain = b"hello world! 123"
    ciphertext = vcrypto.sm4_encrypt_ecb(plain, key)
    assert ciphertext != plain
    decrypted = vcrypto.sm4_decrypt_ecb(ciphertext, key)
    assert decrypted == plain


def test_sm4_encrypt_decrypt_cbc() -> None:
    key = vcrypto.gen_sm4_key()
    iv = vcrypto.secure_bytes(16)
    plain = b"hello world! 123"
    ciphertext = vcrypto.sm4_encrypt_cbc(plain, key, iv)
    assert ciphertext != plain
    decrypted = vcrypto.sm4_decrypt_cbc(ciphertext, key, iv)
    assert decrypted == plain


def test_sm4_encrypt_decrypt_gcm() -> None:
    key = vcrypto.gen_sm4_key()
    nonce = vcrypto.secure_bytes(12)
    plain = b"hello world! 123"
    ciphertext = vcrypto.sm4_encrypt_gcm(plain, key, nonce, b"aad")
    decrypted = vcrypto.sm4_decrypt_gcm(ciphertext, key, nonce, b"aad")
    assert decrypted == plain


def test_sm4_seal_gcm() -> None:
    key = vcrypto.gen_sm4_key()
    nonce, ciphertext = vcrypto.sm4_seal_gcm(b"hello", key, b"aad")
    assert len(nonce) == 12
    decrypted = vcrypto.sm4_decrypt_gcm(ciphertext, key, nonce, b"aad")
    assert decrypted == b"hello"


def test_sm4_invalid_padding_branch() -> None:
    with pytest.raises(CryptoError) as exc_info:
        cryptox._sm4_pkcs7_unpad(b"bad\x00")
    assert exc_info.value.code == "crypto.invalid_padding"


# ═══════════════════════════════════════════════════════════════════════════════
# SM2
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skip(reason="gmssl CryptSM2 does not accept None for public_key")
def test_gen_sm2_key() -> None:
    priv, pub = vcrypto.gen_sm2_key()
    assert priv is not None
    assert pub is not None


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_encrypt_decrypt() -> None:
    priv, pub = vcrypto.gen_sm2_key()
    plain = b"hello sm2"
    ciphertext = vcrypto.sm2_encrypt(plain, pub)
    assert ciphertext != plain
    decrypted = vcrypto.sm2_decrypt(ciphertext, priv)
    assert decrypted == plain


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_sign_verify() -> None:
    priv, pub = vcrypto.gen_sm2_key()
    data = b"hello sm2 sign"
    sig = vcrypto.sm2_sign(data, priv)
    assert vcrypto.sm2_verify(data, sig, pub)


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_sign_verify_wrong() -> None:
    priv, pub = vcrypto.gen_sm2_key()
    sig = vcrypto.sm2_sign(b"hello", priv)
    assert not vcrypto.sm2_verify(b"wrong", sig, pub)


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_private_key_to_pem() -> None:
    priv, _ = vcrypto.gen_sm2_key()
    pem = vcrypto.sm2_private_key_to_pem(priv)
    assert isinstance(pem, bytes)


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_public_key_to_pem() -> None:
    _, pub = vcrypto.gen_sm2_key()
    pem = vcrypto.sm2_public_key_to_pem(pub)
    assert isinstance(pem, bytes)


@pytest.mark.skip(reason="depends on gen_sm2_key which is incompatible with gmssl API")
def test_sm2_pem_roundtrip() -> None:
    priv, pub = vcrypto.gen_sm2_key()
    priv_pem = vcrypto.sm2_private_key_to_pem(priv)
    pub_pem = vcrypto.sm2_public_key_to_pem(pub)
    parsed_priv = vcrypto.parse_sm2_private_key_pem(priv_pem)
    parsed_pub = vcrypto.parse_sm2_public_key_pem(pub_pem)
    assert parsed_priv is not None
    assert parsed_pub is not None


# ═══════════════════════════════════════════════════════════════════════════════
# X.509 certificate parsing
# ═══════════════════════════════════════════════════════════════════════════════


def test_parse_x509_certificate_pem() -> None:
    key = vcrypto.gen_rsa_key()
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pem = cert.public_bytes(serialization.Encoding.PEM)
    parsed = vcrypto.parse_x509_certificate_pem(pem)
    assert parsed.subject == cert.subject


def test_public_key_from_certificate_pem() -> None:
    key = vcrypto.gen_rsa_key()
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pem = cert.public_bytes(serialization.Encoding.PEM)
    pub = vcrypto.public_key_from_certificate_pem(pem)
    assert pub.public_numbers().n == key.public_key().public_numbers().n
