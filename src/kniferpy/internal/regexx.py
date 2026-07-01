from __future__ import annotations

import re
from collections.abc import Callable

_numbers_regex = re.compile(r"\d+")


def _try_compile(pattern: str) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern)
    except re.error:
        return None


def match(pattern: str, text: str) -> bool:
    compiled = _try_compile(pattern)
    return compiled is not None and compiled.search(text) is not None


def is_match(pattern: str, text: str) -> bool:
    compiled = _try_compile(pattern)
    return compiled is not None and compiled.fullmatch(text) is not None


def find(pattern: str, text: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    return found.group(0) if found else ""


def find_all(pattern: str, text: str) -> list[str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return []
    return [m.group(0) for m in compiled.finditer(text)]


def count(pattern: str, text: str) -> int:
    compiled = _try_compile(pattern)
    if compiled is None:
        return 0
    return sum(1 for _ in compiled.finditer(text))


def replace(pattern: str, text: str, replacement: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(lambda _: replacement, text)


def replace_first(pattern: str, text: str, replacement: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(lambda _: replacement, text, count=1)


def replace_func(pattern: str, text: str, repl: Callable[[re.Match[str]], str]) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(repl, text)


def delete_all(pattern: str, text: str) -> str:
    return replace(pattern, text, "")


def delete_first(pattern: str, text: str) -> str:
    return replace_first(pattern, text, "")


def get_group(pattern: str, text: str, group: int = 0) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    if found is None:
        return ""
    try:
        value = found.group(group)
    except IndexError:
        return ""
    return value or ""


def get_group_by_name(pattern: str, text: str, name: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    if found is None:
        return ""
    try:
        value = found.group(name)
    except IndexError:
        return ""
    return value or ""


def find_all_group(pattern: str, text: str, group: int = 1) -> list[str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return []
    result: list[str] = []
    for match_obj in compiled.finditer(text):
        try:
            value = match_obj.group(group)
        except IndexError:
            continue
        if value is not None:
            result.append(value)
    return result


def named_groups(pattern: str, text: str) -> dict[str, str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return {}
    found = compiled.search(text)
    if found is None:
        return {}
    return {key: value or "" for key, value in found.groupdict().items()}


def get_first_number(text: str) -> int | None:
    found = _numbers_regex.search(text)
    if found is None:
        return None
    return int(found.group(0))


def escape(text: str) -> str:
    return re.escape(text)
