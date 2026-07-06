import datetime

import pytest

from kniferpy import vident
from kniferpy.internal import identx
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
    assert not vident.is_valid_id_card18("11010519490230002X")
    assert not vident.is_valid_id_card18("1101051949123100AX")


def test_mainland_15_and_convert() -> None:
    assert vident.is_valid_id_card15("130503670401001")
    assert vident.is_valid_id_card("130503670401001")
    assert vident.convert_15_to_18("130503670401001") == "130503196704010016"
    assert vident.convert_18_to_15("130503196704010016") == "130503670401001"
    assert vident.convert_15_to_18("bad") is None
    assert vident.convert_18_to_15("110105194912310021") is None
    assert not vident.is_valid_id_card15("990503670401001")


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


def test_invalid_card_derived_fields_are_none() -> None:
    assert vident.birth_string("bad") is None
    assert vident.birth_date("bad") is None
    assert vident.age_at("bad", datetime.date(2000, 1, 1)) is None
    assert vident.year("bad") is None
    assert vident.month("bad") is None
    assert vident.day("bad") is None
    assert vident.gender_of("bad") is None
    assert vident.gender_of("1101051949123100AX") is None
    assert vident.province_code("bad") is None
    assert vident.province("bad") is None
    assert vident.city_code("bad") is None
    assert vident.district_code("bad") is None


def test_parse_id_card() -> None:
    info = vident.parse_id_card("11010519491231002X")
    assert info is not None
    assert info.province == "北京"
    assert info.gender is vident.Gender.FEMALE
    assert info.district_code == "110105"
    assert vident.parse_id_card("bad") is None


def test_parse_id_card_returns_none_when_derived_fields_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(identx, "is_valid_id_card18", lambda _card: True)
    monkeypatch.setattr(identx, "is_valid_id_card15", lambda _card: False)
    monkeypatch.setattr(identx, "birth_date", lambda _card: None)

    assert identx.parse_id_card("11010519491231002X") is None


def test_region_cards() -> None:
    assert vident.is_valid_tw_id_card("A123456789")
    assert vident.is_valid_hk_id_card("A123456(3)")
    assert not vident.is_valid_hk_id_card("AB123456(3)")
    assert not vident.is_valid_hk_id_card("A123456A")
    tw = vident.parse_region_card("A123456789")
    assert tw is not None and tw.region == "台湾" and tw.gender == "M" and tw.valid
    tw_female = vident.parse_region_card("A223456781")
    assert tw_female is not None and tw_female.region == "台湾" and tw_female.gender == "F"
    tw_unknown = vident.parse_region_card("A323456789")
    assert tw_unknown is not None and tw_unknown.region == "台湾" and not tw_unknown.valid
    macau = vident.parse_region_card("1571234(5)")
    assert macau is not None and macau.region == "澳门" and macau.valid
    macau_full = vident.parse_region_card("1571234（5）")
    assert macau_full is not None and macau_full.region == "澳门" and macau_full.valid
    hk = vident.parse_region_card("A123456(3)")
    assert hk is not None and hk.region == "香港" and hk.valid
    assert vident.parse_region_card("") is None
    assert vident.parse_region_card("ABC") is None
    assert not vident.is_valid_id_card("")
    assert not vident.is_valid_id_card("A323456789")
    assert not vident.is_valid_tw_id_card("Z12345678A")
    assert not vident.is_valid_hk_id_card("A12345A(3)")


def test_region_card_defensive_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    class AlwaysMatch:
        def match(self, _card: str) -> object:
            return object()

    with monkeypatch.context() as patch:
        patch.setattr(identx, "_RX_TW_CARD", AlwaysMatch())
        assert not identx.is_valid_tw_id_card("0123456789")
        assert not identx.is_valid_tw_id_card("A12A456789")
        assert not identx.is_valid_tw_id_card("A12345678A")

    with monkeypatch.context() as patch:
        patch.setattr(identx, "_RX_HK_ID", AlwaysMatch())
        assert not identx.is_valid_hk_id_card("A12345A3")
        assert not identx.is_valid_hk_id_card("A123456Z")

    assert identx.parse_region_card("ABCDEFGH") is None
    assert not vident.is_valid_id_card("abc")


def test_birth_date_returns_none_when_parser_rejects_birth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(identx, "birth_string", lambda _card: "19990230")

    assert identx.birth_date("11010519491231002X") is None


def test_birth_string_for_invalid_15_digit_card() -> None:
    assert vident.birth_string("130503990230001") is None


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
    zero_check = vident.parse_credit_code("000000000000000000")
    assert zero_check.check_digit == "0"
    assert vident.parse_credit_code(" 91350211m000100y46 ").raw == "91350211M000100Y46"
    assert not vident.is_valid_credit_code("91350211M000100Y44")
    with pytest.raises(ValidationError):
        vident.parse_credit_code("91350211M000100Y4")
    with pytest.raises(ValidationError):
        vident.parse_credit_code("91350211I000100Y46")
    with pytest.raises(ValidationError):
        vident.parse_credit_code("91350211M000100Y4I")
