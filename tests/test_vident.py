import pytest

from kniferpy import vident
from kniferpy.verr import ValidationError


def test_mainland_18_validation() -> None:
    assert vident.is_valid_id_card18("11010519491231002X")
    assert vident.is_valid_id_card18("11010519491231002x")
    assert vident.is_valid_id_card("11010519491231002X")
    assert vident.is_valid_id_card18("11010519491231002X", ignore_case=False)
    assert not vident.is_valid_id_card18("11010519491231002x", ignore_case=False)
    assert vident.is_valid_id_card18("130503196704010016")
    assert not vident.is_valid_id_card18("110105194912310021")
    assert not vident.is_valid_id_card18("00010519491231002X")


def test_mainland_15_and_convert() -> None:
    assert vident.is_valid_id_card15("130503670401001")
    assert vident.is_valid_id_card("130503670401001")
    assert vident.convert_15_to_18("130503670401001") == "130503196704010016"
    assert vident.convert_18_to_15("130503196704010016") == "130503670401001"
    assert vident.convert_15_to_18("bad") is None
    assert vident.convert_18_to_15("110105194912310021") is None


def test_check_code_and_birthday() -> None:
    assert vident.check_code18("11010519491231002") == "X"
    assert vident.check_code18("bad") == " "
    assert vident.is_valid_birthday("19491231")
    assert not vident.is_valid_birthday("19990230")
    assert not vident.is_valid_birthday("1999123")


def test_birth_age_gender_fields() -> None:
    card = "11010519491231002X"
    assert vident.birth_string(card) == "19491231"
    birth = vident.birth_date(card)
    assert birth is not None and (birth.year, birth.month, birth.day) == (1949, 12, 31)
    assert vident.year(card) == 1949
    assert vident.month(card) == 12
    assert vident.day(card) == 31
    assert vident.gender_of(card) is vident.Gender.FEMALE
    assert vident.province_code(card) == "11"
    assert vident.province(card) == "北京"
    assert vident.city_code(card) == "1101"
    assert vident.district_code(card) == "110105"

    import datetime

    assert vident.age_at(card, datetime.date(2000, 1, 1)) == 50
    assert vident.age_at(card, datetime.date(2000, 12, 30)) == 50
    assert vident.age_at(card, datetime.date(2000, 12, 31)) == 51


def test_parse_id_card() -> None:
    info = vident.parse_id_card("11010519491231002X")
    assert info is not None
    assert info.province == "北京"
    assert info.gender is vident.Gender.FEMALE
    assert info.district_code == "110105"
    assert vident.parse_id_card("bad") is None


def test_region_cards() -> None:
    assert vident.is_valid_tw_id_card("A123456789")
    assert vident.is_valid_hk_id_card("A123456(3)")
    tw = vident.parse_region_card("A123456789")
    assert tw is not None and tw.region == "台湾" and tw.gender == "M" and tw.valid
    macau = vident.parse_region_card("1571234(5)")
    assert macau is not None and macau.region == "澳门" and macau.valid
    macau_full = vident.parse_region_card("1571234（5）")
    assert macau_full is not None and macau_full.region == "澳门" and macau_full.valid
    assert vident.parse_region_card("") is None
    assert vident.parse_region_card("ABC") is None
    assert not vident.is_valid_tw_id_card("Z12345678A")
    assert not vident.is_valid_hk_id_card("A12345A(3)")


def test_hide() -> None:
    assert vident.hide("11010519491231002X", 6, 14) == "110105********002X"
    assert vident.hide("abc", 5, 9) == "abc"
    assert vident.hide("abc", 2, 1) == "abc"


def test_credit_code() -> None:
    assert vident.is_valid_credit_code("91350211M000100Y46")
    info = vident.parse_credit_code("91350211M000100Y46")
    assert info.admin_dept == "9"
    assert info.region_code == "350211"
    assert info.check_digit == "6"
    assert not vident.is_valid_credit_code("91350211M000100Y44")
    with pytest.raises(ValidationError):
        vident.parse_credit_code("91350211M000100Y4")
    with pytest.raises(ValidationError):
        vident.parse_credit_code("91350211M000100Y4I")
