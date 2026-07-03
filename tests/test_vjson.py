import pytest
from pathlib import Path

from kniferpy import vjson
from kniferpy.verr import DecodeError, SecurityError


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
    with pytest.raises(DecodeError) as exc_info:
        vjson.parse_obj("[1, 2]")
    assert exc_info.value.code == "json.not_object"


def test_parse_obj_rejects_invalid_json() -> None:
    with pytest.raises(DecodeError) as exc_info:
        vjson.parse_obj("{bad")
    assert exc_info.value.code == "json.invalid"


def test_dumps_pretty_is_stable() -> None:
    assert vjson.dumps_pretty({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}'


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
    assert vjson.is_valid('{"ok": true}')
    assert not vjson.is_valid("{bad")


def test_is_valid_bytes() -> None:
    assert vjson.is_valid(b'{"ok": true}')
    assert not vjson.is_valid(b"{bad")


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
    with pytest.raises(DecodeError) as exc_info:
        vjson.read_obj(path)
    assert exc_info.value.code == "json.not_object"


def test_write_compact(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    vjson.write(path, {"a": 1}, pretty=False)
    content = path.read_text(encoding="utf-8")
    assert content == '{"a":1}'