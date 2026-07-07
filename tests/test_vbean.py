from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

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


def test_tag_alias_list_and_semicolon_aliases() -> None:
    @dataclass
    class AliasTarget:
        name: str = field(default="", metadata={"bean": ["nickname", "alias"]})
        code: str = field(default="", metadata={"bean": "code,aliases=c1;c2"})
        custom: str = field(default="", metadata={"custom": "customName"})

    dst = AliasTarget()
    opts = vbean.Options(tag_names=("custom", "bean"))
    vbean.decode({"ALIAS": "kim", "c2": "007", "customName": "x"}, dst, opts)

    assert dst.name == "kim"
    assert dst.code == "007"
    assert dst.custom == "x"


def test_tuple_set_frozenset_and_dict_key_conversion() -> None:
    @dataclass
    class TypesTarget:
        pair: tuple[int, str] = (0, "")
        open_tuple: tuple[int, ...] = ()
        numbers: set[int] = field(default_factory=set)
        frozen: frozenset[int] = frozenset()
        mapping: dict[int, bool] = field(default_factory=dict)
        raw: object = None
        any_value: object = None
        blob: bytes = b""
        ratio: float = 0.0

    dst = TypesTarget()
    vbean.decode(
        {
            "pair": ["7", 8],
            "open_tuple": ["1", "2"],
            "numbers": ["1", "2"],
            "frozen": ["3", "4"],
            "mapping": {"1": "true", "2": "false"},
            "raw": {"a": 1},
            "any_value": [1, "x"],
            "blob": "hi",
            "ratio": "1.25",
        },
        dst,
    )

    assert dst.pair == (7, "8")
    assert dst.open_tuple == (1, 2)
    assert dst.numbers == {1, 2}
    assert dst.frozen == frozenset({3, 4})
    assert dst.mapping == {1: True, 2: False}
    assert dst.raw == {"a": 1}
    assert dst.any_value == [1, "x"]
    assert dst.blob == b"hi"
    assert dst.ratio == 1.25


def test_conversion_error_branches() -> None:
    @dataclass
    class TypesTarget:
        values: list[int] = field(default_factory=list)
        mapping: dict[str, int] = field(default_factory=dict)

    with pytest.raises(ValidationError) as list_exc:
        vbean.decode({"values": "not-list"}, TypesTarget())
    with pytest.raises(ValidationError) as map_exc:
        vbean.decode({"mapping": "not-map"}, TypesTarget())
    assert list_exc.value.code == "knifer.bean.convert"
    assert map_exc.value.code == "knifer.bean.convert"


def test_union_and_non_assignable_conversion_paths() -> None:
    @dataclass
    class UnionTarget:
        value: int | str | None = None
        required: bytes = b""

    dst = UnionTarget()
    vbean.decode({"value": {"kept": True}, "required": "x"}, dst)
    assert cast(Any, dst).value == {"kept": True}
    assert dst.required == b"x"

    bytes_dst = UnionTarget()
    vbean.decode({"required": object()}, bytes_dst)
    assert isinstance(bytes_dst.required, bytes)


def test_dataclass_to_dict_conversion_for_mapping_field() -> None:
    @dataclass
    class Pair:
        key: str = "1"
        value: int = 2

    @dataclass
    class DictTarget:
        mapping: dict[str, int] = field(default_factory=dict)

    dst = DictTarget()
    vbean.decode({"mapping": Pair()}, dst)
    assert dst.mapping == {"key": 1, "value": 2}


def test_type_hints_failure_falls_back_to_existing_attrs() -> None:
    class BadHints:
        __annotations__ = {"value": "missing.Type"}

        def __init__(self) -> None:
            self.value = ""

    dst = BadHints()
    vbean.decode({"value": 123}, dst)
    assert cast(Any, dst).value == 123


def test_plain_object_target_and_source_errors() -> None:
    class SourceObj:
        def __init__(self) -> None:
            self.name = "plain"
            self._hidden = "skip"

    class TargetObj:
        name: str

        def __init__(self) -> None:
            self.name = ""

    dst = TargetObj()
    vbean.decode(SourceObj(), dst)
    assert dst.name == "plain"

    with pytest.raises(ValidationError):
        vbean.to_map(object())


def test_decode_hook_timedelta_and_passthrough() -> None:
    @dataclass
    class TimeoutConfig:
        delay: timedelta = timedelta()
        name: str = ""

    dst = TimeoutConfig()
    opts = vbean.Options(decode_hook=vbean.string_to_timedelta_hook())
    vbean.decode({"delay": "1h30m", "name": "job"}, dst, opts)
    assert dst.delay == timedelta(hours=1, minutes=30)
    assert dst.name == "job"

    empty = TimeoutConfig(delay=timedelta(seconds=1))
    vbean.decode({"delay": ""}, empty, opts)
    assert empty.delay == timedelta(0)
    invalid = TimeoutConfig()
    with pytest.raises(ValidationError):
        vbean.decode({"delay": "bad"}, invalid, opts)


def test_timedelta_hook_all_units_and_incomplete_values() -> None:
    @dataclass
    class TimeoutConfig:
        delay: timedelta = timedelta()

    opts = vbean.Options(decode_hook=vbean.string_to_timedelta_hook())
    dst = TimeoutConfig()
    vbean.decode({"delay": "1w2d3h4m5s6u"}, dst, opts)
    assert dst.delay == (
        timedelta(weeks=1)
        + timedelta(days=2)
        + timedelta(hours=3)
        + timedelta(minutes=4)
        + timedelta(seconds=5)
        + timedelta(microseconds=6)
    )

    bad = TimeoutConfig()
    with pytest.raises(ValidationError):
        vbean.decode({"delay": "h"}, bad, opts)


def test_compose_decode_hook_skips_none_and_updates_type() -> None:
    seen: list[tuple[type | None, object]] = []

    def to_text(from_type: type | None, to_type: object, value: object) -> object:
        seen.append((from_type, value))
        return str(value)

    def add_suffix(from_type: type | None, to_type: object, value: object) -> object:
        seen.append((from_type, value))
        return f"{value}!"

    hook = vbean.compose_decode_hook(None, to_text, add_suffix)
    assert hook(int, str, 7) == "7!"
    assert seen == [(int, 7), (str, "7")]


def test_merge_with_options_aliases() -> None:
    dst = Target()
    vbean.merge_with_options(dst, [{"name": "kim"}, {"age": "30"}])
    assert dst.name == "kim"
    assert dst.age == 30
    result = vbean.merge_result_with_options(dst, [{"active": "true"}])
    assert result.matched == ["active"]
    assert dst.active is True
