from pathlib import Path

import pytest

from kniferpy import vcrypto


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