from __future__ import annotations

import html
import re
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape as _sax_escape

from kniferpy.verr import DecodeError

# Entity constants (mirror knifer-go internal/xml).
NBSP = "&nbsp;"
AMP = "&amp;"
QUOTE = "&quot;"
APOS = "&apos;"
LT = "&lt;"
GT = "&gt;"

# Key holding element text when an element also carries attributes/children.
CONTENT_KEY = "content"

# XML 1.0 invalid control characters and comment matcher.
_INVALID_RE = re.compile("[\x00-\x08\x0b-\x0c\x0e-\x1f]")
_COMMENT_RE = re.compile(r"<!--.+?-->", re.DOTALL)

# DTD/entity declarations are rejected to avoid entity-expansion attacks.
_DOCTYPE_RE = re.compile(r"<!(?:DOCTYPE|ENTITY)", re.IGNORECASE)

_INT_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?")

_ESCAPE_ENTITIES = {'"': QUOTE, "'": APOS}


def escape(s: str) -> str:
    """Escape ``&``, ``<``, ``>``, ``"`` and ``'`` to XML entities."""
    return _sax_escape(s, _ESCAPE_ENTITIES)


def unescape(s: str) -> str:
    """Decode XML/HTML entities back into their characters."""
    return html.unescape(s)


def clean_invalid(xml_content: str) -> str:
    """Remove XML 1.0 invalid control characters."""
    return _INVALID_RE.sub("", xml_content)


def clean_comment(xml_content: str) -> str:
    """Remove XML comments."""
    return _COMMENT_RE.sub("", xml_content)


def to_map(xml_str: str) -> dict[str, Any]:
    """Parse XML into a nested dict; repeated sibling tags become lists."""
    root = _parse(xml_str)
    result: dict[str, Any] = {}
    _add_map_value(result, _local(root.tag), _element_to_value(root))
    return result


def is_valid(xml_str: str) -> bool:
    """Report whether ``xml_str`` is well-formed and DTD-free."""
    try:
        _parse(xml_str)
    except DecodeError:
        return False
    return True


def _parse(xml_str: str) -> ElementTree.Element:
    if _DOCTYPE_RE.search(xml_str):
        raise DecodeError("vxml: DTD/DOCTYPE is not allowed", code="xml.doctype_forbidden")
    try:
        return ElementTree.fromstring(xml_str)
    except ElementTree.ParseError as exc:
        raise DecodeError(f"vxml: parse error: {exc}", code="xml.invalid") from exc


def _local(tag: str) -> str:
    """Return the local name, dropping any ``{namespace}`` prefix."""
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _direct_text(elem: ElementTree.Element) -> str:
    """Concatenate character data directly under ``elem`` (not its descendants)."""
    parts = [elem.text or ""]
    parts.extend(child.tail or "" for child in elem)
    return "".join(parts)


def _element_to_value(elem: ElementTree.Element) -> Any:
    obj: dict[str, Any] = {}
    for key, value in elem.attrib.items():
        obj[_local(key)] = _parse_scalar(value)
    for child in elem:
        _add_map_value(obj, _local(child.tag), _element_to_value(child))
    text = _direct_text(elem).strip()
    if not obj:
        return "" if text == "" else _parse_scalar(text)
    if text != "":
        obj[CONTENT_KEY] = _parse_scalar(text)
    return obj


def _add_map_value(mapping: dict[str, Any], key: str, value: Any) -> None:
    if key in mapping:
        existing = mapping[key]
        if isinstance(existing, list):
            existing.append(value)
        else:
            mapping[key] = [existing, value]
        return
    mapping[key] = value


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    lowered = s.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if _INT_RE.fullmatch(s):
        return int(s)
    if _FLOAT_RE.fullmatch(s):
        return float(s)
    return s
