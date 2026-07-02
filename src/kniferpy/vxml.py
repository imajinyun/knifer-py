from __future__ import annotations

from typing import Any

from kniferpy.internal import xmlx

CONTENT_KEY = xmlx.CONTENT_KEY


def escape(s: str) -> str:
    return xmlx.escape(s)


def unescape(s: str) -> str:
    return xmlx.unescape(s)


def clean_invalid(xml_content: str) -> str:
    return xmlx.clean_invalid(xml_content)


def clean_comment(xml_content: str) -> str:
    return xmlx.clean_comment(xml_content)


def to_map(xml_str: str) -> dict[str, Any]:
    return xmlx.to_map(xml_str)


def is_valid(xml_str: str) -> bool:
    return xmlx.is_valid(xml_str)
