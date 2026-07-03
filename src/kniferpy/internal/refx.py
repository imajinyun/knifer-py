"""Reflection and introspection helpers.

Ports knifer-go's internal/ref with Python-idiomatic mappings:

- Go reflect.Type / reflect.Value -> type(), inspect members
- Go struct tags (ref/json/xml) -> dataclass annotations
- Go typed nil / IsNil -> Python's is None (not re-exported)
- Go unsafe access / unexported fields -> not applicable (omitted)

Errors use kniferpy.verr types with codes knifer.ref.<reason>.
"""

from __future__ import annotations

import copy
import dataclasses
import inspect
import types
from collections.abc import Callable, Iterable
from typing import Any

from kniferpy.verr import KniferError

# --- filter types --------------------------------------------------------------

FieldFilter = Callable[[str], bool]
MethodFilter = Callable[[str], bool]

# --- type predicates (values) --------------------------------------------------


def is_function(obj: Any) -> bool:
    return callable(obj)


def is_iterable(obj: Any) -> bool:
    return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray))


def is_collection(obj: Any) -> bool:
    return isinstance(obj, (list, tuple))


def is_slice(obj: Any) -> bool:
    return isinstance(obj, list)


def is_array(obj: Any) -> bool:
    return isinstance(obj, tuple)


def is_map(obj: Any) -> bool:
    return isinstance(obj, dict)


# --- type predicates (types) ---------------------------------------------------


def is_func_type(typ: Any) -> bool:
    return typ in (types.FunctionType, types.BuiltinFunctionType, types.MethodType)


def is_rangeable_type(typ: Any) -> bool:
    if typ is None:
        return False
    if not isinstance(typ, type):
        return False
    return issubclass(typ, (list, tuple, dict, set, frozenset))


def is_collection_type(typ: Any) -> bool:
    if typ is None:
        return False
    if not isinstance(typ, type):
        return False
    return issubclass(typ, (list, tuple))


def is_slice_type(typ: Any) -> bool:
    return typ is list


def is_array_type(typ: Any) -> bool:
    return typ is tuple


def is_map_type(typ: Any) -> bool:
    return typ is dict


def implements_error(typ: Any) -> bool:
    if typ is None:
        return False
    return isinstance(typ, type) and issubclass(typ, Exception)


def implements_context(typ: Any) -> bool:
    if typ is None:
        return False
    return hasattr(typ, "__enter__") and hasattr(typ, "__exit__")


# --- field helpers -------------------------------------------------------------


def has_field(target: Any, name: str) -> bool:
    if dataclasses.is_dataclass(target):
        return any(f.name == name for f in dataclasses.fields(target))
    if isinstance(target, type):
        return name in getattr(target, "__annotations__", {})
    return hasattr(target, name)


def get_field_value(obj: Any, field_name: str) -> Any:
    return getattr(obj, field_name, None)


def set_field_value(obj: Any, field_name: str, value: Any) -> None:
    setattr(obj, field_name, value)


def get_public_field_names(target: Any) -> list[str]:
    return [f for f in _collect_field_names(target) if not f.startswith("_")]


def get_fields(target: Any, *filters: FieldFilter) -> list[str]:
    names = _collect_field_names(target)
    if filters and filters[0] is not None:
        names = [n for n in names if filters[0](n)]
    return names


def get_fields_value(obj: Any, *filters: FieldFilter) -> list[Any]:
    names = get_fields(obj, *filters)
    return [getattr(obj, n, None) for n in names]


def _collect_field_names(target: Any) -> list[str]:
    if dataclasses.is_dataclass(target):
        return [f.name for f in dataclasses.fields(target)]
    if isinstance(target, type):
        return list(getattr(target, "__annotations__", {}))
    return list(getattr(type(target), "__annotations__", {}))


# --- method helpers ------------------------------------------------------------


def get_public_method_names(target: Any) -> list[str]:
    names = [n for n, _ in _collect_methods(target) if not n.startswith("_")]
    names.sort()
    return names


def get_public_methods(target: Any, *filters: MethodFilter) -> list[tuple[str, Callable[..., Any]]]:
    methods = [(n, m) for n, m in _collect_methods(target) if not n.startswith("_")]
    if filters and filters[0] is not None:
        methods = [(n, m) for n, m in methods if filters[0](n)]
    return methods


def get_method(target: Any, method_name: str) -> tuple[str, Callable[..., Any]] | None:
    for name, method in _collect_methods(target):
        if name == method_name:
            return (name, method)
    return None


def get_method_by_name(target: Any, method_name: str) -> tuple[str, Callable[..., Any]] | None:
    return get_method(target, method_name)


def get_method_by_name_ignore_case(
    target: Any, method_name: str
) -> tuple[str, Callable[..., Any]] | None:
    lower = method_name.lower()
    for name, method in _collect_methods(target):
        if name.lower() == lower:
            return (name, method)
    return None


def get_method_names(target: Any) -> list[str]:
    names = [n for n, _ in _collect_methods(target)]
    names.sort()
    return names


def get_methods(target: Any, *filters: MethodFilter) -> list[tuple[str, Callable[..., Any]]]:
    methods = list(_collect_methods(target))
    if filters and filters[0] is not None:
        methods = [(n, m) for n, m in methods if filters[0](n)]
    return methods


def is_equals_method(method_name: str) -> bool:
    return method_name.lower() in ("equal", "equals")


def is_hash_code_method(method_name: str) -> bool:
    return method_name.lower() == "hash_code"


def is_to_string_method(method_name: str) -> bool:
    return method_name.lower() in ("string", "to_string", "__str__")


def is_empty_param(method: Callable[..., Any]) -> bool:
    try:
        sig = inspect.signature(method)
        return len(sig.parameters) == 0
    except (ValueError, TypeError):
        return False


def is_getter_or_setter_ignore_case(method_name: str) -> bool:
    return is_getter_or_setter(method_name, ignore_case=True)


def is_getter_or_setter(method_name: str, ignore_case: bool = False) -> bool:
    name = method_name.lower() if ignore_case else method_name
    return name.startswith(("get", "set", "is"))


def _collect_methods(target: Any) -> list[tuple[str, Callable[..., Any]]]:
    return [(n, m) for n, m in inspect.getmembers(target, callable) if not n.startswith("_")]


# --- invocation ----------------------------------------------------------------


def invoke(obj: Any, method_name: str, *args: Any) -> Any:
    method = getattr(obj, method_name, None)
    if method is None:
        raise KniferError(
            message=f"method {method_name!r} not found", code="knifer.ref.method_not_found"
        )
    return method(*args)


def invoke_func(fn: Callable[..., Any], *args: Any) -> Any:
    return fn(*args)


def new_instance(target: Any, *args: Any) -> Any:
    if callable(target):
        return target(*args)
    if hasattr(target, "__dict__") or hasattr(type(target), "__slots__"):
        try:
            return copy.copy(target)
        except Exception:
            raise KniferError(
                message="cannot create instance", code="knifer.ref.new_instance"
            ) from None
    raise KniferError(message="cannot create instance", code="knifer.ref.new_instance")


def new_instance_if_possible(target: Any) -> Any:
    try:
        return new_instance(target)
    except KniferError:
        return None


# --- no-op compatibility -------------------------------------------------------


def set_accessible(obj: Any) -> Any:
    return obj


def remove_final_modify(obj: Any) -> None:
    pass
