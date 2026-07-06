import pytest

from kniferpy import vobj
from kniferpy.internal import objx
from kniferpy.verr import SecurityError


def test_equal_length_contains_and_empty() -> None:
    assert vobj.equal(1, 1.0)
    assert vobj.not_equal("a", "b")
    assert vobj.length([1, 2, 3]) == 3
    assert vobj.length(10) == -1
    assert vobj.contains([1, 2, 3], 2)
    assert vobj.contains("hello", "ell")
    assert vobj.contains({"a": 1}, 1)
    assert not vobj.contains({"a": 1}, 2)
    assert not vobj.contains(None, "x")
    assert not vobj.contains("hello", None)
    assert vobj.is_empty({})
    assert not vobj.is_empty(1)
    assert vobj.is_not_empty([1])


def test_none_and_empty_predicates() -> None:
    assert vobj.is_none(None)
    assert not vobj.is_none(0)
    assert vobj.is_not_none(0)
    assert not vobj.is_not_none(None)
    assert vobj.is_empty(None)
    assert vobj.is_empty("")
    assert vobj.is_empty([])
    assert not vobj.is_empty("go")


def test_defaults_apply_accept() -> None:
    name = "go"
    assert vobj.default_if_none(name, "x") == "go"
    assert vobj.default_if_none(None, "x") == "x"

    calls = 0

    def supplier() -> str:
        nonlocal calls
        calls += 1
        return "fallback"

    assert vobj.default_if_none_func(name, supplier) == "go"
    assert calls == 0
    assert vobj.default_if_none_func(None, supplier) == "fallback"
    assert calls == 1

    assert vobj.default_if_none_apply(name, str.upper, "fallback") == "GO"
    assert vobj.default_if_none_apply(None, str.upper, "fallback") == "fallback"

    assert vobj.apply(name, len) == 2
    assert vobj.apply(None, len) is None

    captured: list[str] = []
    vobj.accept(name, captured.append)
    vobj.accept(None, captured.append)
    assert captured == ["go"]


def test_basic_type_and_valid_number() -> None:
    assert vobj.is_basic_type("x")
    assert vobj.is_basic_type(1)
    assert not vobj.is_basic_type([1])
    assert not vobj.is_basic_type(None)
    assert vobj.is_valid_if_number(1)
    assert vobj.is_valid_if_number(1.25)
    assert not vobj.is_valid_if_number(float("nan"))
    assert not vobj.is_valid_if_number(float("inf"))
    assert vobj.is_valid_if_number("x")


def test_compare_and_compare_none() -> None:
    assert vobj.compare(1, 2) < 0
    assert vobj.compare(2, 1) > 0
    assert vobj.compare(1, 1) == 0
    assert vobj.compare(None, 1) > 0
    assert vobj.compare(1, None) < 0
    assert vobj.compare(None, None) == 0
    assert vobj.compare_none(None, 1, False) < 0
    assert vobj.compare_none(1, None, False) > 0


def test_type_and_string() -> None:
    assert vobj.type_of(None) is None
    assert vobj.type_of(42) is int
    assert vobj.type_name(None) == ""
    assert vobj.type_name(42) == "int"
    assert vobj.type_name("x") == "str"
    assert vobj.to_string(None) == "null"
    assert vobj.to_string(42) == "42"


def test_aggregate_helpers() -> None:
    assert vobj.empty_count(None, "", [], "go") == 3
    assert vobj.has_none("go", None)
    assert not vobj.has_none("go", 1)
    assert vobj.has_empty("go", [])
    assert not vobj.has_empty("go", [1])
    assert vobj.is_all_empty(None, "", [])
    assert not vobj.is_all_empty("", "x")
    assert vobj.is_all_not_empty("x", [1])
    assert not vobj.is_all_not_empty("x", [])


def test_alias_null_nil_helpers() -> None:
    assert vobj.equals(1, 1)
    assert vobj.is_null(None)
    assert vobj.is_not_null(1)
    assert vobj.is_nil(None)
    assert vobj.is_not_nil(1)
    assert vobj.has_null(1, None)
    assert not vobj.has_null(1, 2)


def test_equal_none_and_length_custom_len() -> None:
    class CustomLen:
        def __len__(self) -> int:
            return 0

    assert vobj.equal(None, None)
    assert not vobj.equal(None, 1)
    assert vobj.length(None) == 0
    assert vobj.is_empty(CustomLen())


def test_clone_serialize_deserialize_roundtrip() -> None:
    value = {"items": [1, 2], "name": "kniferpy"}

    cloned = vobj.clone(value)
    stream_clone = vobj.clone_by_stream(value)
    encoded = vobj.serialize(value)

    assert cloned == value
    assert cloned is not value
    assert stream_clone == value
    assert vobj.deserialize(encoded, dict) == value
    assert vobj.deserialize_to(encoded) == value
    assert vobj.must_deserialize(encoded) == value
    assert vobj.clone_with_options(value) == value
    assert vobj.clone_by_stream_with_options(value) == value
    assert vobj.serialize_with_options(value) == encoded
    assert vobj.deserialize_with_options(encoded, dict) == value
    assert vobj.deserialize_to_with_options(encoded) == value


def test_codec_factory_options_and_failure_paths() -> None:
    original = dict(objx._CODEC_CONFIG)
    try:
        vobj.with_encoder_factory(lambda: lambda obj: b"encoded")
        vobj.with_decoder_factory(lambda: lambda data: {"decoded": data.decode()})
        assert vobj.serialize("ignored") == b"encoded"
        assert vobj.deserialize(b"value", dict) == {"decoded": "value"}

        vobj.with_encoder_factory(lambda: lambda obj: (_ for _ in ()).throw(RuntimeError("boom")))
        value = object()
        assert vobj.serialize_or_nil(value) is None
        assert vobj.serialize_or_nil_with_options(value) is None
        assert vobj.clone_if_possible(value) is value
        assert vobj.clone_if_possible_with_options(value) is value
    finally:
        objx._CODEC_CONFIG.clear()
        objx._CODEC_CONFIG.update(original)


def test_register_and_accepted_type_validation() -> None:
    class SafeCustom:
        pass

    class UnsafeCustom:
        pass

    vobj.register(SafeCustom)
    vobj.register_name("custom", SafeCustom)
    assert objx._REGISTERED_TYPES["SafeCustom"] is SafeCustom
    assert objx._REGISTERED_TYPES["custom"] is SafeCustom

    vobj.validate_accepted_types({"k": [SafeCustom(), 1, "x", None]}, SafeCustom)
    encoded = vobj.serialize({"k": [1, "x", None]})
    assert vobj.deserialize(encoded, dict) == {"k": [1, "x", None]}
    assert vobj.deserialize_to(encoded) == {"k": [1, "x", None]}

    with pytest.raises(SecurityError) as unsafe_value_exc:
        vobj.validate_accepted_types(UnsafeCustom(), SafeCustom)
    with pytest.raises(SecurityError) as unsafe_key_exc:
        vobj.validate_accepted_types({UnsafeCustom(): "value"}, SafeCustom)

    assert unsafe_value_exc.value.code == "knifer.unsafe_type"
    assert unsafe_key_exc.value.code == "knifer.unsafe_type"
