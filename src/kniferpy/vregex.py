from __future__ import annotations

import re
from collections.abc import Callable

from kniferpy.internal import regexx


def match(pattern: str, text: str) -> bool:
    return regexx.match(pattern, text)


def is_match(pattern: str, text: str) -> bool:
    return regexx.is_match(pattern, text)


def find(pattern: str, text: str) -> str:
    return regexx.find(pattern, text)


def find_all(pattern: str, text: str) -> list[str]:
    return regexx.find_all(pattern, text)


def count(pattern: str, text: str) -> int:
    return regexx.count(pattern, text)


def replace(pattern: str, text: str, replacement: str) -> str:
    return regexx.replace(pattern, text, replacement)


def replace_first(pattern: str, text: str, replacement: str) -> str:
    return regexx.replace_first(pattern, text, replacement)


def replace_func(pattern: str, text: str, repl: Callable[[re.Match[str]], str]) -> str:
    return regexx.replace_func(pattern, text, repl)


def delete_all(pattern: str, text: str) -> str:
    return regexx.delete_all(pattern, text)


def delete_first(pattern: str, text: str) -> str:
    return regexx.delete_first(pattern, text)


def get_group(pattern: str, text: str, group: int = 0) -> str:
    return regexx.get_group(pattern, text, group)


def get_group_by_name(pattern: str, text: str, name: str) -> str:
    return regexx.get_group_by_name(pattern, text, name)


def find_all_group(pattern: str, text: str, group: int = 1) -> list[str]:
    return regexx.find_all_group(pattern, text, group)


def named_groups(pattern: str, text: str) -> dict[str, str]:
    return regexx.named_groups(pattern, text)


def get_first_number(text: str) -> int | None:
    return regexx.get_first_number(text)


def escape(text: str) -> str:
    return regexx.escape(text)
