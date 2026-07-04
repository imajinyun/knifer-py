from __future__ import annotations

from datetime import date

from kniferpy.internal import identx
from kniferpy.internal.identx import (
    CreditCodeInfo,
    Gender,
    IDCardInfo,
    RegionCardInfo,
)

__all__ = [
    "Gender",
    "GenderFemale",
    "GenderMale",
    "GenderUnknown",
    "IDCardInfo",
    "RegionCardInfo",
    "CreditCodeInfo",
    "convert_15_to_18",
    "convert_18_to_15",
    "is_valid_id_card",
    "is_valid_id_card18",
    "is_valid_id_card15",
    "is_valid_tw_id_card",
    "is_valid_hk_id_card",
    "parse_region_card",
    "check_code18",
    "is_valid_birthday",
    "birth_string",
    "birth_date",
    "age",
    "age_at",
    "year",
    "month",
    "day",
    "gender_of",
    "province_code",
    "province",
    "city_code",
    "district_code",
    "parse_id_card",
    "hide",
    "is_valid_credit_code",
    "parse_credit_code",
]


def convert_15_to_18(id_card: str) -> str | None:
    return identx.convert_15_to_18(id_card)


def convert_18_to_15(id_card: str) -> str | None:
    return identx.convert_18_to_15(id_card)


def is_valid_id_card(id_card: str) -> bool:
    return identx.is_valid_id_card(id_card)


def is_valid_id_card18(id_card: str, ignore_case: bool = True) -> bool:
    return identx.is_valid_id_card18(id_card, ignore_case)


def is_valid_id_card15(id_card: str) -> bool:
    return identx.is_valid_id_card15(id_card)


def is_valid_tw_id_card(id_card: str) -> bool:
    return identx.is_valid_tw_id_card(id_card)


def is_valid_hk_id_card(id_card: str) -> bool:
    return identx.is_valid_hk_id_card(id_card)


def parse_region_card(id_card: str) -> RegionCardInfo | None:
    return identx.parse_region_card(id_card)


def check_code18(code17: str) -> str:
    return identx.check_code18(code17)


def is_valid_birthday(s: str) -> bool:
    return identx.is_valid_birthday(s)


def birth_string(id_card: str) -> str | None:
    return identx.birth_string(id_card)


def birth_date(id_card: str) -> date | None:
    return identx.birth_date(id_card)


def age(id_card: str) -> int | None:
    return identx.age(id_card)


def age_at(id_card: str, at: date) -> int | None:
    return identx.age_at(id_card, at)


def year(id_card: str) -> int | None:
    return identx.year(id_card)


def month(id_card: str) -> int | None:
    return identx.month(id_card)


def day(id_card: str) -> int | None:
    return identx.day(id_card)


def gender_of(id_card: str) -> Gender | None:
    return identx.gender_of(id_card)


def province_code(id_card: str) -> str | None:
    return identx.province_code(id_card)


def province(id_card: str) -> str | None:
    return identx.province(id_card)


def city_code(id_card: str) -> str | None:
    return identx.city_code(id_card)


def district_code(id_card: str) -> str | None:
    return identx.district_code(id_card)


def parse_id_card(id_card: str) -> IDCardInfo | None:
    return identx.parse_id_card(id_card)


def hide(id_card: str, start: int, end: int) -> str:
    return identx.hide(id_card, start, end)


def is_valid_credit_code(code: str) -> bool:
    return identx.is_valid_credit_code(code)


def parse_credit_code(code: str) -> CreditCodeInfo:
    return identx.parse_credit_code(code)


# Go compat Gender constants
GenderUnknown = Gender.UNKNOWN
GenderFemale = Gender.FEMALE
GenderMale = Gender.MALE
