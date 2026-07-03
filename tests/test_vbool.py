from kniferpy import vbool


def test_negate_and_to_int() -> None:
    assert vbool.negate(False) is True
    assert vbool.negate(True) is False
    assert vbool.to_int(True) == 1
    assert vbool.to_int(False) == 0


def test_all_true_and_any_true() -> None:
    assert vbool.all_true([True, True]) is True
    assert vbool.all_true([True, False]) is False
    assert vbool.all_true([]) is True
    assert vbool.any_true([False, True]) is True
    assert vbool.any_true([False, False]) is False
    assert vbool.any_true([]) is False


def test_and_or() -> None:
    assert vbool.And(True, True) is True
    assert vbool.And(True, False) is False
    assert vbool.And() is True
    assert vbool.Or(False, True) is True
    assert vbool.Or(False, False) is False
    assert vbool.Or() is False