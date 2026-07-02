from __future__ import annotations

import re
from urllib.parse import urlparse

from kniferpy.internal import identx, netx

_RX_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_RX_MOBILE = re.compile(r"^1[3-9]\d{9}$")
_RX_CHINESE = re.compile(r"^[\u2e80-\u2eff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+$")
_RX_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def is_email(s: str) -> bool:
    return _RX_EMAIL.match(s) is not None


def is_mobile(s: str) -> bool:
    return _RX_MOBILE.match(s) is not None


def is_url(s: str) -> bool:
    if s == "" or s.strip() != s:
        return False
    try:
        parsed = urlparse(s)
    except ValueError:
        return False
    return bool(parsed.scheme) and bool(parsed.netloc)


def is_ipv4(s: str) -> bool:
    return netx.is_ipv4(s)


def is_ipv6(s: str) -> bool:
    return netx.is_ipv6(s)


def is_id_card(s: str) -> bool:
    return identx.is_valid_id_card(s)


def is_chinese(s: str) -> bool:
    return s != "" and _RX_CHINESE.match(s) is not None


def is_number_str(s: str) -> bool:
    return _RX_NUMBER.match(s) is not None
