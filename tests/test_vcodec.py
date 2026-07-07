from __future__ import annotations

import base64

import pytest

from kniferpy import vcodec

# ── Base64 ───────────────────────────────────────────────────────────────────


class TestBase64:
    def test_encode(self) -> None:
        assert vcodec.base64_encode(b"knifer-go") == "a25pZmVyLWdv"

    def test_encode_str(self) -> None:
        assert vcodec.base64_encode_str("go") == "Z28="

    def test_encode_with_custom_callable_and_fallback(self) -> None:
        assert vcodec.base64_encode_with_encoding(b"go") == "Z28="
        assert vcodec.base64_encode_with_encoding(b"a/b", base64.urlsafe_b64encode) == "YS9i"
        assert vcodec.base64_encode_with_encoding(b"go", object()) == "Z28="

    def test_decode(self) -> None:
        assert vcodec.base64_decode("a25pZmVyLWdv") == b"knifer-go"

    def test_decode_with_custom_callable_path(self) -> None:
        assert vcodec.base64_decode_with_encoding("Z28=", lambda value: value) == b"go"

    def test_decode_str(self) -> None:
        assert vcodec.base64_decode_str("Z28=") == "go"

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base64_decode("not base64")

    def test_url_encode_decode(self) -> None:
        encoded = vcodec.base64_url_encode(b"a/b?c=d")
        assert encoded == "YS9iP2M9ZA=="
        assert vcodec.base64_url_decode(encoded) == b"a/b?c=d"

    def test_url_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base64_url_decode("invalid!")

    def test_raw_url_encode_decode(self) -> None:
        encoded = vcodec.base64_raw_url_encode(b"go?")
        assert encoded == "Z28_"
        assert vcodec.base64_raw_url_decode(encoded) == b"go?"

    def test_raw_url_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base64_raw_url_decode("!!!")


# ── Hex ──────────────────────────────────────────────────────────────────────


class TestHex:
    def test_encode(self) -> None:
        assert vcodec.hex_encode(b"\x47\x6f") == "476f"

    def test_encode_str(self) -> None:
        assert vcodec.hex_encode_str("go") == "676f"

    def test_decode(self) -> None:
        assert vcodec.hex_decode("476f") == b"Go"

    def test_decode_str(self) -> None:
        assert vcodec.hex_decode_str("676f") == "go"

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.hex_decode("xyz")


# ── Base32 ───────────────────────────────────────────────────────────────────


class TestBase32:
    def test_encode(self) -> None:
        assert vcodec.base32_encode(b"go") == "M5XQ===="

    def test_decode(self) -> None:
        assert vcodec.base32_decode("M5XQ====") == b"go"

    def test_encode_hex(self) -> None:
        assert vcodec.base32_encode_with_encoding(b"go", vcodec.BASE32_HEX_ENCODING) == "CTNG===="

    def test_encode_unknown_uses_standard(self) -> None:
        assert vcodec.base32_encode_with_encoding(b"go", "unknown") == "M5XQ===="

    def test_decode_hex(self) -> None:
        assert vcodec.base32_decode_with_encoding("CTNG====", vcodec.BASE32_HEX_ENCODING) == b"go"

    def test_decode_without_padding_and_unknown_encoding(self) -> None:
        assert vcodec.base32_decode("M5XQ") == b"go"
        assert vcodec.base32_decode_with_encoding("M5XQ", "unknown") == b"go"

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base32_decode("!!!")


# ── Base58 ───────────────────────────────────────────────────────────────────


class TestBase58:
    def test_encode(self) -> None:
        assert vcodec.base58_encode(b"hello world") == "StV1DL6CwTryKyV"
        assert vcodec.base58_encode(b"\x00\x00") == "11"
        assert vcodec.base58_encode(b"\x00hello") == "1Cn8eVZg"

    def test_decode(self) -> None:
        assert vcodec.base58_decode("StV1DL6CwTryKyV") == b"hello world"
        assert vcodec.base58_decode("11") == b"\x00\x00"
        assert vcodec.base58_decode("1Cn8eVZg") == b"\x00hello"

    def test_encode_flickr(self) -> None:
        assert (
            vcodec.base58_encode_with_alphabet(b"hello", vcodec.BASE58_FLICKR_ALPHABET) == "cM8DuyF"
        )

    def test_decode_flickr(self) -> None:
        assert (
            vcodec.base58_decode_with_alphabet("cM8DuyF", vcodec.BASE58_FLICKR_ALPHABET) == b"hello"
        )

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base58_decode("0")


# ── Base62 ───────────────────────────────────────────────────────────────────


class TestBase62:
    def test_encode(self) -> None:
        assert vcodec.base62_encode(b"hello") == "7tQLFHz"
        assert vcodec.base62_encode(b"\x00\x00") == "00"
        assert vcodec.base62_encode(b"\x00hello") == "07tQLFHz"

    def test_decode(self) -> None:
        assert vcodec.base62_decode("7tQLFHz") == b"hello"
        assert vcodec.base62_decode("00") == b"\x00\x00"
        assert vcodec.base62_decode("07tQLFHz") == b"\x00hello"

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.base62_decode("!!!")


# ── Morse ────────────────────────────────────────────────────────────────────


class TestMorse:
    def test_encode(self) -> None:
        assert vcodec.morse_encode("SOS 1") == "... --- ... / .----"

    def test_decode(self) -> None:
        assert vcodec.morse_decode("... --- ... / .----") == "SOS 1"

    def test_encode_single(self) -> None:
        assert vcodec.morse_encode("go") == "--. ---"

    def test_decode_empty(self) -> None:
        assert vcodec.morse_decode("") == ""

    def test_decode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.morse_decode("... invalid")

    def test_encode_invalid(self) -> None:
        with pytest.raises(ValueError):
            vcodec.morse_encode("\u20ac")


# ── ROT ──────────────────────────────────────────────────────────────────────


class TestROT:
    def test_rot13(self) -> None:
        assert vcodec.rot13("hello") == "uryyb"
        assert vcodec.rot13("uryyb") == "hello"

    def test_rot47(self) -> None:
        assert vcodec.rot47("Hello!") == "w6==@P"
        assert vcodec.rot47("w6==@P") == "Hello!"
        assert vcodec.rot47("世界") == "世界"

    def test_rotn(self) -> None:
        assert vcodec.rotn("abcXYZ", 2) == "cdeZAB"
        assert vcodec.rotn("abcXYZ", -2) == "yzaVWX"

    def test_rotn_large_shift(self) -> None:
        assert vcodec.rotn("a", 28) == "c"  # 28 % 26 = 2

    def test_rot47_and_rotn_keep_non_rotated_chars(self) -> None:
        assert vcodec.rot47("Hello 世界") == "w6==@ 世界"
        assert vcodec.rotn("abc-123", 2) == "cde-123"


# ── Legacy ───────────────────────────────────────────────────────────────────


class TestLegacy:
    def test_base64_helpers(self) -> None:
        encoded = vcodec.base64_encode_str("kniferpy")
        assert encoded == "a25pZmVycHk="
        assert vcodec.base64_decode_str(encoded) == "kniferpy"
        assert vcodec.base64_url_decode(vcodec.base64_url_encode(b"a?b")) == b"a?b"

    def test_hex_helpers(self) -> None:
        encoded = vcodec.hex_encode_str("kniferpy")
        assert encoded == "6b6e696665727079"
        assert vcodec.hex_decode_str(encoded) == "kniferpy"

    def test_rot13(self) -> None:
        assert vcodec.rot13("uryyb") == "hello"
