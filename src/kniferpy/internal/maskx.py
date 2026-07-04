from __future__ import annotations


def hide(value: str, start: int, end: int) -> str:
    runes = list(value)
    length = len(runes)
    if start < 0:
        start = 0
    if end > length:
        end = length
    if start > end:
        start = end
    for index in range(start, end):
        runes[index] = "*"
    return "".join(runes)


def first_mask(value: str) -> str:
    if value.strip() == "":
        return ""
    return hide(value, 1, len(value))


def chinese_name(full_name: str) -> str:
    return first_mask(full_name)


def id_card(value: str, front: int, end: int) -> str:
    if value.strip() == "":
        return ""
    length = len(value)
    if front < 0 or end < 0 or front + end > length:
        return ""
    return hide(value, front, length - end)


def fixed_phone(value: str) -> str:
    if value.strip() == "":
        return ""
    return hide(value, 4, len(value) - 2)


def mobile_phone(value: str) -> str:
    if value.strip() == "":
        return ""
    return hide(value, 3, len(value) - 4)


def address(value: str, sensitive_size: int) -> str:
    if value.strip() == "":
        return ""
    length = len(value)
    return hide(value, length - sensitive_size, length)


def email(value: str) -> str:
    if value.strip() == "":
        return ""
    index = value.find("@")
    if index <= 1:
        return value
    return hide(value, 1, index)


def password(value: str) -> str:
    if value.strip() == "":
        return ""
    return "*" * len(value)


def car_license(value: str) -> str:
    if value.strip() == "":
        return ""
    length = len(value)
    if length == 7:
        return hide(value, 3, 6)
    if length == 8:
        return hide(value, 3, 7)
    return value


def bank_card(value: str) -> str:
    if value.strip() == "":
        return value
    cleaned = "".join(ch for ch in value if not ch.isspace())
    length = len(cleaned)
    if length < 9:
        return cleaned
    end_length = length % 4 or 4
    mid_length = length - 4 - end_length
    parts = [cleaned[:4]]
    for index in range(mid_length):
        if index % 4 == 0:
            parts.append(" ")
        parts.append("*")
    parts.append(" ")
    parts.append(cleaned[length - end_length :])
    return "".join(parts)


def ipv4(value: str) -> str:
    index = value.find(".")
    if index >= 0:
        return value[:index] + ".*.*.*"
    return value + ".*.*.*"


def ipv6(value: str) -> str:
    index = value.find(":")
    if index >= 0:
        return value[:index] + ":*:*:*:*:*:*:*:*"
    return value + ":*:*:*:*:*:*:*:*"


def passport(value: str) -> str:
    if value.strip() == "":
        return value
    length = len(value)
    if length <= 2:
        return hide(value, 0, length)
    return hide(value, 2, length - 2)


def credit_code(value: str) -> str:
    if value.strip() == "":
        return value
    length = len(value)
    if length <= 4:
        return hide(value, 0, length)
    return hide(value, 4, length - 4)


def clear() -> str:
    return ""


# --- Type-based masked dispatch ----------------------------------------------

from enum import IntEnum


class MaskType(IntEnum):
    USER_ID = 0
    CHINESE_NAME = 1
    ID_CARD = 2
    FIXED_PHONE = 3
    MOBILE_PHONE = 4
    ADDRESS = 5
    EMAIL = 6
    PASSWORD = 7
    CAR_LICENSE = 8
    BANK_CARD = 9
    IPV4 = 10
    IPV6 = 11
    PASSPORT = 12
    CREDIT_CODE = 13
    FIRST_MASK = 14
    CLEAR_TO_NULL = 15
    CLEAR_TO_EMPTY = 16


def masked(value: str, typ: MaskType) -> str:
    if value.strip() == "":
        return ""
    if typ == MaskType.USER_ID:
        return "0"
    if typ == MaskType.CHINESE_NAME:
        return chinese_name(value)
    if typ == MaskType.ID_CARD:
        return id_card(value, 1, 2)
    if typ == MaskType.FIXED_PHONE:
        return fixed_phone(value)
    if typ == MaskType.MOBILE_PHONE:
        return mobile_phone(value)
    if typ == MaskType.ADDRESS:
        return address(value, 8)
    if typ == MaskType.EMAIL:
        return email(value)
    if typ == MaskType.PASSWORD:
        return password(value)
    if typ == MaskType.CAR_LICENSE:
        return car_license(value)
    if typ == MaskType.BANK_CARD:
        return bank_card(value)
    if typ == MaskType.IPV4:
        return ipv4(value)
    if typ == MaskType.IPV6:
        return ipv6(value)
    if typ == MaskType.PASSPORT:
        return passport(value)
    if typ == MaskType.CREDIT_CODE:
        return credit_code(value)
    if typ == MaskType.FIRST_MASK:
        return first_mask(value)
    if typ in (MaskType.CLEAR_TO_EMPTY, MaskType.CLEAR_TO_NULL):
        return ""
    return value


def masked_ptr(value: str, typ: MaskType) -> str | None:
    if typ == MaskType.CLEAR_TO_NULL:
        return None
    return masked(value, typ)


def clear_to_nil() -> None:
    return None


def user_id_value() -> int:
    return 0
