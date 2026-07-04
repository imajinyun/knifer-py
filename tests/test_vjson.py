import pytest
from pathlib import Path

from kniferpy import vjson
from kniferpy.verr import DecodeError, JSONError, SecurityError


def test_parse_obj_and_get_path() -> None:
    obj = vjson.parse_obj('{"user":{"name":"kniferpy","roles":["dev"]}}')

    assert vjson.get_path(obj, "user.name") == "kniferpy"
    assert vjson.get_path(obj, "user.roles.0") == "dev"
    assert vjson.get_path(obj, "missing", default="fallback") == "fallback"
    assert vjson.get_str(obj, "user.name") == "kniferpy"
    assert vjson.get_str(obj, "user.roles", default="fallback") == "fallback"


def test_get_path_nested_dict() -> None:
    obj = {"a": {"b": {"c": 42}}}
    assert vjson.get_path(obj, "a.b.c") == 42


def test_get_path_list_index_out_of_range() -> None:
    obj = {"items": [1, 2]}
    assert vjson.get_path(obj, "items.5", default=None) is None


def test_get_path_non_digit_list_index() -> None:
    obj = {"items": [1, 2]}
    assert vjson.get_path(obj, "items.abc", default=None) is None


def test_get_path_non_dict_non_list() -> None:
    assert vjson.get_path(42, "a.b", default=None) is None


def test_get_int_rejects_bool() -> None:
    assert vjson.get_int({"ok": True}, "ok", default=0) == 0


def test_get_float_from_int() -> None:
    assert vjson.get_float({"count": 3}, "count") == 3.0


def test_get_float_rejects_bool() -> None:
    assert vjson.get_float({"ok": True}, "ok", default=0.0) == 0.0


def test_get_bool_default() -> None:
    assert vjson.get_bool({"ok": True}, "ok") is True
    assert vjson.get_bool({"ok": False}, "ok") is False
    assert vjson.get_bool({"ok": 1}, "ok", default=False) is False


def test_get_list_default() -> None:
    assert vjson.get_list({"arr": [1, 2]}, "arr") == [1, 2]
    assert vjson.get_list({"arr": "not_list"}, "arr", default=[]) == []


def test_get_dict_default() -> None:
    assert vjson.get_dict({"obj": {"k": "v"}}, "obj") == {"k": "v"}
    assert vjson.get_dict({"obj": "not_dict"}, "obj", default={}) == {}


def test_parse_obj_rejects_array() -> None:
    with pytest.raises(JSONError) as exc_info:
        vjson.parse_obj("[1, 2]")
    assert exc_info.value.code == "json.not_object"


def test_parse_obj_rejects_invalid_json() -> None:
    with pytest.raises(JSONError) as exc_info:
        vjson.parse_obj("{bad")
    assert exc_info.value.code == "json.invalid"


def test_dumps_pretty_is_stable() -> None:
    assert vjson.to_json_str({"b": 2, "a": 1}, pretty=True) == '{\n  "a": 1,\n  "b": 2\n}'


def test_dumps_compact() -> None:
    assert vjson.dumps({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_dumps_unicode() -> None:
    assert vjson.dumps({"k": "你好"}) == '{"k":"你好"}'


def test_typed_getters_and_validity() -> None:
    obj = {"ok": True, "count": 3, "ratio": 1.5, "name": "kniferpy", "items": [1], "meta": {}}

    assert vjson.get_bool(obj, "ok") is True
    assert vjson.get_int(obj, "count") == 3
    assert vjson.get_int(obj, "ok", default=0) == 0
    assert vjson.get_float(obj, "ratio") == 1.5
    assert vjson.get_float(obj, "count") == 3.0
    assert vjson.get_list(obj, "items") == [1]
    assert vjson.get_dict(obj, "meta") == {}
    assert vjson.has_path(obj, "meta")
    assert not vjson.has_path(obj, "missing")
    assert vjson.is_json('{"ok": true}')
    assert not vjson.is_json("{bad")


def test_is_valid_bytes() -> None:
    assert vjson.is_json(b'{"ok": true}')
    assert not vjson.is_json(b"{bad")


def test_read_write_json_file(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data.json"

    vjson.write(path, {"b": 2, "a": 1})

    assert vjson.read_obj(path) == {"a": 1, "b": 2}


def test_read_json_file_reuses_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('{"ok": true}', encoding="utf-8")

    with pytest.raises(SecurityError) as exc_info:
        vjson.read(path, max_bytes=3)
    assert exc_info.value.code == "file.too_large"


def test_read_json_file_list(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('[1, 2, 3]', encoding="utf-8")
    assert vjson.read(path) == [1, 2, 3]


def test_read_obj_rejects_list(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('[1, 2, 3]', encoding="utf-8")
    with pytest.raises(JSONError) as exc_info:
        vjson.read_obj(path)
    assert exc_info.value.code == "json.not_object"


def test_write_compact(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    vjson.write(path, {"a": 1}, pretty=False)
    content = path.read_text(encoding="utf-8")
    assert content == '{"a":1}'


# ========== JSONObject ==========


def test_json_object_basic() -> None:
    obj = vjson.new_json_object()
    obj.set("name", "kniferpy")
    obj.set("version", 1)
    assert obj.len() == 2
    assert obj.has("name") is True
    assert obj.has("missing") is False
    assert obj.get_string("name") == "kniferpy"
    assert obj.get_int("version") == 1
    assert obj.keys() == ["name", "version"]


def test_json_object_remove() -> None:
    obj = vjson.new_json_object()
    obj.set("a", 1).set("b", 2)
    assert obj.remove("a") is True
    assert obj.remove("missing") is False
    assert obj.len() == 1
    assert obj.has("a") is False


def test_json_object_to_map() -> None:
    obj = vjson.new_json_object()
    obj.set("k", "v")
    assert obj.to_map() == {"k": "v"}


def test_json_object_get_or_default() -> None:
    obj = vjson.new_json_object()
    obj.set("x", "hello")
    assert obj.get_or_default("x", "fallback") == "hello"
    assert obj.get_or_default("missing", "fallback") == "fallback"


def test_json_object_typed_getters() -> None:
    obj = vjson.new_json_object()
    obj.set("str", "hi").set("num", 42).set("pi", 3.14).set("ok", True)
    assert obj.get_string("str") == "hi"
    assert obj.get_string_or("str", "x") == "hi"
    assert obj.get_string_or("missing", "x") == "x"
    assert obj.get_int("num") == 42
    assert obj.get_int_or("num", 0) == 42
    assert obj.get_int_or("missing", 99) == 99
    assert obj.get_float64("pi") == 3.14
    assert obj.get_float64_or("pi", 0.0) == 3.14
    assert obj.get_bool("ok") is True
    assert obj.get_bool_or("ok", False) is True
    assert obj.get_bool_or("missing", False) is False


def test_json_object_for_each() -> None:
    obj = vjson.new_json_object()
    obj.set("a", 1).set("b", 2)
    items: list[tuple[str, object]] = []
    obj.for_each(lambda k, v: items.append((k, v)) or True)
    assert len(items) == 2


def test_json_object_null() -> None:
    obj = vjson.new_json_object()
    obj.set("none", None)
    assert obj.is_null("none") is True
    assert obj.is_null("missing") is False


def test_json_object_to_string() -> None:
    obj = vjson.new_json_object()
    obj.set("x", 1)
    s = obj.to_string()
    assert '"x":1' in s


def test_json_object_get_by_path() -> None:
    obj = vjson.new_json_object()
    obj.set("user", {"name": "kniferpy"})
    assert obj.get_by_path("user.name") == "kniferpy"


# ========== JSONArray ==========


def test_json_array_basic() -> None:
    arr = vjson.new_json_array()
    arr.add("a").add("b").add("c")
    assert arr.len() == 3
    assert arr.get_string(0) == "a"
    assert arr.get_string(1) == "b"
    v, ok = arr.get(0)
    assert v == "a"
    assert ok is True


def test_json_array_get_or_default() -> None:
    arr = vjson.new_json_array()
    arr.add("x")
    assert arr.get_or_default(0, "fallback") == "x"
    assert arr.get_or_default(99, "fallback") == "fallback"


def test_json_array_remove() -> None:
    arr = vjson.new_json_array()
    arr.add("a").add("b")
    assert arr.remove(0) is True
    assert arr.len() == 1
    assert arr.remove(99) is False


def test_json_array_insert() -> None:
    arr = vjson.new_json_array()
    arr.add("a").add("c")
    arr.insert(1, "b")
    assert arr.to_slice() == ["a", "b", "c"]


def test_json_array_set() -> None:
    arr = vjson.new_json_array()
    arr.add("a").add("b")
    arr.set(0, "x")
    assert arr.get_string(0) == "x"


def test_json_array_range() -> None:
    arr = vjson.new_json_array()
    arr.add(1).add(2).add(3)
    items: list[int] = []
    arr.range(lambda i, v: items.append(v) or True)
    assert items == [1, 2, 3]


def test_json_array_join() -> None:
    arr = vjson.new_json_array()
    arr.add("a").add("b").add("c")
    assert arr.join(",") == "a,b,c"


def test_json_array_add_all() -> None:
    arr = vjson.new_json_array()
    arr.add_all("a", "b", "c")
    assert arr.len() == 3


def test_json_array_typed_getters() -> None:
    arr = vjson.new_json_array()
    arr.add("hi").add(42).add(3.14).add(True)
    assert arr.get_string(0) == "hi"
    assert arr.get_string_or(0, "x") == "hi"
    assert arr.get_int(1) == 42
    assert arr.get_int64_or(1, 0) == 42
    assert arr.get_float64(2) == 3.14
    assert arr.get_bool(3) is True
    assert arr.get_bool_or(3, False) is True


def test_json_array_to_string() -> None:
    arr = vjson.new_json_array()
    arr.add(1).add(2)
    assert "[1,2]" in arr.to_string() or "[1, 2]" in arr.to_string()


# ========== is_null ==========


def test_is_null() -> None:
    assert vjson.is_null(None) is True
    assert vjson.is_null(vjson.Null) is True
    assert vjson.is_null("") is False
    assert vjson.is_null(0) is False


# ========== is_json_obj / is_json_array ==========


def test_is_json_obj() -> None:
    assert vjson.is_json_obj('{"a":1}') is True
    assert vjson.is_json_obj("[1]") is False
    assert vjson.is_json_obj("bad") is False


def test_is_json_array() -> None:
    assert vjson.is_json_array("[1]") is True
    assert vjson.is_json_array('{"a":1}') is False
    assert vjson.is_json_array("bad") is False


# ========== format_json_str ==========


def test_format_json_str() -> None:
    assert vjson.format_json_str('{"b":2,"a":1}') == '{\n  "a": 1,\n  "b": 2\n}'


def test_format_json_str_invalid() -> None:
    assert vjson.format_json_str("bad") == "bad"


# ========== quote ==========


def test_quote() -> None:
    assert vjson.quote("hello") == '"hello"'
    assert vjson.quote('say "hi"') == '"say \\"hi\\""'


# ========== put_by_path ==========


def test_put_by_path() -> None:
    obj = {"a": {"b": 1}}
    vjson.put_by_path(obj, "a.c", 2)
    assert obj["a"]["c"] == 2


def test_put_by_path_new_nested() -> None:
    obj: dict[str, object] = {}
    vjson.put_by_path(obj, "x.y.z", 42)
    assert obj["x"]["y"]["z"] == 42


# ========== Config ==========


def test_config_ignore_case() -> None:
    cfg = vjson.new_config(ignore_case=True)
    obj = vjson.new_json_object(cfg)
    obj.set("Name", "kniferpy")
    assert obj.has("name") is True
    assert obj.get_string("name") == "kniferpy"


def test_config_clone() -> None:
    cfg = vjson.new_config(ignore_null_value=True)
    cloned = cfg.clone()
    assert cloned.ignore_null_value is True


# ========== to_bean ==========


def test_to_bean() -> None:
    from dataclasses import dataclass

    @dataclass
    class User:
        name: str = ""
        age: int = 0

    d = {"name": "kniferpy", "age": 1}
    bean = vjson.to_bean(d, User)
    assert bean is not None
    assert bean.name == "kniferpy"
    assert bean.age == 1


def test_to_list() -> None:
    from dataclasses import dataclass

    @dataclass
    class Item:
        id: int = 0

    items = vjson.to_list([{"id": 1}, {"id": 2}], Item)
    assert len(items) == 2
    assert items[0].id == 1
    assert items[1].id == 2