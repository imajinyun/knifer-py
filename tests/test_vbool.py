from kniferpy import vbool


def test_negate_and_to_int() -> None:
    assert vbool.negate(False) is True
    assert vbool.negate(True) is False
    assert vbool.to_int(True) == 1
    assert vbool.to_int(False) == 0


def test_all_and_any() -> None:
    assert vbool.all_true([True, True]) is True
    assert vbool.all_true([True, False]) is False
    # Vacuous truth matches knifer-go And() with no inputs.
    assert vbool.all_true([]) is True
    assert vbool.any_true([False, True]) is True
    assert vbool.any_true([False, False]) is False
    assert vbool.any_true([]) is False
