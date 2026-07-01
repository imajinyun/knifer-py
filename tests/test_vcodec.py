import binascii

import pytest

from kniferpy import vcodec


def test_base64_helpers() -> None:
    encoded = vcodec.base64_encode_str("kniferpy")

    assert encoded == "a25pZmVycHk="
    assert vcodec.base64_decode_str(encoded) == "kniferpy"
    assert vcodec.base64_url_decode(vcodec.base64_url_encode(b"a?b")) == b"a?b"


def test_hex_helpers() -> None:
    encoded = vcodec.hex_encode_str("kniferpy")

    assert encoded == "6b6e696665727079"
    assert vcodec.hex_decode_str(encoded) == "kniferpy"


def test_rot13() -> None:
    assert vcodec.rot13("uryyb") == "hello"


def test_base64_decode_rejects_invalid_input() -> None:
    with pytest.raises(binascii.Error):
        vcodec.base64_decode("not base64")
