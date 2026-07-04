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
from kniferpy.internal.jwtx import JWTBuilder

__all__ = [
    "JWTBuilder",
    "algorithm_name",
    "create_signer",
    "generate_ec_key",
    "generate_rsa_key",
    "jwt_of",
    "min_hmac_key_bytes",
    "new_jwt",
    "new_jwt_builder",
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