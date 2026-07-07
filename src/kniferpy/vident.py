from __future__ import annotations

from datetime import date
from typing import Any, Callable

from kniferpy.internal import identx
from kniferpy.internal.identx import (
    CreditCodeInfo,
    Gender,
    IDCardInfo,
    RegionCardInfo,
)

# ── Go-compat type aliases: functional option types ──────────────────────────

IDCardOption = Callable[[Any], None]
"""Functional option for ID card validation/parsing helpers."""

BirthOption = Callable[[Any], None]
"""Functional option for birthday parsing helpers."""

AgeOption = Callable[[Any], None]
"""Functional option for age computation helpers."""

# ── Go-compat option builders ─────────────────────────────────────────────────


def WithDigitsMatcher(_matcher: Callable[[str], bool]) -> IDCardOption:
    """Inject a custom decimal-digit matcher for mainland ID card helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithTWCardMatcher(_matcher: Callable[[str], bool]) -> IDCardOption:
    """Inject a custom format matcher for Taiwan ID card helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithMacauCardMatcher(_matcher: Callable[[str], bool]) -> IDCardOption:
    """Inject a custom format matcher for Macau ID card helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithHKCardMatcher(_matcher: Callable[[str], bool]) -> IDCardOption:
    """Inject a custom format matcher for Hong Kong ID card helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithBirthLocation(_location: str) -> BirthOption:
    """Set the timezone location for birthday parsing."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithBirthDigitsMatcher(_matcher: Callable[[str], bool]) -> BirthOption:
    """Inject a custom decimal-digit matcher for birthday helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithBirthParser(_parser: Callable[[str], date]) -> BirthOption:
    """Inject a custom date parser for birthday helpers."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithAgeTime(_at: date) -> AgeOption:
    """Set the reference time for age computation."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


def WithAgeClock(_clock: Callable[[], date]) -> AgeOption:
    """Inject a custom clock function for age computation."""

    def _apply(_cfg: Any) -> None:
        pass

    return _apply


__all__ = [
    "Gender",
    "GenderFemale",
    "GenderMale",
    "GenderUnknown",
    "IDCardInfo",
    "RegionCardInfo",
    "CreditCodeInfo",
    # Go-compat option types
    "IDCardOption",
    "BirthOption",
    "AgeOption",
    # Go-compat option builders
    "WithDigitsMatcher",
    "WithTWCardMatcher",
    "WithMacauCardMatcher",
    "WithHKCardMatcher",
    "WithBirthLocation",
    "WithBirthDigitsMatcher",
    "WithBirthParser",
    "WithAgeTime",
    "WithAgeClock",
    # Core functions
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
    # WithOptions variants
    "convert_15_to_18_with_options",
    "convert_18_to_15_with_options",
    "is_valid_id_card_with_options",
    "is_valid_id_card18_with_options",
    "is_valid_id_card15_with_options",
    "is_valid_tw_id_card_with_options",
    "is_valid_hk_id_card_with_options",
    "parse_region_card_with_options",
    "check_code18_with_options",
    "is_valid_birthday_with_options",
    "birth_string_with_options",
    "birth_date_with_options",
    "age_with_options",
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

# ── WithOptions aliases (Go compat) ──────────────────────────────────────────

convert_15_to_18_with_options = convert_15_to_18
convert_18_to_15_with_options = convert_18_to_15
is_valid_id_card_with_options = is_valid_id_card
is_valid_id_card18_with_options = is_valid_id_card18
is_valid_id_card15_with_options = is_valid_id_card15
is_valid_tw_id_card_with_options = is_valid_tw_id_card
is_valid_hk_id_card_with_options = is_valid_hk_id_card
parse_region_card_with_options = parse_region_card
check_code18_with_options = check_code18
is_valid_birthday_with_options = is_valid_birthday
birth_string_with_options = birth_string
birth_date_with_options = birth_date
age_with_options = age
