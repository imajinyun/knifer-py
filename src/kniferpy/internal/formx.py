from __future__ import annotations

import re
from typing import Callable
from urllib.parse import urlparse

from kniferpy.internal import identx, netx

_RX_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_RX_MOBILE = re.compile(r"^1[3-9]\d{9}$")
_RX_CHINESE = re.compile(r"^[\u2e80-\u2eff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+$")
_RX_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


class _ValidatorConfig:
    def __init__(self) -> None:
        self.email: Callable[[str], bool] = _RX_EMAIL.match
        self.mobile: Callable[[str], bool] = _RX_MOBILE.match
        self.id_card: Callable[[str], bool] = identx.is_valid_id_card
        self.chinese: Callable[[str], bool] = _RX_CHINESE.match
        self.number: Callable[[str], bool] = _RX_NUMBER.match


ValidatorOption = Callable[[_ValidatorConfig], None]


def with_email_matcher(matcher: Callable[[str], bool]) -> ValidatorOption:
    def _opt(c: _ValidatorConfig) -> None:
        c.email = matcher
    return _opt


def with_mobile_matcher(matcher: Callable[[str], bool]) -> ValidatorOption:
    def _opt(c: _ValidatorConfig) -> None:
        c.mobile = matcher
    return _opt


def with_id_card_matcher(matcher: Callable[[str], bool]) -> ValidatorOption:
    def _opt(c: _ValidatorConfig) -> None:
        c.id_card = matcher
    return _opt


def with_chinese_matcher(matcher: Callable[[str], bool]) -> ValidatorOption:
    def _opt(c: _ValidatorConfig) -> None:
        c.chinese = matcher
    return _opt


def with_number_matcher(matcher: Callable[[str], bool]) -> ValidatorOption:
    def _opt(c: _ValidatorConfig) -> None:
        c.number = matcher
    return _opt


def _apply_options(opts: list[ValidatorOption]) -> _ValidatorConfig:
    cfg = _ValidatorConfig()
    for opt in opts:
        opt(cfg)
    return cfg


def _call_matcher(matcher: Callable[[str], bool], s: str) -> bool:
    result = matcher(s)
    return bool(result)


def is_email(s: str) -> bool:
    return is_email_with_options(s)


def is_email_with_options(s: str, *opts: ValidatorOption) -> bool:
    return _call_matcher(_apply_options(list(opts)).email, s)


def is_mobile(s: str) -> bool:
    return is_mobile_with_options(s)


def is_mobile_with_options(s: str, *opts: ValidatorOption) -> bool:
    return _call_matcher(_apply_options(list(opts)).mobile, s)


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
    return is_id_card_with_options(s)


def is_id_card_with_options(s: str, *opts: ValidatorOption) -> bool:
    return _call_matcher(_apply_options(list(opts)).id_card, s)


def is_chinese(s: str) -> bool:
    return is_chinese_with_options(s)


def is_chinese_with_options(s: str, *opts: ValidatorOption) -> bool:
    return s != "" and _call_matcher(_apply_options(list(opts)).chinese, s)


def is_number_str(s: str) -> bool:
    return is_number_str_with_options(s)


def is_number_str_with_options(s: str, *opts: ValidatorOption) -> bool:
    return _call_matcher(_apply_options(list(opts)).number, s)
