from __future__ import annotations

import html
import re


def is_empty(value: str | None) -> bool:
    return value is None or value == ""


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def trim(value: str | None) -> str:
    return "" if value is None else value.strip()


def sub_before(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return value
    index = value.rfind(separator) if last else value.find(separator)
    return value if index < 0 else value[:index]


def sub_after(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return ""
    index = value.rfind(separator) if last else value.find(separator)
    return "" if index < 0 else value[index + len(separator) :]


def split_trim(value: str, separator: str) -> list[str]:
    return [part.strip() for part in value.split(separator) if part.strip()]


def contains_any(value: str, *items: str) -> bool:
    return any(item in value for item in items)


def contains_all(value: str, *items: str) -> bool:
    return all(item in value for item in items)


def contains_ignore_case(value: str, item: str) -> bool:
    return item.casefold() in value.casefold()


def equals_ignore_case(left: str, right: str) -> bool:
    return left.casefold() == right.casefold()


def reverse(value: str) -> str:
    return value[::-1]


def add_prefix_if_not(value: str, prefix: str) -> str:
    return value if value.startswith(prefix) else f"{prefix}{value}"


def add_suffix_if_not(value: str, suffix: str) -> str:
    return value if value.endswith(suffix) else f"{value}{suffix}"


def default_if_empty(value: str | None, default: str) -> str:
    return default if value is None or value == "" else value


def default_if_blank(value: str | None, default: str) -> str:
    return default if value is None or value.strip() == "" else value


def escape_html(value: str) -> str:
    return html.escape(value)


def unescape_html(value: str) -> str:
    return html.unescape(value)


def to_snake_case(value: str) -> str:
    normalized = re.sub(r"[\s\-]+", "_", value.strip())
    normalized = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", normalized)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    return normalized.lower().strip("_")


def to_kebab_case(value: str) -> str:
    return to_snake_case(value).replace("_", "-")


def to_pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[\s_\-]+", value.strip()) if part)
