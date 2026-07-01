from __future__ import annotations

from kniferpy.internal import strx


def is_empty(value: str | None) -> bool:
    return strx.is_empty(value)


def is_not_empty(value: str | None) -> bool:
    return not is_empty(value)


def is_blank(value: str | None) -> bool:
    return strx.is_blank(value)


def is_not_blank(value: str | None) -> bool:
    return not is_blank(value)


def trim(value: str | None) -> str:
    return strx.trim(value)


def sub_before(value: str, separator: str, *, last: bool = False) -> str:
    return strx.sub_before(value, separator, last=last)


def sub_after(value: str, separator: str, *, last: bool = False) -> str:
    return strx.sub_after(value, separator, last=last)


def split_trim(value: str, separator: str) -> list[str]:
    return strx.split_trim(value, separator)


def contains_any(value: str, *items: str) -> bool:
    return strx.contains_any(value, *items)


def contains_all(value: str, *items: str) -> bool:
    return strx.contains_all(value, *items)


def contains_ignore_case(value: str, item: str) -> bool:
    return strx.contains_ignore_case(value, item)


def equals_ignore_case(left: str, right: str) -> bool:
    return strx.equals_ignore_case(left, right)


def reverse(value: str) -> str:
    return strx.reverse(value)


def add_prefix_if_not(value: str, prefix: str) -> str:
    return strx.add_prefix_if_not(value, prefix)


def add_suffix_if_not(value: str, suffix: str) -> str:
    return strx.add_suffix_if_not(value, suffix)


def default_if_empty(value: str | None, default: str) -> str:
    return strx.default_if_empty(value, default)


def default_if_blank(value: str | None, default: str) -> str:
    return strx.default_if_blank(value, default)


def escape_html(value: str) -> str:
    return strx.escape_html(value)


def unescape_html(value: str) -> str:
    return strx.unescape_html(value)


def to_snake_case(value: str) -> str:
    return strx.to_snake_case(value)


def to_kebab_case(value: str) -> str:
    return strx.to_kebab_case(value)


def to_pascal_case(value: str) -> str:
    return strx.to_pascal_case(value)
