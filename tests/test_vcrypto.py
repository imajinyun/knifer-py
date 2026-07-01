from pathlib import Path

from kniferpy import vcrypto


def test_sha256_hex() -> None:
    assert (
        vcrypto.sha256_hex("kniferpy")
        == "983b8790345a90a374d0cc2d52d2a2175dc335542f8207d70726dd8daed95342"
    )


def test_hmac_sha256_hex() -> None:
    assert (
        vcrypto.hmac_sha256_hex("secret", "payload")
        == "b82fcb791acec57859b989b430a826488ce2e479fdf92326bd0a2e8375a42ba4"
    )


def test_sha1_and_md5_checksum_hex() -> None:
    assert vcrypto.sha1_hex("kniferpy") == "d55ede568f80b6dbbb02ac9e2853ff3f658d9ec9"
    assert vcrypto.md5_checksum_hex("kniferpy") == "ee248a454d8a92483ff2d4b5386de125"


def test_verify_hmac_sha256_hex() -> None:
    expected = vcrypto.hmac_sha256_hex("secret", "payload")

    assert vcrypto.verify_hmac_sha256_hex("secret", "payload", expected)
    assert not vcrypto.verify_hmac_sha256_hex("secret", "payload", "bad")


def test_verify_sha256_and_file_sha256(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("kniferpy", encoding="utf-8")
    expected = vcrypto.sha256_hex("kniferpy")

    assert vcrypto.verify_sha256_hex("kniferpy", expected)
    assert vcrypto.file_sha256_hex(path) == expected
    assert vcrypto.verify_file_sha256_hex(path, expected)


def test_pbkdf2_sha256_hex() -> None:
    derived = vcrypto.pbkdf2_sha256_hex("password", "salt", iterations=100_000, dklen=16)

    assert len(derived) == 32


def test_pbkdf2_rejects_low_iterations() -> None:
    try:
        vcrypto.pbkdf2_sha256_hex("password", "salt", iterations=10)
    except ValueError as err:
        assert str(err) == "iterations must be at least 100000"
    else:
        raise AssertionError("expected ValueError")
