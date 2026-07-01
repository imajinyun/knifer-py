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


def test_category_detection() -> None:
    analysis = vpass.analyze("Ab3$defgh")
    assert analysis.has_lower
    assert analysis.has_upper
    assert analysis.has_digit
    assert analysis.has_symbol


def test_repeated_and_sequential_penalties() -> None:
    assert vpass.analyze("aaa12345").repeated
    assert vpass.analyze("abcdefgh").sequential


def test_strong_password() -> None:
    analysis = vpass.analyze("Tr0ub4dour&3xtraLong!")
    assert analysis.strength >= Strength.STRONG
    assert vpass.is_strong("Tr0ub4dour&3xtraLong!")


def test_single_category_is_capped() -> None:
    # Long, but only lowercase letters (avoid sequential/repeated runs).
    assert vpass.score("qzmwpbjxvktr") <= 35


def test_strength_str() -> None:
    assert str(Strength.VERY_WEAK) == "very weak"
    assert str(Strength.STRONG) == "strong"
    assert str(Strength.UNKNOWN) == "unknown"
