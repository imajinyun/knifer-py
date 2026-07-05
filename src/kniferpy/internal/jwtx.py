from __future__ import annotations

import base64
import hmac as _hmac
import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.algorithms import NoneAlgorithm

from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, utils
from cryptography.hazmat.primitives import hashes

from kniferpy.verr import CryptoError

_MIN_HS256_SECRET_BYTES = 32
_MIN_HS384_SECRET_BYTES = 48
_MIN_HS512_SECRET_BYTES = 64


_HMAC_MIN_BYTES: dict[str, int] = {
    "HS256": _MIN_HS256_SECRET_BYTES,
    "HS384": _MIN_HS384_SECRET_BYTES,
    "HS512": _MIN_HS512_SECRET_BYTES,
}


def min_hmac_key_bytes(algorithm: str) -> int:
    """Return the minimum recommended HMAC key length for ``algorithm``."""
    return _HMAC_MIN_BYTES.get(algorithm.upper(), 0)


def algorithm_name(alg: str) -> str:
    """Return the standard cryptographic algorithm name for a JWT algorithm ID."""
    mapping: dict[str, str] = {
        "HS256": "HmacSHA256",
        "HS384": "HmacSHA384",
        "HS512": "HmacSHA512",
        "RS256": "SHA256withRSA",
        "RS384": "SHA384withRSA",
        "RS512": "SHA512withRSA",
        "ES256": "SHA256withECDSA",
        "ES384": "SHA384withECDSA",
        "ES512": "SHA512withECDSA",
        "PS256": "SHA256withRSAandMGF1",
        "PS384": "SHA384withRSAandMGF1",
        "PS512": "SHA512withRSAandMGF1",
    }
    return mapping.get(alg.upper(), alg.upper())


# ── HMAC signing ──────────────────────────────────────────────────────────────


def _sign_hmac(payload: dict[str, Any], secret: str | bytes, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    _validate_hmac_secret(secret, alg)
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, secret, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_hmac(token: str, secret: str | bytes, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    _validate_hmac_secret(secret, alg)
    try:
        payload = jwt.decode(token, secret, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def _validate_hmac_secret(secret: str | bytes, alg: str) -> None:
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
    min_bytes = _HMAC_MIN_BYTES.get(alg.upper(), 0)
    if len(secret_bytes) < min_bytes:
        raise CryptoError(
            f"{alg} secret must be at least {min_bytes} bytes",
            code="jwt.weak_secret",
            context={"min_bytes": min_bytes},
        )


def sign_hs256(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS256", expires_in=expires_in)


def sign_hs384(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS384", expires_in=expires_in)


def sign_hs512(payload: dict[str, Any], secret: str | bytes, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_hmac(payload, secret, "HS512", expires_in=expires_in)


def verify_hs256(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS256", issuer=issuer, audience=audience)


def verify_hs384(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS384", issuer=issuer, audience=audience)


def verify_hs512(token: str, secret: str | bytes, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_hmac(token, secret, "HS512", issuer=issuer, audience=audience)


# ── ECDSA signing ─────────────────────────────────────────────────────────────


# ── ECDSA signing ─────────────────────────────────────────────────────────────


def _sign_ec(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_ec(token: str, public_key: ec.EllipticCurvePublicKey, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, public_key, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def sign_es256(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES256", expires_in=expires_in)


def sign_es384(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES384", expires_in=expires_in)


def sign_es512(payload: dict[str, Any], private_key: ec.EllipticCurvePrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ec(payload, private_key, "ES512", expires_in=expires_in)


def verify_es256(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES256", issuer=issuer, audience=audience)


def verify_es384(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES384", issuer=issuer, audience=audience)


def verify_es512(token: str, public_key: ec.EllipticCurvePublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ec(token, public_key, "ES512", issuer=issuer, audience=audience)


# ── RSA-PSS signing ───────────────────────────────────────────────────────────


# ── RSA-PSS signing ───────────────────────────────────────────────────────────


def _sign_ps(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, alg: str, *, expires_in: int | timedelta | None = None, headers: dict[str, Any] | None = None) -> str:
    claims = dict(payload)
    if expires_in is not None:
        delta = expires_in if isinstance(expires_in, timedelta) else timedelta(seconds=expires_in)
        claims["exp"] = datetime.now(timezone.utc) + delta
    try:
        return jwt.encode(claims, private_key, algorithm=alg, headers=headers)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.sign_failed") from exc


def _verify_ps(token: str, public_key: rsa.RSAPublicKey, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, public_key, algorithms=[alg], issuer=issuer, audience=audience)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.verify_failed") from exc
    if not isinstance(payload, dict):
        raise CryptoError("JWT payload is not an object", code="jwt.invalid_payload")
    return payload


def sign_ps256(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS256", expires_in=expires_in)


def sign_ps384(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS384", expires_in=expires_in)


def sign_ps512(payload: dict[str, Any], private_key: rsa.RSAPrivateKey, *, expires_in: int | timedelta | None = None) -> str:
    return _sign_ps(payload, private_key, "PS512", expires_in=expires_in)


def verify_ps256(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS256", issuer=issuer, audience=audience)


def verify_ps384(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS384", issuer=issuer, audience=audience)


def verify_ps512(token: str, public_key: rsa.RSAPublicKey, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    return _verify_ps(token, public_key, "PS512", issuer=issuer, audience=audience)


# ── JWT object parsing ────────────────────────────────────────────────────────


def parse_jwt(token: str) -> dict[str, Any]:
    """Parse a JWT without verifying the signature."""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.decode_failed") from exc


def new_jwt(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new JWT claims object from a payload dict."""
    return dict(payload)


def jwt_of(token: str) -> dict[str, Any]:
    """Parse a JWT and return the claims object (alias for parse_jwt)."""
    return parse_jwt(token)


def _get_header(token: str) -> dict[str, Any]:
    try:
        return jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise CryptoError(str(exc), code="jwt.decode_failed") from exc


# ── Strict verification ───────────────────────────────────────────────────────


def verify_strict(token: str, secret: str | bytes, alg: str, *, issuer: str | None = None, audience: str | None = None) -> dict[str, Any]:
    """Verify a JWT strictly without algorithm fallback.

    The token's ``alg`` header must match ``alg``.
    """
    header = _get_header(token)
    if header.get("alg", "").upper() != alg.upper():
        raise CryptoError(
            f"algorithm mismatch: expected {alg}, got {header.get('alg')}",
            code="jwt.algorithm_mismatch",
        )
    return _verify_hmac(token, secret, alg, issuer=issuer, audience=audience)


def validate_algorithm(token: str, expected_alg: str) -> bool:
    """Check if the token's ``alg`` header matches the expected algorithm."""
    try:
        header = _get_header(token)
    except CryptoError:
        return False
    return header.get("alg", "").upper() == expected_alg.upper()


# ── Date validation ───────────────────────────────────────────────────────────


def validate_jwt_date(token: str, *, leeway: int = 0) -> bool:
    """Validate ``nbf``, ``exp``, and ``iat`` claims in a JWT.

    ``leeway`` is the acceptable clock skew in seconds.
    """
    try:
        claims = parse_jwt(token)
    except CryptoError:
        return False
    return validate_date(claims, leeway=leeway)


def validate_date(claims: dict[str, Any], *, leeway: int = 0) -> bool:
    """Validate ``nbf``, ``exp``, and ``iat`` claims in a claims dict.

    ``leeway`` is the acceptable clock skew in seconds.
    """
    now = datetime.now(timezone.utc)
    delta = timedelta(seconds=leeway)
    nbf = claims.get("nbf")
    if nbf is not None:
        nbf_time = datetime.fromtimestamp(nbf, tz=timezone.utc)
        if now < nbf_time - delta:
            return False
    exp = claims.get("exp")
    if exp is not None:
        exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        if now > exp_time + delta:
            return False
    iat = claims.get("iat")
    if iat is not None:
        iat_time = datetime.fromtimestamp(iat, tz=timezone.utc)
        if now < iat_time - delta:
            return False
    return True


# ── Signer constructor ────────────────────────────────────────────────────────


def create_signer(algorithm_id: str) -> str:
    """Convert a JWT algorithm ID (e.g. ``HS256``) to a signer name."""
    if not algorithm_id:
        raise CryptoError("empty algorithm ID", code="jwt.invalid_algorithm")
    return algorithm_name(algorithm_id)


# ── key generation ──────────────────────────────────────────────────────────


def generate_ec_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


def generate_rsa_key(bits: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


# ── JWT Builder ───────────────────────────────────────────────────────────────


class JWTBuilder:
    """Fluent JWT token builder and validator.

    Usage::

        token = JWTBuilder().set_subject("user1").set_issuer("myapp").sign_hs256(secret)
        claims = JWTBuilder().require_issuer("myapp").verify_hs256(token, secret)
    """

    def __init__(self) -> None:
        self._claims: dict[str, Any] = {}
        self._expires_in: int | timedelta | None = None
        self._issuer: str | None = None
        self._audience: str | None = None
        self._headers: dict[str, Any] | None = None

    def set_subject(self, sub: str) -> JWTBuilder:
        self._claims["sub"] = sub
        return self

    def set_issuer(self, iss: str) -> JWTBuilder:
        self._claims["iss"] = iss
        return self

    def set_audience(self, aud: str) -> JWTBuilder:
        self._claims["aud"] = aud
        return self

    def set_jwt_id(self, jti: str) -> JWTBuilder:
        self._claims["jti"] = jti
        return self

    def set_expires_in(self, expires_in: int | timedelta) -> JWTBuilder:
        self._expires_in = expires_in
        return self

    def set_claim(self, key: str, value: Any) -> JWTBuilder:
        self._claims[key] = value
        return self

    def set_claims(self, claims: dict[str, Any]) -> JWTBuilder:
        self._claims.update(claims)
        return self

    def set_headers(self, headers: dict[str, Any]) -> JWTBuilder:
        self._headers = headers
        return self

    def require_issuer(self, iss: str) -> JWTBuilder:
        self._issuer = iss
        return self

    def require_audience(self, aud: str) -> JWTBuilder:
        self._audience = aud
        return self

    def sign_hs256(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS256", expires_in=self._expires_in, headers=self._headers)

    def sign_hs384(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS384", expires_in=self._expires_in, headers=self._headers)

    def sign_hs512(self, secret: str | bytes) -> str:
        return _sign_hmac(self._claims, secret, "HS512", expires_in=self._expires_in, headers=self._headers)

    def sign_es256(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES256", expires_in=self._expires_in, headers=self._headers)

    def sign_es384(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES384", expires_in=self._expires_in, headers=self._headers)

    def sign_es512(self, private_key: ec.EllipticCurvePrivateKey) -> str:
        return _sign_ec(self._claims, private_key, "ES512", expires_in=self._expires_in, headers=self._headers)

    def sign_ps256(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS256", expires_in=self._expires_in, headers=self._headers)

    def sign_ps384(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS384", expires_in=self._expires_in, headers=self._headers)

    def sign_ps512(self, private_key: rsa.RSAPrivateKey) -> str:
        return _sign_ps(self._claims, private_key, "PS512", expires_in=self._expires_in, headers=self._headers)

    def verify_hs256(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs256(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_hs384(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs384(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_hs512(self, token: str, secret: str | bytes) -> dict[str, Any]:
        return verify_hs512(token, secret, issuer=self._issuer, audience=self._audience)

    def verify_es256(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es256(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_es384(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es384(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_es512(self, token: str, public_key: ec.EllipticCurvePublicKey) -> dict[str, Any]:
        return verify_es512(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps256(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps256(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps384(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps384(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_ps512(self, token: str, public_key: rsa.RSAPublicKey) -> dict[str, Any]:
        return verify_ps512(token, public_key, issuer=self._issuer, audience=self._audience)

    def verify_strict(self, token: str, secret: str | bytes, alg: str) -> dict[str, Any]:
        return verify_strict(token, secret, alg, issuer=self._issuer, audience=self._audience)

    def parse_unverified(self, token: str) -> dict[str, Any]:
        """Decode a JWT without verifying the signature."""
        return parse_jwt(token)


def new_jwt_builder() -> JWTBuilder:
    return JWTBuilder()


# ── Go-compat generic token creation ─────────────────────────────────────────


def create_token(payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token from payload and HMAC key (Go compat)."""
    return sign_hs256(payload, key)


def create_jwt_token(payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token from payload and HMAC key (Go compat alias)."""
    return sign_hs256(payload, key)


def create_token_with_headers(headers: dict[str, Any], payload: dict[str, Any], key: str | bytes) -> str:
    """Create an HS256 token with custom headers (Go compat)."""
    return _sign_hmac(payload, key, "HS256", headers=headers)


def create_token_with_algorithm(payload: dict[str, Any], key: str | bytes, algorithm: str) -> str:
    """Create a token with an explicit HMAC algorithm (Go compat)."""
    return _sign_hmac(payload, key, algorithm)


def create_token_with_headers_and_algorithm(
    headers: dict[str, Any], payload: dict[str, Any], key: str | bytes, algorithm: str
) -> str:
    """Create a token with custom headers and HMAC algorithm (Go compat)."""
    return _sign_hmac(payload, key, algorithm, headers=headers)


# ── Go-compat generic verification ───────────────────────────────────────────


def verify(token: str, key: str | bytes) -> bool:
    """Verify a JWT with an HMAC key using the token's header algorithm (Go compat)."""
    try:
        header = _get_header(token)
        alg = header.get("alg", "HS256")
        match alg.upper():
            case "HS256":
                _verify_hmac(token, key, "HS256")
            case "HS384":
                _verify_hmac(token, key, "HS384")
            case "HS512":
                _verify_hmac(token, key, "HS512")
            case _:
                _verify_hmac(token, key, "HS256")
        return True
    except CryptoError:
        return False


def verify_jwt(token: str, key: str | bytes) -> bool:
    """Verify a JWT with an HMAC key (Go compat alias)."""
    return verify(token, key)


def of_validator(token: str) -> dict[str, Any]:
    """Parse a token and return claims for validation (Go compat)."""
    return parse_jwt(token)


# ── JWTSigner abstraction ────────────────────────────────────────────────────


class JWTSigner:
    """A JWT signer that can sign and verify tokens using a specific algorithm.

    This is the Python equivalent of Go's ``JWTSigner`` interface.
    Concrete signers are created via the ``HS256()``, ``HS384()``, ``HS512()``,
    ``PS256()``, ``PS384()``, ``PS512()``, ``ES256()``, ``ES384()``, ``ES512()``
    factory functions, or via ``new_hmac_signer()``, ``new_rsa_pss_signer()``,
    ``new_ecdsa_signer()`` with an explicit algorithm string.
    """

    def __init__(self, algorithm: str, sign_fn: Callable, verify_fn: Callable) -> None:
        self._algorithm = algorithm
        self._sign = sign_fn
        self._verify = verify_fn

    def algorithm(self) -> str:
        """Return the JWT algorithm ID (e.g. ``HS256``)."""
        return self._algorithm

    def sign(self, header_b64: str, payload_b64: str) -> str:
        """Sign the ``header_b64.payload_b64`` pair and return the base64-url signature."""
        return self._sign(header_b64, payload_b64)

    def verify(self, header_b64: str, payload_b64: str, sig_b64: str) -> bool:
        """Verify that ``sig_b64`` is a valid signature for ``header_b64.payload_b64``."""
        return self._verify(header_b64, payload_b64, sig_b64)


# ── HMAC signer ──────────────────────────────────────────────────────────────


def _hmac_sign(key: bytes, hash_name: str) -> Callable:
    def sign(header_b64: str, payload_b64: str) -> str:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = _hmac.new(key, message, hash_name).digest()
        return base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")

    return sign


def _hmac_verify(key: bytes, hash_name: str) -> Callable:
    def verify(header_b64: str, payload_b64: str, sig_b64: str) -> bool:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = _hmac.new(key, message, hash_name).digest()
        sig = base64.urlsafe_b64decode(sig_b64 + "==")
        return _hmac.compare_digest(expected, sig)

    return verify


def new_hmac_signer(algorithm: str, key: bytes) -> JWTSigner:
    """Create an HMAC signer for HS256, HS384, or HS512.

    Returns (signer, None) on success, or (None, error) on bad algorithm.
    """
    if not isinstance(key, bytes):
        key = key.encode("utf-8") if isinstance(key, str) else key
    hash_map = {"HS256": "sha256", "HS384": "sha384", "HS512": "sha512"}
    if algorithm.upper() not in hash_map:
        raise CryptoError(f"unsupported HMAC algorithm: {algorithm}", code="jwt.unsupported_algorithm")
    hash_name = hash_map[algorithm.upper()]
    return JWTSigner(algorithm.upper(), _hmac_sign(key, hash_name), _hmac_verify(key, hash_name))


def new_hmac_signer_strict(algorithm: str, key: bytes) -> JWTSigner:
    """Create an HMAC signer and enforce the recommended minimum key length."""
    min_bytes = min_hmac_key_bytes(algorithm)
    if len(key) < min_bytes:
        raise CryptoError(
            f"{algorithm} requires at least {min_bytes} bytes, got {len(key)}",
            code="jwt.weak_secret",
        )
    return new_hmac_signer(algorithm, key)


def must_hmac_signer(algorithm: str, key: bytes) -> JWTSigner:
    """Create an HMAC signer; raises on invalid algorithm."""
    return new_hmac_signer(algorithm, key)


def create_signer_from_key(algorithm_id: str, key: bytes) -> JWTSigner:
    """Create an HMAC signer from algorithm ID."""
    if algorithm_id.upper() == "NONE":
        raise CryptoError("none algorithm is rejected", code="jwt.unsupported_algorithm")
    return new_hmac_signer(algorithm_id, key)


def create_signer_from_key_strict(algorithm_id: str, key: bytes) -> JWTSigner:
    """Create an HMAC signer from algorithm ID with strict key length check."""
    if algorithm_id.upper() == "NONE":
        raise CryptoError("none algorithm is rejected", code="jwt.unsupported_algorithm")
    return new_hmac_signer_strict(algorithm_id, key)


# ── RSA-PSS signer ───────────────────────────────────────────────────────────


def _rsa_pss_sign(priv: rsa.RSAPrivateKey, hash_alg: str) -> Callable:
    hash_map = {"sha256": hashes.SHA256(), "sha384": hashes.SHA384(), "sha512": hashes.SHA512()}
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    def sign(header_b64: str, payload_b64: str) -> str:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = priv.sign(
            message,
            padding.PSS(mgf=padding.MGF1(chosen_hash), salt_length=padding.PSS.MAX_LENGTH),
            chosen_hash,
        )
        return base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")

    return sign


def _rsa_pss_verify(pub: rsa.RSAPublicKey, hash_alg: str) -> Callable:
    hash_map = {"sha256": hashes.SHA256(), "sha384": hashes.SHA384(), "sha512": hashes.SHA512()}
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    def verify(header_b64: str, payload_b64: str, sig_b64: str) -> bool:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        try:
            sig = base64.urlsafe_b64decode(sig_b64 + "==")
            pub.verify(
                sig,
                message,
                padding.PSS(mgf=padding.MGF1(chosen_hash), salt_length=padding.PSS.MAX_LENGTH),
                chosen_hash,
            )
            return True
        except Exception:
            return False

    return verify


def new_rsa_pss_signer(
    algorithm: str, priv: rsa.RSAPrivateKey, pub: rsa.RSAPublicKey
) -> JWTSigner:
    """Create an RSA-PSS signer for PS256, PS384, or PS512."""
    hash_map = {"PS256": "sha256", "PS384": "sha384", "PS512": "sha512"}
    if algorithm.upper() not in hash_map:
        raise CryptoError(f"unsupported RSA-PSS algorithm: {algorithm}", code="jwt.unsupported_algorithm")
    hash_name = hash_map[algorithm.upper()]
    return JWTSigner(algorithm.upper(), _rsa_pss_sign(priv, hash_name), _rsa_pss_verify(pub, hash_name))


# ── ECDSA signer ─────────────────────────────────────────────────────────────


def _ecdsa_sign(priv: ec.EllipticCurvePrivateKey, hash_alg: str) -> Callable:
    hash_map = {"sha256": hashes.SHA256(), "sha384": hashes.SHA384(), "sha512": hashes.SHA512()}
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    def sign(header_b64: str, payload_b64: str) -> str:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        sig_der = priv.sign(message, ec.ECDSA(chosen_hash))
        r, s = _decode_der_ecdsa(sig_der)
        sig_bytes = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode("ascii")

    return sign


def _ecdsa_verify(pub: ec.EllipticCurvePublicKey, hash_alg: str) -> Callable:
    hash_map = {"sha256": hashes.SHA256(), "sha384": hashes.SHA384(), "sha512": hashes.SHA512()}
    chosen_hash = hash_map.get(hash_alg, hashes.SHA256())

    def verify(header_b64: str, payload_b64: str, sig_b64: str) -> bool:
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        try:
            sig_bytes = base64.urlsafe_b64decode(sig_b64 + "==")
            r = int.from_bytes(sig_bytes[:32], "big")
            s = int.from_bytes(sig_bytes[32:], "big")
            sig_der = _encode_der_ecdsa(r, s)
            pub.verify(sig_der, message, ec.ECDSA(chosen_hash))
            return True
        except Exception:
            return False

    return verify


def _decode_der_ecdsa(sig_der: bytes) -> tuple[int, int]:
    """Decode a DER-encoded ECDSA signature into (r, s)."""
    if sig_der[0] != 0x30:
        raise ValueError("invalid DER signature")
    offset = 2
    if sig_der[offset] == 0x02:
        offset += 1
        r_len = sig_der[offset]
        offset += 1
        r = int.from_bytes(sig_der[offset : offset + r_len], "big")
        offset += r_len
    else:
        raise ValueError("expected r integer")
    if sig_der[offset] == 0x02:
        offset += 1
        s_len = sig_der[offset]
        offset += 1
        s = int.from_bytes(sig_der[offset : offset + s_len], "big")
    else:
        raise ValueError("expected s integer")
    return r, s


def _encode_der_ecdsa(r: int, s: int) -> bytes:
    """Encode (r, s) into a DER-encoded ECDSA signature."""
    r_bytes = r.to_bytes((r.bit_length() + 7) // 8, "big")
    s_bytes = s.to_bytes((s.bit_length() + 7) // 8, "big")
    if r_bytes[0] & 0x80:
        r_bytes = b"\x00" + r_bytes
    if s_bytes[0] & 0x80:
        s_bytes = b"\x00" + s_bytes
    inner = b"\x02" + bytes([len(r_bytes)]) + r_bytes + b"\x02" + bytes([len(s_bytes)]) + s_bytes
    return b"\x30" + bytes([len(inner)]) + inner


def new_ecdsa_signer(
    algorithm: str, priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey
) -> JWTSigner:
    """Create an ECDSA signer for ES256, ES384, or ES512."""
    hash_map = {"ES256": "sha256", "ES384": "sha384", "ES512": "sha512"}
    if algorithm.upper() not in hash_map:
        raise CryptoError(f"unsupported ECDSA algorithm: {algorithm}", code="jwt.unsupported_algorithm")
    hash_name = hash_map[algorithm.upper()]
    return JWTSigner(algorithm.upper(), _ecdsa_sign(priv, hash_name), _ecdsa_verify(pub, hash_name))


# ── Go-compat signer constructors ────────────────────────────────────────────


def HS256(key: bytes) -> JWTSigner:
    return new_hmac_signer("HS256", key)


def HS384(key: bytes) -> JWTSigner:
    return new_hmac_signer("HS384", key)


def HS512(key: bytes) -> JWTSigner:
    return new_hmac_signer("HS512", key)


def PS256(priv: rsa.RSAPrivateKey, pub: rsa.RSAPublicKey) -> JWTSigner:
    return new_rsa_pss_signer("PS256", priv, pub)


def PS384(priv: rsa.RSAPrivateKey, pub: rsa.RSAPublicKey) -> JWTSigner:
    return new_rsa_pss_signer("PS384", priv, pub)


def PS512(priv: rsa.RSAPrivateKey, pub: rsa.RSAPublicKey) -> JWTSigner:
    return new_rsa_pss_signer("PS512", priv, pub)


def ES256(priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey) -> JWTSigner:
    return new_ecdsa_signer("ES256", priv, pub)


def ES384(priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey) -> JWTSigner:
    return new_ecdsa_signer("ES384", priv, pub)


def ES512(priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey) -> JWTSigner:
    return new_ecdsa_signer("ES512", priv, pub)


# ── Go-compat JWT signer wrapper functions ───────────────────────────────────


def jwtsigner_hmac(algorithm: str, key: bytes) -> JWTSigner:
    return new_hmac_signer(algorithm, key)


def jwtsigner_hs256(key: bytes) -> JWTSigner:
    return HS256(key)


def jwtsigner_ecdsa(
    algorithm: str, priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey
) -> JWTSigner:
    return new_ecdsa_signer(algorithm, priv, pub)


def jwtsigner_es256(priv: ec.EllipticCurvePrivateKey, pub: ec.EllipticCurvePublicKey) -> JWTSigner:
    return ES256(priv, pub)


# ── Go-compat CreateToken/Verify with signer ─────────────────────────────────


def create_token_with_signer(payload: dict[str, Any], signer: JWTSigner) -> str:
    """Create a JWT token using a JWTSigner (Go compat)."""
    import jwt as _jwt_module

    header = {"alg": signer.algorithm(), "typ": "JWT"}
    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("ascii"))
        .rstrip(b"=")
        .decode("ascii")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("ascii"))
        .rstrip(b"=")
        .decode("ascii")
    )
    sig_b64 = signer.sign(header_b64, payload_b64)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def create_token_with_headers_and_signer(
    headers: dict[str, Any], payload: dict[str, Any], signer: JWTSigner
) -> str:
    """Create a JWT token with custom headers and a JWTSigner (Go compat)."""
    header = dict(headers)
    header.setdefault("alg", signer.algorithm())
    header.setdefault("typ", "JWT")
    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("ascii"))
        .rstrip(b"=")
        .decode("ascii")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("ascii"))
        .rstrip(b"=")
        .decode("ascii")
    )
    sig_b64 = signer.sign(header_b64, payload_b64)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def create_jwt_token_with_signer(payload: dict[str, Any], signer: JWTSigner) -> str:
    """Create a JWT token using a JWTSigner (Go compat)."""
    return create_token_with_signer(payload, signer)


def verify_with_signer(token: str, signer: JWTSigner) -> bool:
    """Verify a JWT token using a JWTSigner (Go compat)."""
    parts = token.split(".")
    if len(parts) != 3:
        return False
    return signer.verify(parts[0], parts[1], parts[2])


def verify_jwt_with_signer(token: str, signer: JWTSigner) -> bool:
    """Verify a JWT token using a JWTSigner (Go compat alias)."""
    return verify_with_signer(token, signer)


def verify_strict_signer(token: str, signer: JWTSigner) -> bool:
    """Verify a JWT token using a JWTSigner, requiring algorithm match in header (Go compat)."""
    parts = token.split(".")
    if len(parts) != 3:
        return False
    try:
        header_json = base64.urlsafe_b64decode(parts[0] + "==").decode("ascii")
        header = json.loads(header_json)
        if header.get("alg", "").upper() != signer.algorithm().upper():
            return False
    except Exception:
        return False
    return signer.verify(parts[0], parts[1], parts[2])


def validate_algorithm_with_signer(token: str, signer: JWTSigner) -> None:
    """Check whether the token's alg header matches the signer (Go compat)."""
    parts = token.split(".")
    if len(parts) != 3:
        raise CryptoError("invalid token format", code="jwt.invalid_token")
    try:
        header_json = base64.urlsafe_b64decode(parts[0] + "==").decode("ascii")
        header = json.loads(header_json)
    except Exception as exc:
        raise CryptoError("invalid token header", code="jwt.invalid_token") from exc
    if header.get("alg", "").upper() != signer.algorithm().upper():
        raise CryptoError(
            f"algorithm mismatch: expected {signer.algorithm()}, got {header.get('alg')}",
            code="jwt.algorithm_mismatch",
        )