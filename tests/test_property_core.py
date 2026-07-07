from __future__ import annotations

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from kniferpy import vcodec, vstr


@settings(max_examples=100)
@given(st.binary())
def test_base64_round_trip(data: bytes) -> None:
    assert vcodec.base64_decode(vcodec.base64_encode(data)) == data


@settings(max_examples=100)
@given(st.binary())
def test_hex_round_trip(data: bytes) -> None:
    assert vcodec.hex_decode(vcodec.hex_encode(data)) == data


@settings(max_examples=100)
@given(st.binary())
def test_base58_round_trip(data: bytes) -> None:
    assert vcodec.base58_decode(vcodec.base58_encode(data)) == data


@settings(max_examples=100)
@given(st.binary())
def test_base62_round_trip(data: bytes) -> None:
    assert vcodec.base62_decode(vcodec.base62_encode(data)) == data


@settings(max_examples=100)
@given(st.text())
def test_reverse_is_involution(value: str) -> None:
    assert vstr.reverse(vstr.reverse(value)) == value


@settings(max_examples=100)
@given(st.text())
def test_html_escape_unescape_round_trip(value: str) -> None:
    assert vstr.unescape_html(vstr.escape_html(value)) == value


@settings(max_examples=100)
@given(st.text(alphabet=st.characters(blacklist_characters="/"), max_size=50))
def test_sub_before_after_recompose(value: str) -> None:
    left = vstr.sub_before(value + "/tail", "/")
    right = vstr.sub_after(value + "/tail", "/")
    assert f"{left}/{right}" == value + "/tail"


@settings(max_examples=100)
@given(st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), max_size=100))
def test_rotn_round_trip_for_letters(value: str) -> None:
    assert vcodec.rotn(vcodec.rotn(value, 7), -7) == value


@settings(max_examples=100)
@given(st.text(alphabet=st.characters(blacklist_categories=["Cs"]), max_size=50))
def test_unicode_escape_round_trip(value: str) -> None:
    escaped = vstr.escape_unicode(value)
    assert re.fullmatch(r"(?:[\x00-\x7F]|\\u[0-9A-F]{4})*", escaped)
    assert vstr.unescape_unicode(escaped) == value
