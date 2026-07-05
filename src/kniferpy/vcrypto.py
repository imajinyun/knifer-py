from __future__ import annotations

from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa

from kniferpy.internal import cryptox

# ── Error sentinels ──────────────────────────────────────────────────────────

ErrInvalidKey = cryptox.ErrInvalidKey
ErrInvalidIV = cryptox.ErrInvalidIV
ErrInvalidCipherText = cryptox.ErrInvalidCipherText
ErrInvalidSM2Signature = cryptox.ErrInvalidSM2Signature
ErrInvalidOTP = cryptox.ErrInvalidOTP
ErrInvalidPasswordHash = cryptox.ErrInvalidPasswordHash
ErrInvalidJWK = cryptox.ErrInvalidJWK

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

pbkdf2 = cryptox.pbkdf2
pbkdf2_sha256 = cryptox.pbkdf2_sha256
pbkdf2_sha256_hex = cryptox.pbkdf2_sha256_hex

# ── AES-GCM ─────────────────────────────────────────────────────────────────

aes_encrypt_gcm = cryptox.aes_encrypt_gcm
aes_decrypt_gcm = cryptox.aes_decrypt_gcm
aes_seal_gcm = cryptox.aes_seal_gcm
aes_open_gcm = cryptox.aes_open_gcm

# ── Secure random ───────────────────────────────────────────────────────────

secure_bytes = cryptox.secure_bytes
secure_bytes_with_options = cryptox.secure_bytes_with_options
secure_token_urlsafe = cryptox.secure_token_urlsafe
secure_alnum = cryptox.secure_alnum
gen_aes_key = cryptox.gen_aes_key
gen_aes_key_with_options = cryptox.gen_aes_key_with_options

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
totp_now_with_options = cryptox.totp_now_with_options
totp_verify_now_with_options = cryptox.totp_verify_now_with_options
set_otp_clock = cryptox.set_otp_clock
otp_auth_url = cryptox.otp_auth_url

# ── Argon2id password hashing ───────────────────────────────────────────────

hash_password_argon2id = cryptox.hash_password_argon2id
verify_password_argon2id = cryptox.verify_password_argon2id
parse_password_hash = cryptox.parse_password_hash

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
parse_x509_certificate_pem = cryptox.parse_x509_certificate_pem
public_key_from_certificate_pem = cryptox.public_key_from_certificate_pem

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
validate_sm4_key = cryptox.validate_sm4_key
validate_sm4_iv = cryptox.validate_sm4_iv

# ── *WithOptions aliases (Go compat) ──────────────────────────────────────────

gen_aes_key_with_options = cryptox.gen_aes_key_with_options
secure_bytes_with_options = cryptox.secure_bytes_with_options
totp_now_with_options = cryptox.totp_now_with_options
totp_verify_now_with_options = cryptox.totp_verify_now_with_options

# ── Go-compat random_bytes ──────────────────────────────────────────────────

random_bytes = cryptox.random_bytes
random_bytes_with_options = cryptox.random_bytes_with_options

# ── SM3 ─────────────────────────────────────────────────────────────────────

sm3 = cryptox.sm3
sm3_hex = cryptox.sm3_hex
sm3_new = cryptox.sm3_new
sm3_equal = cryptox.sm3_equal
hmac_sm3_bytes = cryptox.hmac_sm3_bytes
hmac_sm3_hex = cryptox.hmac_sm3_hex

# ── SM4 ─────────────────────────────────────────────────────────────────────

gen_sm4_key = cryptox.gen_sm4_key
gen_sm4_key_with_options = cryptox.gen_sm4_key_with_options
sm4_encrypt_ecb = cryptox.sm4_encrypt_ecb
sm4_decrypt_ecb = cryptox.sm4_decrypt_ecb
sm4_encrypt_cbc = cryptox.sm4_encrypt_cbc
sm4_decrypt_cbc = cryptox.sm4_decrypt_cbc
sm4_encrypt_gcm = cryptox.sm4_encrypt_gcm
sm4_decrypt_gcm = cryptox.sm4_decrypt_gcm
sm4_seal_gcm = cryptox.sm4_seal_gcm

# ── SM2 ─────────────────────────────────────────────────────────────────────

gen_sm2_key = cryptox.gen_sm2_key
sm2_encrypt = cryptox.sm2_encrypt
sm2_decrypt = cryptox.sm2_decrypt
sm2_sign = cryptox.sm2_sign
sm2_verify = cryptox.sm2_verify
sm2_private_key_to_pem = cryptox.sm2_private_key_to_pem
sm2_public_key_to_pem = cryptox.sm2_public_key_to_pem
parse_sm2_private_key_pem = cryptox.parse_sm2_private_key_pem
parse_sm2_public_key_pem = cryptox.parse_sm2_public_key_pem

# ── Go-compat sign/verify with RSA options ──────────────────────────────────

sign_with_rsa_options = cryptox.sign_with_rsa_options
verify_with_rsa_options = cryptox.verify_with_rsa_options

# ── __all__ ─────────────────────────────────────────────────────────────────

__all__ = [
    # Error sentinels
    "ErrInvalidKey",
    "ErrInvalidIV",
    "ErrInvalidCipherText",
    "ErrInvalidSM2Signature",
    "ErrInvalidOTP",
    "ErrInvalidPasswordHash",
    "ErrInvalidJWK",
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
    "pbkdf2",
    "pbkdf2_sha256",
    "pbkdf2_sha256_hex",
    # AES-GCM
    "aes_encrypt_gcm",
    "aes_decrypt_gcm",
    "aes_seal_gcm",
    "aes_open_gcm",
    # Random
    "secure_bytes",
    "secure_bytes_with_options",
    "secure_token_urlsafe",
    "secure_alnum",
    "gen_aes_key",
    "gen_aes_key_with_options",
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
    "totp_now_with_options",
    "totp_verify_now_with_options",
    "set_otp_clock",
    "otp_auth_url",
    # Argon2id
    "hash_password_argon2id",
    "verify_password_argon2id",
    "parse_password_hash",
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
    "parse_x509_certificate_pem",
    "public_key_from_certificate_pem",
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
    "validate_sm4_key",
    "validate_sm4_iv",
    # Go-compat random_bytes
    "random_bytes",
    "random_bytes_with_options",
    # SM3
    "sm3",
    "sm3_hex",
    "sm3_new",
    "sm3_equal",
    "hmac_sm3_bytes",
    "hmac_sm3_hex",
    # SM4
    "gen_sm4_key",
    "gen_sm4_key_with_options",
    "sm4_encrypt_ecb",
    "sm4_decrypt_ecb",
    "sm4_encrypt_cbc",
    "sm4_decrypt_cbc",
    "sm4_encrypt_gcm",
    "sm4_decrypt_gcm",
    "sm4_seal_gcm",
    # SM2
    "gen_sm2_key",
    "sm2_encrypt",
    "sm2_decrypt",
    "sm2_sign",
    "sm2_verify",
    "sm2_private_key_to_pem",
    "sm2_public_key_to_pem",
    "parse_sm2_private_key_pem",
    "parse_sm2_public_key_pem",
    # Go-compat sign/verify with RSA options
    "sign_with_rsa_options",
    "verify_with_rsa_options",
]