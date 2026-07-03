from __future__ import annotations

from pathlib import Path

import pytest

from kniferpy import vconf
from kniferpy.verr import ValidationError


def test_parse_default_group() -> None:
    conf = vconf.parse("name = knifer\nport = 8080\n")
    assert conf.get("name") == "knifer"
    assert conf.get("port") == "8080"


def test_parse_colon_separator() -> None:
    conf = vconf.parse("host: localhost")
    assert conf.get("host") == "localhost"


def test_parse_ignores_comments_and_blank_lines() -> None:
    conf = vconf.parse("# a comment\n; another\n\nname = value\n")
    assert conf.keys() == ["name"]


def test_parse_strips_quotes() -> None:
    conf = vconf.parse("a = \"quoted\"\nb = 'single'\n")
    assert conf.get("a") == "quoted"
    assert conf.get("b") == "single"


def test_parse_sections() -> None:
    conf = vconf.parse("[db]\nhost = localhost\nport = 5432\n[cache]\nttl = 60\n")
    assert conf.get_by_group("db", "host") == "localhost"
    assert conf.get_by_group("cache", "ttl") == "60"
    assert "db" in conf.groups()
    assert "cache" in conf.groups()


def test_parse_invalid_line_raises() -> None:
    with pytest.raises(ValidationError):
        vconf.parse("this line has no separator")


def test_parse_empty_key_raises() -> None:
    with pytest.raises(ValidationError):
        vconf.parse("= value")


def test_parse_empty_section_group_exists() -> None:
    conf = vconf.parse("[empty]\n")
    assert "empty" in conf.groups()
    assert conf.keys("empty") == []


def test_get_or_default() -> None:
    conf = vconf.parse("present = yes")
    assert conf.get_or_default("present", "fallback") == "yes"
    assert conf.get_or_default("absent", "fallback") == "fallback"


def test_get_int() -> None:
    conf = vconf.parse("count = 42\nbad = notanumber")
    assert conf.get_int("count", 0) == 42
    assert conf.get_int("bad", 7) == 7
    assert conf.get_int("missing", 9) == 9


def test_get_float() -> None:
    conf = vconf.parse("ratio = 1.5\nbad = x")
    assert conf.get_float("ratio", 0.0) == 1.5
    assert conf.get_float("bad", 2.5) == 2.5
    assert conf.get_float("missing", 3.5) == 3.5


def test_get_bool() -> None:
    conf = vconf.parse("on = true\noff = false\nbad = maybe")
    assert conf.get_bool("on", False) is True
    assert conf.get_bool("off", True) is False
    assert conf.get_bool("bad", True) is True
    assert conf.get_bool("missing", True) is True


def test_get_list() -> None:
    conf = vconf.parse("hosts = a, b ,c\nempty = ")
    assert conf.get_list("hosts") == ["a", "b", "c"]
    assert conf.get_list("empty") == []
    assert conf.get_list("missing") == []


def test_typed_getters_by_group() -> None:
    conf = vconf.parse("[db]\nport = 5432\ndebug = true\n")
    assert conf.get_int("port", 0, group="db") == 5432
    assert conf.get_bool("debug", False, group="db") is True


def test_set_and_delete() -> None:
    conf = vconf.new()
    conf.set("a", "1")
    conf.set_by_group("grp", "b", "2")
    assert conf.get("a") == "1"
    assert conf.get_by_group("grp", "b") == "2"
    conf.delete("a")
    assert conf.get("a") == ""
    conf.delete_by_group("grp", "b")
    assert conf.get_by_group("grp", "b") == ""


def test_keys_and_groups_sorted() -> None:
    conf = vconf.parse("b = 2\na = 1\n[z]\nx = 1\n")
    assert conf.keys() == ["a", "b"]
    assert conf.groups() == ["", "z"]


def test_to_dict_is_deep_copy() -> None:
    conf = vconf.parse("a = 1")
    snapshot = conf.to_dict()
    snapshot[""]["a"] = "mutated"
    assert conf.get("a") == "1"


def test_clone_is_independent() -> None:
    conf = vconf.parse("a = 1")
    clone = conf.clone()
    clone.set("a", "2")
    assert conf.get("a") == "1"
    assert clone.get("a") == "2"


def test_lookup_reports_presence() -> None:
    conf = vconf.parse("a = 1")
    assert conf.lookup("", "a") == ("1", True)
    assert conf.lookup("", "missing") == ("", False)
    assert conf.lookup("nogroup", "a") == ("", False)


def test_expand_simple_reference() -> None:
    conf = vconf.parse("base = /opt\nfull = ${base}/app\n")
    assert conf.get_expanded("full") == "/opt/app"


def test_expand_group_reference() -> None:
    conf = vconf.parse("[paths]\nroot = /srv\nlog = ${paths.root}/log\n")
    assert conf.get_expanded("log", group="paths") == "/srv/log"


def test_expand_with_default_when_missing() -> None:
    conf = vconf.parse("value = ${absent:fallback}")
    assert conf.get_expanded("value") == "fallback"


def test_expand_env_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIFER_CONF_TEST", "from-env")
    conf = vconf.parse("value = ${ENV:KNIFER_CONF_TEST}")
    assert conf.get_expanded("value") == "from-env"


def test_expand_handles_self_reference_cycle() -> None:
    conf = vconf.parse("a = ${a}")
    # A direct cycle resolves to empty rather than recursing forever.
    assert conf.get_expanded("a") == ""


def test_expand_returns_full_copy() -> None:
    conf = vconf.parse("base = x\nfull = ${base}-y\n")
    expanded = conf.expand()
    assert expanded.get("full") == "x-y"
    assert conf.get("full") == "${base}-y"


def test_apply_profile_default_group() -> None:
    conf = vconf.parse("name = base\n[profile.test]\nname = test\n")
    applied = conf.apply_profile("test")
    assert applied.get("name") == "test"


def test_apply_profile_named_group() -> None:
    conf = vconf.parse(
        "name = base\n[server]\nport = 8080\n[profile.dev.server]\nport = 9090\n"
    )
    dev = conf.apply_profile("dev")
    assert dev.get("name") == "base"
    assert dev.get_by_group("server", "port") == "9090"


def test_apply_profile_empty_returns_base_only() -> None:
    conf = vconf.parse("name = base\n[profile.dev]\nname = dev\n")
    applied = conf.apply_profile("")
    # An empty profile performs no overlay: the base value is unchanged and the
    # untouched profile groups are copied through verbatim (matches knifer-go).
    assert applied.get("name") == "base"
    assert "profile.dev" in applied.groups()


def test_merge_later_overrides_earlier() -> None:
    a = vconf.parse("x = 1\ny = 1\n")
    b = vconf.parse("y = 2\nz = 3\n")
    merged = vconf.merge(a, b)
    assert merged.get("x") == "1"
    assert merged.get("y") == "2"
    assert merged.get("z") == "3"


def test_merge_method_mutates_receiver() -> None:
    a = vconf.parse("x = 1")
    b = vconf.parse("x = 2")
    a.merge(b)
    assert a.get("x") == "2"


def test_merge_none_is_noop() -> None:
    a = vconf.parse("x = 1")
    assert a.merge(None).get("x") == "1"


def test_parse_bytes() -> None:
    conf = vconf.parse_bytes(b"name = bytes\n")
    assert conf.get("name") == "bytes"


def test_load_file(tmp_path: Path) -> None:
    path = tmp_path / "app.properties"
    path.write_text("name = fromfile\nport = 9000\n", encoding="utf-8")
    conf = vconf.load(path)
    assert conf.get("name") == "fromfile"
    assert conf.get_int("port", 0) == 9000


def test_load_files_merges_in_order(tmp_path: Path) -> None:
    first = tmp_path / "base.properties"
    second = tmp_path / "override.properties"
    first.write_text("a = 1\nb = 1\n", encoding="utf-8")
    second.write_text("b = 2\n", encoding="utf-8")
    conf = vconf.load_files(first, second)
    assert conf.get("a") == "1"
    assert conf.get("b") == "2"


def test_load_profile_from_file(tmp_path: Path) -> None:
    path = tmp_path / "app.properties"
    path.write_text("name = base\n[profile.test]\nname = test\n", encoding="utf-8")
    conf = vconf.load_profile(path, "test")
    assert conf.get("name") == "test"
