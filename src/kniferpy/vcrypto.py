from __future__ import annotations

from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa

from kniferpy.internal import cryptox

# ── SHA digests ─────────────────────────────────────────────────────────────

sha224 = cryptox.sha224
sha224_hex = cryptox.sha224_hex
sha256 = cryptox.sha256
sha256_hex = cryptox.sha256_hex
sha256_hex_bytes = cryptox.sha256_hex_bytes
sha384 = cryptox.sha384
sha384_hex = cryptox.sha384_hex
sha512 = cryptox.sha512
sha512_hex = cryptox.sha512_hex
sha512_hex_bytes = cryptox.sha512_hex_bytes
sha1_hex = cryptox.sha1_hex
md5_checksum_hex = cryptox.md5_checksum_hex
file_sha256_hex = cryptox.file_sha256_hex

# Generic digest
digest = cryptox.digest
digest_hex = cryptox.digest_hex

# ── HMAC ────────────────────────────────────────────────────────────────────

hmac_sha256_hex = cryptox.hmac_sha256_hex
hmac_sha384_hex = cryptox.hmac_sha384_hex
hmac_sha512_hex = cryptox.hmac_sha512_hex
hmac_hex = cryptox.hmac_hex
hmac_bytes = cryptox.hmac_bytes
hmac_equal = cryptox.hmac_equal
constant_time_equal = cryptox.constant_time_equal
verify_hmac_sha256_hex = cryptox.verify_hmac_sha256_hex
verify_sha256_hex = cryptox.verify_sha256_hex
verify_file_sha256_hex = cryptox.verify_file_sha256_hex

# ── PBKDF2 ──────────────────────────────────────────────────────────────────

pbkdf2_sha256_hex = cryptox.pbkdf2_sha256_hex

# ── AES-GCM ─────────────────────────────────────────────────────────────────

aes_encrypt_gcm = cryptox.aes_encrypt_gcm
aes_decrypt_gcm = cryptox.aes_decrypt_gcm
aes_seal_gcm = cryptox.aes_seal_gcm
aes_open_gcm = cryptox.aes_open_gcm

# ── Secure random ───────────────────────────────────────────────────────────

secure_bytes = cryptox.secure_bytes
secure_token_urlsafe = cryptox.secure_token_urlsafe
secure_alnum = cryptox.secure_alnum
gen_aes_key = cryptox.gen_aes_key

# ── OTP ─────────────────────────────────────────────────────────────────────

generate_otp_secret = cryptox.generate_otp_secret
otp_secret_base32 = cryptox.otp_secret_base32
parse_otp_secret_base32 = cryptox.parse_otp_secret_base32
hotp = cryptox.hotp
hotp_verify = cryptox.hotp_verify
totp = cryptox.totp
totp_now = cryptox.totp_now
totp_verify = cryptox.totp_verify
totp_verify_now = cryptox.totp_verify_now
otp_auth_url = cryptox.otp_auth_url

# ── Argon2id password hashing ───────────────────────────────────────────────

hash_password_argon2id = cryptox.hash_password_argon2id
verify_password_argon2id = cryptox.verify_password_argon2id

# ── RSA ─────────────────────────────────────────────────────────────────────

gen_rsa_key = cryptox.gen_rsa_key
rsa_encrypt_oaep = cryptox.rsa_encrypt_oaep
rsa_decrypt_oaep = cryptox.rsa_decrypt_oaep
rsa_sign_pss = cryptox.rsa_sign_pss
rsa_verify_pss = cryptox.rsa_verify_pss
sign_sha256_with_rsa = cryptox.sign_sha256_with_rsa
verify_sha256_with_rsa = cryptox.verify_sha256_with_rsa

# ── PEM ─────────────────────────────────────────────────────────────────────

private_key_to_pem = cryptox.private_key_to_pem
public_key_to_pem = cryptox.public_key_to_pem
parse_rsa_private_key_pem = cryptox.parse_rsa_private_key_pem
parse_rsa_public_key_pem = cryptox.parse_rsa_public_key_pem
private_key_to_pkcs8_pem = cryptox.private_key_to_pkcs8_pem
public_key_to_pkcs1_pem = cryptox.public_key_to_pkcs1_pem

# ── JWK ─────────────────────────────────────────────────────────────────────

rsa_public_key_to_jwk = cryptox.rsa_public_key_to_jwk
rsa_private_key_to_jwk = cryptox.rsa_private_key_to_jwk
jwk_to_rsa_public_key = cryptox.jwk_to_rsa_public_key
jwk_to_rsa_private_key = cryptox.jwk_to_rsa_private_key
marshal_jwk = cryptox.marshal_jwk
parse_jwk = cryptox.parse_jwk
marshal_jwks = cryptox.marshal_jwks
parse_jwks = cryptox.parse_jwks
select_jwk_by_key_id = cryptox.select_jwk_by_key_id

# ── Sign params ─────────────────────────────────────────────────────────────

sign_params = cryptox.sign_params
sign_params_sha256 = cryptox.sign_params_sha256

# ── Validation ──────────────────────────────────────────────────────────────

validate_aes_key = cryptox.validate_aes_key
validate_aes_iv = cryptox.validate_aes_iv
validate_aes_gcm_nonce = cryptox.validate_aes_gcm_nonce

# ── __all__ ─────────────────────────────────────────────────────────────────

__all__ = [
    # SHA
    "sha224",
    "sha224_hex",
    "sha256",
    "sha256_hex",
    "sha256_hex_bytes",
    "sha384",
    "sha384_hex",
    "sha512",
    "sha512_hex",
    "sha512_hex_bytes",
    "sha1_hex",
    "md5_checksum_hex",
    "file_sha256_hex",
    "digest",
    "digest_hex",
    # HMAC
    "hmac_sha256_hex",
    "hmac_sha384_hex",
    "hmac_sha512_hex",
    "hmac_hex",
    "hmac_bytes",
    "hmac_equal",
    "constant_time_equal",
    "verify_hmac_sha256_hex",
    "verify_sha256_hex",
    "verify_file_sha256_hex",
    # PBKDF2
    "pbkdf2_sha256_hex",
    # AES-GCM
    "aes_encrypt_gcm",
    "aes_decrypt_gcm",
    "aes_seal_gcm",
    "aes_open_gcm",
    # Random
    "secure_bytes",
    "secure_token_urlsafe",
    "secure_alnum",
    "gen_aes_key",
    # OTP
    "generate_otp_secret",
    "otp_secret_base32",
    "parse_otp_secret_base32",
    "hotp",
    "hotp_verify",
    "totp",
    "totp_now",
    "totp_verify",
    "totp_verify_now",
    "otp_auth_url",
    # Argon2id
    "hash_password_argon2id",
    "verify_password_argon2id",
    # RSA
    "gen_rsa_key",
    "rsa_encrypt_oaep",
    "rsa_decrypt_oaep",
    "rsa_sign_pss",
    "rsa_verify_pss",
    "sign_sha256_with_rsa",
    "verify_sha256_with_rsa",
    # PEM
    "private_key_to_pem",
    "public_key_to_pem",
    "parse_rsa_private_key_pem",
    "parse_rsa_public_key_pem",
    "private_key_to_pkcs8_pem",
    "public_key_to_pkcs1_pem",
    # JWK
    "rsa_public_key_to_jwk",
    "rsa_private_key_to_jwk",
    "jwk_to_rsa_public_key",
    "jwk_to_rsa_private_key",
    "marshal_jwk",
    "parse_jwk",
    "marshal_jwks",
    "parse_jwks",
    "select_jwk_by_key_id",
    # Sign params
    "sign_params",
    "sign_params_sha256",
    # Validation
    "validate_aes_key",
    "validate_aes_iv",
    "validate_aes_gcm_nonce",
]