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


def test_parse_obj_rejects_array() -> None:
    try:
        vjson.parse_obj("[1, 2]")
    except DecodeError as err:
        assert err.code == "json.not_object"
    else:
        raise AssertionError("expected DecodeError")


def test_dumps_pretty_is_stable() -> None:
    assert vjson.dumps_pretty({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}'


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


def test_read_write_json_file(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data.json"

    vjson.write(path, {"b": 2, "a": 1})

    assert vjson.read_obj(path) == {"a": 1, "b": 2}


def test_read_json_file_reuses_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('{"ok": true}', encoding="utf-8")

    try:
        vjson.read(path, max_bytes=3)
    except SecurityError as err:
        assert err.code == "file.too_large"
    else:
        raise AssertionError("expected file.too_large")
