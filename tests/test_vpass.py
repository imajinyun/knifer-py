import pytest

from kniferpy import vpass
from kniferpy.vpass import Strength


def test_empty_password_is_very_weak() -> None:
    analysis = vpass.analyze("")
    assert analysis.score == 0
    assert analysis.strength is Strength.VERY_WEAK
    assert analysis.length == 0
    assert not analysis.has_lower
    assert not analysis.has_upper


def test_common_weak_password_is_capped() -> None:
    assert vpass.score("password") <= 10
    assert vpass.is_weak("password")
    assert not vpass.is_strong("password")
    assert vpass.analyze("123456").common_weak


def test_all_common_weak_passwords() -> None:
    common = {
        "000000", "111111", "123123", "123456", "12345678", "123456789",
        "admin", "iloveyou", "letmein", "password", "password1",
        "qwerty", "qwerty123", "welcome", "woaini", "zxcvbn",
    }
    for pwd in common:
        assert vpass.analyze(pwd).common_weak, f"{pwd!r} should be common_weak"
        assert vpass.is_weak(pwd)


def test_category_detection() -> None:
    analysis = vpass.analyze("Ab3$defgh")
    assert analysis.has_lower
    assert analysis.has_upper
    assert analysis.has_digit
    assert analysis.has_symbol


def test_lowercase_only() -> None:
    analysis = vpass.analyze("abcdefgh")
    assert analysis.has_lower
    assert not analysis.has_upper
    assert not analysis.has_digit
    assert not analysis.has_symbol


def test_uppercase_only() -> None:
    analysis = vpass.analyze("ABCDEFGH")
    assert not analysis.has_lower
    assert analysis.has_upper
    assert not analysis.has_digit
    assert not analysis.has_symbol


def test_digits_only() -> None:
    analysis = vpass.analyze("12345678")
    assert not analysis.has_lower
    assert not analysis.has_upper
    assert analysis.has_digit
    assert not analysis.has_symbol


def test_symbols_only() -> None:
    analysis = vpass.analyze("!@#$%^&*()")
    assert not analysis.has_lower
    assert not analysis.has_upper
    assert not analysis.has_digit
    assert analysis.has_symbol


def test_repeated_and_sequential_penalties() -> None:
    assert vpass.analyze("aaa12345").repeated
    assert vpass.analyze("abcdefgh").sequential


def test_repeated_characters_detected() -> None:
    assert vpass.analyze("abcccde").repeated
    assert not vpass.analyze("abcabc").repeated


def test_sequential_descending_detected() -> None:
    assert vpass.analyze("cba9876").sequential


def test_strong_password() -> None:
    analysis = vpass.analyze("Tr0ub4dour&3xtraLong!")
    assert analysis.strength >= Strength.STRONG
    assert vpass.is_strong("Tr0ub4dour&3xtraLong!")


def test_very_strong_password() -> None:
    analysis = vpass.analyze("C0mpl3x!P@ssw0rd#2026$Secure")
    assert analysis.strength is Strength.VERY_STRONG


def test_single_category_is_capped() -> None:
    # Long, but only lowercase letters (avoid sequential/repeated runs).
    assert vpass.score("qzmwpbjxvktr") <= 35


def test_short_password_is_weak() -> None:
    assert vpass.is_weak("Ab1!")
    assert vpass.score("Ab1!") < 50


def test_strength_of_helper() -> None:
    assert vpass.strength_of("") is Strength.VERY_WEAK
    assert vpass.strength_of("password") is Strength.VERY_WEAK
    assert vpass.strength_of("Tr0ub4dour&3xtraLong!") >= Strength.STRONG


def test_strength_str() -> None:
    assert str(Strength.VERY_WEAK) == "very weak"
    assert str(Strength.WEAK) == "weak"
    assert str(Strength.MEDIUM) == "medium"
    assert str(Strength.STRONG) == "strong"
    assert str(Strength.VERY_STRONG) == "very strong"
    assert str(Strength.UNKNOWN) == "unknown"


def test_strength_int_values() -> None:
    assert Strength.VERY_WEAK == 1
    assert Strength.WEAK == 2
    assert Strength.MEDIUM == 3
    assert Strength.STRONG == 4
    assert Strength.VERY_STRONG == 5


def test_analysis_attributes() -> None:
    analysis = vpass.analyze("Hello123!")
    assert isinstance(analysis.score, int)
    assert isinstance(analysis.strength, Strength)
    assert isinstance(analysis.length, int)
    assert isinstance(analysis.has_lower, bool)
    assert isinstance(analysis.has_upper, bool)
    assert isinstance(analysis.has_digit, bool)
    assert isinstance(analysis.has_symbol, bool)
    assert isinstance(analysis.repeated, bool)
    assert isinstance(analysis.sequential, bool)
    assert isinstance(analysis.common_weak, bool)


def test_medium_strength_threshold() -> None:
    analysis = vpass.analyze("HelloWorld123")
    assert analysis.strength >= Strength.MEDIUM


def test_long_password_boost() -> None:
    # 16+ chars gets a boost
    analysis = vpass.analyze("Abcdefghijklmnop123!")
    assert analysis.length >= 16
    assert analysis.score >= 70