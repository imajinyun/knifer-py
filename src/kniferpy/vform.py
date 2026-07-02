from __future__ import annotations

from kniferpy.internal import formx

__all__ = [
    "is_email",
    "is_mobile",
    "is_url",
    "is_ipv4",
    "is_ipv6",
    "is_id_card",
    "is_chinese",
    "is_number_str",
]


def is_email(s: str) -> bool:
    return formx.is_email(s)


def is_mobile(s: str) -> bool:
    return formx.is_mobile(s)


def is_url(s: str) -> bool:
    return formx.is_url(s)


def is_ipv4(s: str) -> bool:
    return formx.is_ipv4(s)


def is_ipv6(s: str) -> bool:
    return formx.is_ipv6(s)


def is_id_card(s: str) -> bool:
    return formx.is_id_card(s)


def is_chinese(s: str) -> bool:
    return formx.is_chinese(s)


def is_number_str(s: str) -> bool:
    return formx.is_number_str(s)
