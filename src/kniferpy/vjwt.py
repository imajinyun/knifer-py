"""JWT signing, verification, and validation.

HMAC (HS256/HS384/HS512), ECDSA (ES256/ES384/ES512), and RSA-PSS
(PS256/PS384/PS512) signers. Fluent :class:`JWTBuilder` for claims
construction and token verification. Also includes JWT parsing, strict
algorithm verification, and date validation.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ec, rsa

from kniferpy.internal import jwtx
from kniferpy.internal.jwtx import JWTBuilder, JWTSigner

# ── Algorithm Constants ───────────────────────────────────────────────────────

JWTAlgHS256 = "HS256"
JWTAlgHS384 = "HS384"
JWTAlgHS512 = "HS512"
JWTAlgPS256 = "PS256"
JWTAlgPS384 = "PS384"
JWTAlgPS512 = "PS512"
JWTAlgES256 = "ES256"
JWTAlgES384 = "ES384"
JWTAlgES512 = "ES512"

# ── Header Key Constants ──────────────────────────────────────────────────────

JWTHeaderAlgorithm = "alg"
JWTHeaderType = "typ"
JWTHeaderContentType = "cty"
JWTHeaderKeyID = "kid"

# ── Payload Key Constants ─────────────────────────────────────────────────────

JWTPayloadIssuer = "iss"
JWTPayloadSubject = "sub"
JWTPayloadAudience = "aud"
JWTPayloadExpiresAt = "exp"
JWTPayloadNotBefore = "nbf"
JWTPayloadIssuedAt = "iat"
JWTPayloadJWTID = "jti"

# ── Min HMAC Key Byte Constants ────────────────────────────────────────────────

MinHMACKeyBytesHS256 = 32
MinHMACKeyBytesHS384 = 48
MinHMACKeyBytesHS512 = 64

# ── Error ─────────────────────────────────────────────────────────────────────

from kniferpy.verr import CryptoError as JWTError


def new_jwt_error(msg: str) -> JWTError:
    return JWTError(msg)


def jwt_errorf(format_str: str, *args: Any) -> JWTError:
    return JWTError(format_str % args)

__all__ = [
    "JWTBuilder",
    "JWTSigner",
    "JWTError",
    "algorithm_name",
    "create_signer",
    "generate_ec_key",
    "generate_rsa_key",
    "jwt_of",
    "jwt_errorf",
    "min_hmac_key_bytes",
    "new_jwt",
    "new_jwt_builder",
    "new_jwt_error",
    "parse_jwt",
    "sign_es256",
    "sign_es384",
    "sign_es512",
    "sign_hs256",
    "sign_hs384",
    "sign_hs512",
    "sign_ps256",
    "sign_ps384",
    "sign_ps512",
    "validate_algorithm",
    "validate_date",
    "validate_jwt_date",
    "verify_es256",
    "verify_es384",
    "verify_es512",
    "verify_hs256",
    "verify_hs384",
    "verify_hs512",
    "verify_ps256",
    "verify_ps384",
    "verify_ps512",
    "verify_strict",
    # Go-compat generic creation
    "create_token",
    "create_jwt_token",
    "create_token_with_headers",
    "create_token_with_algorithm",
    "create_token_with_headers_and_algorithm",
    # Go-compat generic verification
    "verify",
    "verify_jwt",
    "of_validator",
    # Go-compat signer constructors
    "HS256",
    "HS384",
    "HS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
    "new_hmac_signer",
    "new_hmac_signer_strict",
    "must_hmac_signer",
    "new_rsa_pss_signer",
    "new_ecdsa_signer",
    "create_signer_from_key",
    "create_signer_from_key_strict",
    "jwtsigner_hmac",
    "jwtsigner_hs256",
    "jwtsigner_ecdsa",
    "jwtsigner_es256",
    # Go-compat CreateToken/Verify with signer
    "create_token_with_signer",
    "create_token_with_headers_and_signer",
    "create_jwt_token_with_signer",
    "verify_with_signer",
    "verify_jwt_with_signer",
    "verify_strict_signer",
    "validate_algorithm_with_signer",
    # Algorithm constants
    "JWTAlgHS256",
    "JWTAlgHS384",
    "JWTAlgHS512",
    "JWTAlgPS256",
    "JWTAlgPS384",
    "JWTAlgPS512",
    "JWTAlgES256",
    "JWTAlgES384",
    "JWTAlgES512",
    # Header key constants
    "JWTHeaderAlgorithm",
    "JWTHeaderType",
    "JWTHeaderContentType",
    "JWTHeaderKeyID",
    # Payload key constants
    "JWTPayloadIssuer",
    "JWTPayloadSubject",
    "JWTPayloadAudience",
    "JWTPayloadExpiresAt",
    "JWTPayloadNotBefore",
    "JWTPayloadIssuedAt",
    "JWTPayloadJWTID",
    # Min key bytes
    "MinHMACKeyBytesHS256",
    "MinHMACKeyBytesHS384",
    "MinHMACKeyBytesHS512",
]

# ── HMAC ──────────────────────────────────────────────────────────────────────

sign_hs256 = jwtx.sign_hs256
sign_hs384 = jwtx.sign_hs384
sign_hs512 = jwtx.sign_hs512
verify_hs256 = jwtx.verify_hs256
verify_hs384 = jwtx.verify_hs384
verify_hs512 = jwtx.verify_hs512

# ── ECDSA ─────────────────────────────────────────────────────────────────────

sign_es256 = jwtx.sign_es256
sign_es384 = jwtx.sign_es384
sign_es512 = jwtx.sign_es512
verify_es256 = jwtx.verify_es256
verify_es384 = jwtx.verify_es384
verify_es512 = jwtx.verify_es512

# ── RSA-PSS ───────────────────────────────────────────────────────────────────

sign_ps256 = jwtx.sign_ps256
sign_ps384 = jwtx.sign_ps384
sign_ps512 = jwtx.sign_ps512
verify_ps256 = jwtx.verify_ps256
verify_ps384 = jwtx.verify_ps384
verify_ps512 = jwtx.verify_ps512

# ── JWT parsing ───────────────────────────────────────────────────────────────

parse_jwt = jwtx.parse_jwt
new_jwt = jwtx.new_jwt
jwt_of = jwtx.jwt_of

# ── Strict verification ───────────────────────────────────────────────────────

verify_strict = jwtx.verify_strict
validate_algorithm = jwtx.validate_algorithm

# ── Date validation ───────────────────────────────────────────────────────────

validate_jwt_date = jwtx.validate_jwt_date
validate_date = jwtx.validate_date

# ── Utility ───────────────────────────────────────────────────────────────────

min_hmac_key_bytes = jwtx.min_hmac_key_bytes
algorithm_name = jwtx.algorithm_name
create_signer = jwtx.create_signer

# ── Key generation ────────────────────────────────────────────────────────────

generate_ec_key = jwtx.generate_ec_key
generate_rsa_key = jwtx.generate_rsa_key

# ── Builder ───────────────────────────────────────────────────────────────────

new_jwt_builder = jwtx.new_jwt_builder

# ── Go-compat generic token creation ─────────────────────────────────────────

create_token = jwtx.create_token
create_jwt_token = jwtx.create_jwt_token
create_token_with_headers = jwtx.create_token_with_headers
create_token_with_algorithm = jwtx.create_token_with_algorithm
create_token_with_headers_and_algorithm = jwtx.create_token_with_headers_and_algorithm

# ── Go-compat generic verification ───────────────────────────────────────────

verify = jwtx.verify
verify_jwt = jwtx.verify_jwt
of_validator = jwtx.of_validator

# ── Go-compat signer constructors ────────────────────────────────────────────

HS256 = jwtx.HS256
HS384 = jwtx.HS384
HS512 = jwtx.HS512
PS256 = jwtx.PS256
PS384 = jwtx.PS384
PS512 = jwtx.PS512
ES256 = jwtx.ES256
ES384 = jwtx.ES384
ES512 = jwtx.ES512

new_hmac_signer = jwtx.new_hmac_signer
new_hmac_signer_strict = jwtx.new_hmac_signer_strict
must_hmac_signer = jwtx.must_hmac_signer
new_rsa_pss_signer = jwtx.new_rsa_pss_signer
new_ecdsa_signer = jwtx.new_ecdsa_signer
create_signer_from_key = jwtx.create_signer_from_key
create_signer_from_key_strict = jwtx.create_signer_from_key_strict

jwtsigner_hmac = jwtx.jwtsigner_hmac
jwtsigner_hs256 = jwtx.jwtsigner_hs256
jwtsigner_ecdsa = jwtx.jwtsigner_ecdsa
jwtsigner_es256 = jwtx.jwtsigner_es256

# ── Go-compat CreateToken/Verify with signer ─────────────────────────────────

create_token_with_signer = jwtx.create_token_with_signer
create_token_with_headers_and_signer = jwtx.create_token_with_headers_and_signer
create_jwt_token_with_signer = jwtx.create_jwt_token_with_signer
verify_with_signer = jwtx.verify_with_signer
verify_jwt_with_signer = jwtx.verify_jwt_with_signer
verify_strict_signer = jwtx.verify_strict_signer
validate_algorithm_with_signer = jwtx.validate_algorithm_with_signer