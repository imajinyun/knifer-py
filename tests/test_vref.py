from __future__ import annotations

import dataclasses
import inspect

import pytest

from kniferpy import vref
from kniferpy.internal import refx
from kniferpy.verr import KniferError

# --- test helpers ---------------------------------------------------------------


@dataclasses.dataclass
class User:
    name: str
    age: int = 0

    def greet(self, prefix: str) -> str:
        return f"{prefix}, {self.name}"

    def get_name(self) -> str:
        return self.name

    def to_string(self) -> str:
        return self.name


@dataclasses.dataclass
class TaggedUser:
    name: str = dataclasses.field(metadata={"json": "user_name"})
    age: int = dataclasses.field(default=0, metadata={"ref": "user_age"})
    ignored: str = dataclasses.field(default="", metadata={"xml": "ignored_xml"})


@dataclasses.dataclass
class Base:
    base: str = "base"


@dataclasses.dataclass
class Child(Base):
    child: str = "child"


class Profile:
    def __init__(self, name: str) -> None:
        self.name = name
        self._secret = "hidden"

    def greet(self) -> str:
        return f"hello, {self.name}"


# --- type predicates (values) --------------------------------------------------


def test_is_function_returns_true_for_callable() -> None:
    assert vref.is_function(lambda: None) is True
    assert vref.is_function(sum) is True


def test_is_function_returns_false_for_non_callable() -> None:
    assert vref.is_function("not a function") is False
    assert vref.is_function(42) is False


def test_is_iterable_true() -> None:
    assert vref.is_iterable([1, 2, 3]) is True
    assert vref.is_iterable((1, 2)) is True
    assert vref.is_iterable({"a": 1}) is True


def test_is_iterable_false_for_string() -> None:
    assert vref.is_iterable("abc") is False


def test_is_collection() -> None:
    assert vref.is_collection([1, 2]) is True
    assert vref.is_collection((1,)) is True
    assert vref.is_collection({"a": 1}) is False


def test_is_slice() -> None:
    assert vref.is_slice([1, 2]) is True
    assert vref.is_slice((1, 2)) is False


def test_is_array() -> None:
    assert vref.is_array((1, 2)) is True
    assert vref.is_array([1, 2]) is False


def test_is_map() -> None:
    assert vref.is_map({"a": 1}) is True
    assert vref.is_map([1, 2]) is False


# --- type predicates (types) ---------------------------------------------------


def test_is_func_type() -> None:
    assert vref.is_func_type(type(lambda: None)) is True


def test_is_rangeable_type() -> None:
    assert vref.is_rangeable_type(list) is True
    assert vref.is_rangeable_type(dict) is True
    assert vref.is_rangeable_type(tuple) is True
    assert vref.is_rangeable_type(int) is False
    assert vref.is_rangeable_type(None) is False


def test_is_collection_type() -> None:
    assert vref.is_collection_type(list) is True
    assert vref.is_collection_type(tuple) is True
    assert vref.is_collection_type(dict) is False


def test_is_slice_type() -> None:
    assert vref.is_slice_type(list) is True
    assert vref.is_slice_type(tuple) is False


def test_is_array_type() -> None:
    assert vref.is_array_type(tuple) is True
    assert vref.is_array_type(list) is False


def test_is_map_type() -> None:
    assert vref.is_map_type(dict) is True
    assert vref.is_map_type(list) is False


def test_implements_error() -> None:
    assert vref.implements_error(ValueError) is True
    assert vref.implements_error(int) is False
    assert vref.implements_error(None) is False


def test_implements_context() -> None:
    class ContextManager:
        def __enter__(self) -> ContextManager:
            return self

        def __exit__(self, *args: object) -> None:
            pass

    assert vref.implements_context(ContextManager) is True
    assert vref.implements_context(int) is False
    assert vref.implements_context(None) is False


# --- field helpers -------------------------------------------------------------


def test_has_field_dataclass() -> None:
    assert vref.has_field(User, "name") is True
    assert vref.has_field(User, "missing") is False


def test_has_field_plain_class() -> None:
    p = Profile("Alice")
    assert vref.has_field(p, "name") is True
    assert vref.has_field(Profile, "name") is False


def test_get_field_value() -> None:
    u = User(name="Alice", age=30)
    assert vref.get_field_value(u, "name") == "Alice"
    assert vref.get_field_value(u, "missing") is None


def test_set_field_value() -> None:
    u = User(name="Alice")
    vref.set_field_value(u, "name", "Bob")
    assert u.name == "Bob"


def test_get_public_field_names() -> None:
    names = vref.get_public_field_names(User)
    assert "name" in names
    assert "age" in names


def test_get_fields() -> None:
    names = vref.get_fields(User)
    assert "name" in names
    assert "age" in names


def test_get_fields_with_filter() -> None:
    names = vref.get_fields(User, lambda n: n == "name")
    assert names == ["name"]


def test_get_fields_value() -> None:
    u = User(name="Alice", age=30)
    values = vref.get_fields_value(u)
    assert "Alice" in values
    assert 30 in values


def test_field_aliases_and_direct_fields() -> None:
    user = TaggedUser("alice", 30, "x")

    assert vref.has_field(TaggedUser, "name")
    assert vref.get_field(TaggedUser, "user_name") == "name"
    assert vref.get_field(TaggedUser, "user_age") == "age"
    assert vref.get_field(TaggedUser, "ignored_xml") == "ignored"
    assert vref.get_field(TaggedUser, "missing") is None
    assert vref.get_field_map(TaggedUser) == {"name": "name", "age": "age", "ignored": "ignored"}
    assert vref.get_field_name("name") == "name"
    assert vref.get_fields_directly(Child, with_embedded_fields=True) == ["base", "child"]
    assert vref.get_static_field_value(user) is user
    assert vref.get_field_value_with_options(user, "name") == "alice"
    assert vref.get_fields_value_with_options(user, lambda name: name != "ignored") == ["alice", 30]
    vref.set_field_value_with_options(user, "name", "bob")
    assert user.name == "bob"


def test_field_helpers_for_plain_objects_and_missing_aliases() -> None:
    profile = Profile("Alice")
    assert vref.get_public_field_names(profile) == []
    assert vref.get_fields(profile) == []
    assert vref.get_fields_value(profile) == []
    assert vref.get_field(Profile, "name") is None
    assert vref.get_field_map(Profile) == {}
    assert vref.get_fields_directly(Profile, with_embedded_fields=True) == []


def test_type_predicate_edge_cases() -> None:
    assert not vref.is_rangeable_type("list")
    assert not vref.is_collection_type("list")
    assert vref.is_func_type(type(str.upper)) is False


# --- method helpers ------------------------------------------------------------


def test_get_public_method_names() -> None:
    names = vref.get_public_method_names(User(name="Alice"))
    assert "greet" in names
    assert "get_name" in names


def test_get_public_methods() -> None:
    methods = vref.get_public_methods(User(name="Alice"))
    method_names = [n for n, _ in methods]
    assert "greet" in method_names


def test_get_method() -> None:
    result = vref.get_method(User(name="Alice"), "greet")
    assert result is not None
    name, _ = result
    assert name == "greet"


def test_get_method_missing() -> None:
    assert vref.get_method(User(name="Alice"), "nonexistent") is None


def test_get_method_by_name_ignore_case() -> None:
    result = vref.get_method_by_name_ignore_case(User(name="Alice"), "GREET")
    assert result is not None
    name, _ = result
    assert name == "greet"


def test_get_method_names() -> None:
    names = vref.get_method_names(User(name="Alice"))
    assert "greet" in names


def test_get_methods() -> None:
    methods = vref.get_methods(User(name="Alice"))
    method_names = [n for n, _ in methods]
    assert "greet" in method_names


def test_get_methods_with_filter() -> None:
    methods = vref.get_methods(User(name="Alice"), lambda n: n == "greet")
    names = [n for n, _ in methods]
    assert names == ["greet"]


def test_public_method_variants_and_direct_methods() -> None:
    user = User("Alice")
    greet_param = tuple(inspect.signature(user.greet).parameters.values())[0]

    assert vref.get_public_method(user, "greet") is not None
    assert vref.get_public_method(user, "greet", greet_param) is not None
    assert vref.get_public_method(user, "missing") is None
    assert vref.get_method_of_obj(user, "greet", "hello") is None
    assert vref.get_method_ignore_case(user, "GREET") is not None
    assert vref.get_method_ignore_case(user, "GREET", greet_param) is not None
    assert vref.get_method_ignore_case(user, "GREET", str) is None
    assert vref.get_method_by_name(user, "greet") is not None
    direct = vref.get_methods_directly(user)
    assert any(name == "greet" for name, _ in direct)
    with_supers = vref.get_methods_directly(user, with_supers=True, with_method_from_object=True)
    assert len(with_supers) >= len(direct)


def test_signature_fallbacks_and_method_name_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(inspect, "signature", lambda method: (_ for _ in ()).throw(ValueError()))

    assert vref.is_empty_param(lambda: None) is False
    assert vref.get_public_method(User("Alice"), "greet", str) is None
    assert vref.get_method_ignore_case(User("Alice"), "greet", str) is None


def test_is_equals_method() -> None:
    assert vref.is_equals_method("equals") is True
    assert vref.is_equals_method("equal") is True
    assert vref.is_equals_method("greet") is False


def test_is_hash_code_method() -> None:
    assert vref.is_hash_code_method("hash_code") is True
    assert vref.is_hash_code_method("hashCode") is False


def test_is_to_string_method() -> None:
    assert vref.is_to_string_method("to_string") is True
    assert vref.is_to_string_method("__str__") is True
    assert vref.is_to_string_method("string") is True


def test_is_empty_param() -> None:
    assert vref.is_empty_param(lambda: None) is True
    assert vref.is_empty_param(lambda x: x) is False


def test_is_getter_or_setter() -> None:
    assert vref.is_getter_or_setter("get_name") is True
    assert vref.is_getter_or_setter("set_name") is True
    assert vref.is_getter_or_setter("is_active") is True
    assert vref.is_getter_or_setter("greet") is False


def test_is_getter_or_setter_ignore_case() -> None:
    assert vref.is_getter_or_setter_ignore_case("GET_NAME") is True


# --- invocation ----------------------------------------------------------------


def test_invoke() -> None:
    result = vref.invoke(User(name="Alice"), "greet", "hello")
    assert result == "hello, Alice"


def test_invoke_method_not_found() -> None:
    with pytest.raises(KniferError) as exc:
        vref.invoke(User(name="Alice"), "nonexistent")
    assert "not found" in str(exc.value)


def test_invoke_func() -> None:
    result = vref.invoke_func(lambda a, b: a + b, 2, 3)
    assert result == 5


def test_invoke_static_raw_method_and_checked_errors() -> None:
    user = User("Alice")
    method = vref.get_method(user, "greet")
    assert method is not None

    assert vref.invoke_static(lambda a, b: a + b, 1, 2) == 3
    assert vref.invoke_raw(lambda value: value.upper(), "x") == "X"
    assert vref.invoke_method(user, method, "hi") == "hi, Alice"
    assert vref.invoke_with_check(user, method, "hello") == "hello, Alice"
    with pytest.raises(KniferError) as exc_info:
        vref.invoke_with_check(user, method)
    assert exc_info.value.code == "knifer.ref.invoke_failed"


def test_invoke_missing_and_failing_function_paths() -> None:
    with pytest.raises(TypeError):
        vref.invoke_func(
            lambda value: value,
        )
    with pytest.raises(TypeError):
        vref.invoke_static(lambda value: value)


def test_new_instance_dataclass() -> None:
    result = vref.new_instance(User(name="Alice"))
    assert isinstance(result, User)
    assert result.name == "Alice"


def test_new_instance_callable() -> None:
    result = vref.new_instance(lambda: 42)
    assert result == 42


def test_new_instance_type_and_error_paths() -> None:
    assert isinstance(vref.new_instance(Profile, "Alice"), Profile)
    with pytest.raises(KniferError) as exc_info:
        vref.new_instance(42)
    assert exc_info.value.code == "knifer.ref.new_instance"


def test_new_instance_copy_failure_returns_knifer_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class Copyable:
        pass

    monkeypatch.setattr(
        refx.copy, "copy", lambda _obj: (_ for _ in ()).throw(RuntimeError("copy failed"))
    )
    with pytest.raises(KniferError) as exc_info:
        vref.new_instance(Copyable())
    assert exc_info.value.code == "knifer.ref.new_instance"


def test_new_instance_if_possible() -> None:
    result = vref.new_instance_if_possible(User(name="Alice"))
    assert result is not None


def test_new_instance_if_possible_returns_none_for_non_type() -> None:
    assert vref.new_instance_if_possible("hello") is None


def test_set_accessible() -> None:
    obj = User(name="Alice")
    assert vref.set_accessible(obj) is obj


def test_remove_final_modify() -> None:
    vref.remove_final_modify(User(name="Alice"))
