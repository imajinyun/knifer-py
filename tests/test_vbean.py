from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pytest

from kniferpy import vbean
from kniferpy.verr import ValidationError


@dataclass
class Source:
    name: str = ""
    age: int = 0
    active: bool = False


@dataclass
class Target:
    name: str = ""
    age: int = 0
    active: bool = False


@dataclass
class Tagged:
    user_name: str = field(default="", metadata={"bean": "userName,alias=uname|nick"})
    secret: str = field(default="", metadata={"bean": "-"})


# --- to_map / fill_map --------------------------------------------------------


def test_to_map_from_dataclass() -> None:
    assert vbean.to_map(Source(name="kim", age=30, active=True)) == {
        "name": "kim",
        "age": 30,
        "active": True,
    }


def test_to_map_from_mapping() -> None:
    assert vbean.to_map({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_to_map_from_plain_object() -> None:
    class Obj:
        def __init__(self) -> None:
            self.x = 1
            self._hidden = 2

    assert vbean.to_map(Obj()) == {"x": 1}


def test_to_map_uses_tag_name() -> None:
    assert vbean.to_map(Tagged(user_name="kim")) == {"userName": "kim"}


def test_to_map_omits_dash_tag() -> None:
    result = vbean.to_map(Tagged(user_name="kim", secret="s"))
    assert "secret" not in result


def test_fill_map_into_existing() -> None:
    dst: dict[str, object] = {"keep": 1}
    vbean.fill_map({"a": 2}, dst)
    assert dst == {"keep": 1, "a": 2}


def test_fill_map_none_raises() -> None:
    with pytest.raises(ValidationError):
        vbean.fill_map({"a": 1}, None)  # type: ignore[arg-type]


def test_to_map_none_src_raises() -> None:
    with pytest.raises(ValidationError):
        vbean.to_map(None)


def test_to_map_scalar_src_raises() -> None:
    with pytest.raises(ValidationError):
        vbean.to_map(42)


# --- copy_properties ----------------------------------------------------------


def test_copy_dataclass_to_dataclass() -> None:
    dst = Target()
    vbean.copy_properties(Source(name="kim", age=30, active=True), dst)
    assert dst == Target(name="kim", age=30, active=True)


def test_copy_map_to_dataclass() -> None:
    dst = Target()
    vbean.copy_properties({"name": "amy", "age": 22}, dst)
    assert dst.name == "amy"
    assert dst.age == 22


def test_copy_to_dict_dst() -> None:
    dst: dict[str, object] = {}
    vbean.copy(Source(name="kim", age=1, active=False), dst)
    assert dst == {"name": "kim", "age": 1, "active": False}


def test_copy_none_dst_raises() -> None:
    with pytest.raises(ValidationError):
        vbean.copy_properties(Source(), None)


def test_copy_scalar_dst_raises() -> None:
    with pytest.raises(ValidationError):
        vbean.copy_properties(Source(), 5)


# --- case sensitivity & aliases ----------------------------------------------


def test_case_insensitive_matching_default() -> None:
    dst = Target()
    vbean.copy_properties({"NAME": "kim", "Age": 5}, dst)
    assert dst.name == "kim"
    assert dst.age == 5


def test_case_sensitive_option() -> None:
    dst = Target()
    opts = vbean.Options(case_insensitive=False)
    vbean.copy_properties({"NAME": "kim"}, dst, opts)
    assert dst.name == ""


def test_alias_matching() -> None:
    dst = Tagged()
    vbean.copy_properties({"nick": "kimmy"}, dst)
    assert dst.user_name == "kimmy"


# --- weak type conversion -----------------------------------------------------


def test_weak_string_to_int() -> None:
    dst = Target()
    vbean.decode({"age": "42"}, dst)
    assert dst.age == 42


def test_weak_int_to_string() -> None:
    dst = Target()
    vbean.decode({"name": 123}, dst)
    assert dst.name == "123"


def test_weak_string_to_bool() -> None:
    dst = Target()
    vbean.decode({"active": "yes"}, dst)
    assert dst.active is True


def test_weak_disabled_raises() -> None:
    dst = Target()
    opts = vbean.Options(weakly_typed=False)
    with pytest.raises(ValidationError):
        vbean.decode({"age": "42"}, dst, opts)


def test_bad_conversion_reports_field() -> None:
    dst = Target()
    with pytest.raises(ValidationError) as excinfo:
        vbean.decode({"age": "not-a-number"}, dst)
    assert "age" in excinfo.value.message


def test_bool_not_coerced_to_int_weakly() -> None:
    # A bool source stays a bool for a bool target; int target coerces it.
    dst = Target()
    vbean.decode({"active": 1}, dst)
    assert dst.active is True


# --- nested conversion --------------------------------------------------------


@dataclass
class Inner:
    id: int = 0
    label: str = ""


@dataclass
class Outer:
    inner: Inner | None = None
    tags: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def test_nested_dataclass_from_map() -> None:
    dst = Outer()
    vbean.decode({"inner": {"id": "7", "label": "x"}}, dst)
    assert dst.inner == Inner(id=7, label="x")


def test_list_element_conversion() -> None:
    dst = Outer()
    vbean.decode({"tags": [1, 2, 3]}, dst)
    assert dst.tags == ["1", "2", "3"]


def test_dict_value_conversion() -> None:
    dst = Outer()
    vbean.decode({"counts": {"a": "1", "b": "2"}}, dst)
    assert dst.counts == {"a": 1, "b": 2}


def test_optional_none_stays_none() -> None:
    dst = Outer()
    vbean.decode({"inner": None}, dst)
    assert dst.inner is None


# --- ignore options -----------------------------------------------------------


def test_ignore_empty() -> None:
    dst = Target(name="orig")
    opts = vbean.Options(ignore_empty=True)
    vbean.copy_properties({"name": ""}, dst, opts)
    assert dst.name == "orig"


def test_ignore_zero() -> None:
    dst = Target(age=99)
    opts = vbean.Options(ignore_zero=True)
    vbean.copy_properties({"age": 0}, dst, opts)
    assert dst.age == 99


# --- Result & strict ----------------------------------------------------------


def test_decode_result_reports_matched_and_unused() -> None:
    dst = Target()
    result = vbean.decode_result({"name": "kim", "extra": 1}, dst)
    assert result.matched == ["name"]
    assert result.unused == ["extra"]


def test_decode_result_reports_skipped() -> None:
    dst = Target()
    opts = vbean.Options(ignore_empty=True)
    result = vbean.decode_result({"name": "", "age": 3}, dst, opts)
    assert result.skipped == ["name"]
    assert result.matched == ["age"]


def test_strict_unused_raises() -> None:
    dst = Target()
    opts = vbean.Options(strict_unused=True)
    with pytest.raises(ValidationError):
        vbean.decode({"name": "kim", "surprise": 1}, dst, opts)


# --- merge --------------------------------------------------------------------


def test_merge_left_to_right() -> None:
    dst = Target()
    vbean.merge(dst, {"name": "a", "age": 1}, {"name": "b"})
    assert dst.name == "b"
    assert dst.age == 1


def test_merge_result_aggregates() -> None:
    dst = Target()
    result = vbean.merge_result(dst, {"name": "a"}, {"age": 2})
    assert result.matched == ["age", "name"]


# --- decode hooks -------------------------------------------------------------


@dataclass
class Event:
    when: datetime | None = None


def test_string_to_datetime_hook() -> None:
    dst = Event()
    opts = vbean.Options(decode_hook=vbean.string_to_datetime_hook("%Y-%m-%d"))
    vbean.decode({"when": "2026-07-03"}, dst, opts)
    assert dst.when == datetime(2026, 7, 3)


def test_compose_decode_hook() -> None:
    def upper(_from: type | None, _to: object, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    def suffix(_from: type | None, _to: object, value: object) -> object:
        return value + "!" if isinstance(value, str) else value

    dst = Target()
    opts = vbean.Options(decode_hook=vbean.compose_decode_hook(upper, suffix))
    vbean.decode({"name": "kim"}, dst, opts)
    assert dst.name == "KIM!"


def test_new_options_defaults() -> None:
    opts = vbean.new_options()
    assert opts.weakly_typed is True
    assert opts.case_insensitive is True
