from __future__ import annotations

from kniferpy.internal import maskx


def hide(value: str, start: int, end: int) -> str:
    return maskx.hide(value, start, end)


def first_mask(value: str) -> str:
    return maskx.first_mask(value)


def chinese_name(full_name: str) -> str:
    return maskx.chinese_name(full_name)


def id_card(value: str, front: int = 6, end: int = 4) -> str:
    return maskx.id_card(value, front, end)


def fixed_phone(value: str) -> str:
    return maskx.fixed_phone(value)


def mobile_phone(value: str) -> str:
    return maskx.mobile_phone(value)


def address(value: str, sensitive_size: int) -> str:
    return maskx.address(value, sensitive_size)


def email(value: str) -> str:
    return maskx.email(value)


def password(value: str) -> str:
    return maskx.password(value)


def car_license(value: str) -> str:
    return maskx.car_license(value)


def bank_card(value: str) -> str:
    return maskx.bank_card(value)


def ipv4(value: str) -> str:
    return maskx.ipv4(value)


def ipv6(value: str) -> str:
    return maskx.ipv6(value)


def passport(value: str) -> str:
    return maskx.passport(value)


def credit_code(value: str) -> str:
    return maskx.credit_code(value)


def clear() -> str:
    return maskx.clear()
