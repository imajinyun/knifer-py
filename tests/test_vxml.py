import pytest

from kniferpy import vxml
from kniferpy.verr import DecodeError


def test_escape_unescape_roundtrip() -> None:
    raw = '<tag attr="v">a & b \' c</tag>'
    escaped = vxml.escape(raw)
    assert "&lt;" in escaped
    assert "&amp;" in escaped
    assert "&quot;" in escaped
    assert "&apos;" in escaped
    assert vxml.unescape(escaped) == raw


def test_unescape_named_and_numeric_entities() -> None:
    assert vxml.unescape("a&nbsp;b") == "a\xa0b"
    assert vxml.unescape("&#65;&#x42;") == "AB"


def test_clean_invalid_removes_control_chars() -> None:
    dirty = "a\x00b\x08c\x0bd"
    assert vxml.clean_invalid(dirty) == "abcd"
    # Valid whitespace (tab/newline/carriage return) is preserved.
    assert vxml.clean_invalid("a\tb\nc\rd") == "a\tb\nc\rd"


def test_clean_comment_removes_comments() -> None:
    xml = "<r><!-- drop me --><a>1</a></r>"
    assert vxml.clean_comment(xml) == "<r><a>1</a></r>"
    assert vxml.clean_comment("<r><!-- multi\nline --><a/></r>") == "<r><a/></r>"


def test_to_map_scalars_and_nesting() -> None:
    xml = "<root><n>42</n><f>3.14</f><b>true</b><s>hello</s></root>"
    result = vxml.to_map(xml)
    assert result == {
        "root": {
            "n": 42,
            "f": 3.14,
            "b": True,
            "s": "hello",
        }
    }


def test_to_map_repeated_siblings_become_list() -> None:
    xml = "<root><item>1</item><item>2</item><item>3</item></root>"
    assert vxml.to_map(xml) == {"root": {"item": [1, 2, 3]}}


def test_to_map_attributes_and_mixed_content() -> None:
    xml = '<root id="7">text<child>x</child></root>'
    result = vxml.to_map(xml)
    assert result["root"]["id"] == 7
    assert result["root"]["child"] == "x"
    assert result["root"][vxml.CONTENT_KEY] == "text"


def test_to_map_empty_element() -> None:
    assert vxml.to_map("<root><empty/></root>") == {"root": {"empty": ""}}


def test_to_map_namespace_prefix_stripped() -> None:
    xml = '<root xmlns:ns="urn:x"><ns:child>v</ns:child></root>'
    assert vxml.to_map(xml) == {"root": {"child": "v"}}


def test_is_valid() -> None:
    assert vxml.is_valid("<root><a/></root>") is True
    assert vxml.is_valid("<root><a></root>") is False
    assert vxml.is_valid("not xml at all <") is False


def test_to_map_invalid_raises_decode_error() -> None:
    with pytest.raises(DecodeError):
        vxml.to_map("<root><unclosed></root>")


def test_doctype_is_rejected() -> None:
    payload = '<?xml version="1.0"?>' '<!DOCTYPE foo [<!ENTITY xxe "boom">]>' "<root>&xxe;</root>"
    assert vxml.is_valid(payload) is False
    with pytest.raises(DecodeError):
        vxml.to_map(payload)
