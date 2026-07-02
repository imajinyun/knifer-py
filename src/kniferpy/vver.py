from __future__ import annotations

from collections.abc import Sequence

from kniferpy.internal import verx
from kniferpy.internal.verx import DEFAULT_VERSIONS_DELIMITER

__all__ = [
    "DEFAULT_VERSIONS_DELIMITER",
    "compare_version",
    "any_match",
    "any_match_slice",
    "is_greater_than",
    "is_greater_than_or_equal",
    "is_less_than",
    "is_less_than_or_equal",
    "match_el",
    "match_el_with_delimiter",
]


def compare_version(version1: str, version2: str) -> int:
    return verx.compare_version(version1, version2)


def any_match(current_version: str, *compare_versions: str) -> bool:
    return verx.any_match(current_version, *compare_versions)


def any_match_slice(current_version: str, compare_versions: Sequence[str]) -> bool:
    return verx.any_match_slice(current_version, compare_versions)


def is_greater_than(current_version: str, compare_version_str: str) -> bool:
    return verx.is_greater_than(current_version, compare_version_str)


def is_greater_than_or_equal(current_version: str, compare_version_str: str) -> bool:
    return verx.is_greater_than_or_equal(current_version, compare_version_str)


def is_less_than(current_version: str, compare_version_str: str) -> bool:
    return verx.is_less_than(current_version, compare_version_str)


def is_less_than_or_equal(current_version: str, compare_version_str: str) -> bool:
    return verx.is_less_than_or_equal(current_version, compare_version_str)


def match_el(current_version: str, version_el: str) -> bool:
    return verx.match_el(current_version, version_el)


def match_el_with_delimiter(
    current_version: str, version_el: str, delimiter: str
) -> bool:
    return verx.match_el_with_delimiter(current_version, version_el, delimiter)
