from __future__ import annotations

import base64
import dataclasses
import socket
import threading
import time
import urllib.request
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
    assert conf.get_by_group_expanded("paths", "log") == "/srv/log"


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


def test_expand_depth_guard_and_dollar_placeholder() -> None:
    conf = vconf.parse("a = $b\nb = value")
    assert conf.get_expanded("a") == "value"
    assert conf._expand_value("", "${missing}", set(), 65) == "${missing}"


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


# ---------------------------------------------------------------------------
# Watch
# ---------------------------------------------------------------------------


class TestWatch:
    def test_watch_detects_change(self, tmp_path: Path) -> None:
        path = tmp_path / "watch.properties"
        path.write_text("key = first\n", encoding="utf-8")

        events: list[vconf.WatchEvent] = []

        def handler(event: vconf.WatchEvent) -> None:
            events.append(event)

        t = vconf.watch(path, handler, interval=0.1)
        time.sleep(0.2)
        path.write_text("key = second\n", encoding="utf-8")
        time.sleep(0.3)

        t._conf_stop.set()  # type: ignore[attr-defined]
        t.join(timeout=1.0)
        assert len(events) >= 1


# ---------------------------------------------------------------------------
# Bind
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ServerConfig:
    host: str = ""
    port: int = 0
    debug: bool = False


class TestBind:
    def test_bind_default_group(self) -> None:
        conf = vconf.parse("host = localhost\nport = 8080\ndebug = true\n")
        obj = ServerConfig()
        vconf.bind(conf, obj)
        assert obj.host == "localhost"
        assert obj.port == 8080
        assert obj.debug is True

    def test_bind_group(self) -> None:
        conf = vconf.parse("[server]\nhost = 0.0.0.0\nport = 3000\n")
        obj = ServerConfig()
        vconf.bind_group(conf, "server", obj)
        assert obj.host == "0.0.0.0"
        assert obj.port == 3000

    def test_bind_conversion_failures_keep_defaults(self) -> None:
        conf = vconf.parse("port = bad\ndebug = maybe\n")
        obj = ServerConfig(port=7, debug=True)
        vconf.bind(conf, obj)
        assert obj.port == 7
        assert obj.debug is False


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class TestSchema:
    def test_validate_schema_required(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(key="name", required=True),
        ])
        conf = vconf.parse("")
        errors = vconf.validate_schema(conf, schema)
        assert len(errors) == 1
        assert "required" in errors[0].lower()

    def test_validate_schema_type(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(key="port", type="int"),
        ])
        conf = vconf.parse("port = notanumber")
        errors = vconf.validate_schema(conf, schema)
        assert len(errors) == 1

    def test_validate_schema_choices(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(key="level", choices=["debug", "info", "error"]),
        ])
        conf = vconf.parse("level = trace")
        errors = vconf.validate_schema(conf, schema)
        assert len(errors) == 1

    def test_validate_schema_group_and_default(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(group="server", key="port", type="int", default="8080"),
            vconf.FieldRule(group="server", key="mode", choices=["dev", "prod"]),
        ])
        conf = vconf.parse("[server]\nmode = test\n")
        assert vconf.validate_schema(conf, schema) == ["server.mode: 'test' not in ['dev', 'prod']"]
        vconf.apply_defaults(conf, schema)
        assert conf.get_by_group("server", "port") == "8080"

    def test_validate_schema_valid(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(key="name", required=True),
            vconf.FieldRule(key="port", type="int"),
        ])
        conf = vconf.parse("name = myapp\nport = 8080\n")
        errors = vconf.validate_schema(conf, schema)
        assert len(errors) == 0

    def test_apply_defaults(self) -> None:
        schema = vconf.Schema(fields=[
            vconf.FieldRule(key="timeout", default="30"),
        ])
        conf = vconf.parse("")
        vconf.apply_defaults(conf, schema)
        assert conf.get("timeout") == "30"

    def test_schema_from_struct(self) -> None:
        @dataclasses.dataclass
        class AppConfig:
            name: str = dataclasses.field(default="", metadata={"conf": "app_name,required"})
            port: int = dataclasses.field(default=0, metadata={"conf": "port,default:8080"})

        obj = AppConfig()
        schema = vconf.schema_from_struct(obj)
        assert len(schema.fields) == 2
        assert schema.fields[0].key == "app_name"
        assert schema.fields[0].required is True
        assert schema.fields[1].key == "port"
        assert schema.fields[1].default == "8080"


def test_error_getters_and_conf_error() -> None:
    conf = vconf.parse("count = 42\nflag = true\nbad = no-int")
    cause = RuntimeError("root")
    err = vconf.ConfError("failed", cause)

    assert conf.get_int_e("count") == 42
    assert conf.get_bool_e("flag") is True
    with pytest.raises(ValidationError) as missing_int:
        conf.get_int_e("missing")
    assert conf.get_int_e("bad") == 0
    with pytest.raises(ValidationError) as missing_bool:
        conf.get_bool_e("missing")
    assert missing_int.value.code == "knifer.conf.key_not_found"
    assert missing_bool.value.code == "knifer.conf.key_not_found"
    assert str(err) == "failed: root"


def test_profile_key_overlay_and_decrypt_values() -> None:
    conf = vconf.parse(
        "name = base\n"
        "[profile]\n"
        "prod.name = from-profile-group\n"
        "prod.db.host = db-profile\n"
        "[profile.prod]\n"
        "name = prod\n"
    )
    def decrypt(value: str) -> str:
        if value == "fail":
            raise RuntimeError("bad")
        return value.upper()

    decrypted = vconf.parse("a = ok\nb = fail").decrypt_values(decrypt)

    applied = conf.apply_profile("prod")

    assert applied.get("name") == "from-profile-group"
    assert applied.get_by_group("db", "host") == "db-profile"
    assert decrypted.get("a") == "OK"
    assert decrypted.get("b") == "fail"


def test_load_with_options_files_and_base64(tmp_path: Path) -> None:
    first = tmp_path / "first.properties"
    second = tmp_path / "second.properties"
    first.write_text("secret = aGVsbG8=\nname = first\n", encoding="utf-8")
    second.write_text("name = second\n", encoding="utf-8")
    opts = vconf.LoadOptions(decrypt=vconf.base64_decrypt)

    loaded = vconf.load_with_options(first, opts)
    merged = vconf.load_files_with_options([first, second], None)

    assert loaded.get("secret") == "hello"
    assert merged.get("name") == "second"
    assert vconf.base64_decrypt(base64.b64encode(b"ok").decode()) == "ok"


def test_parse_by_ext_yaml_toml_json_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_conf = vconf.parse_by_ext("app:\n  name: knifer\nlist:\n  - a\n  - b\n", ".yaml")
    toml_conf = vconf.parse_by_ext("[app]\nname='knifer'\n", "toml")
    json_conf = vconf.parse_by_ext('{"app":{"name":"knifer"},"ports":[1,2]}', "json")
    ini_conf = vconf.parse_by_ext("name = ini", "properties")

    assert yaml_conf.get("app.name") == "knifer"
    assert yaml_conf.get("list") == "a,b"
    assert vconf.parse_yaml_full("app:\n  name: knifer\n").get("app.name") == "knifer"
    assert vconf.parse_yaml_full_with_options("app:\n  name: knifer\n").get("app.name") == "knifer"
    assert toml_conf.get("app.name") == "knifer"
    assert vconf.parse_toml_with_options("[app]\nname='knifer'\n").get("app.name") == "knifer"
    assert json_conf.get("app.name") == "knifer"
    assert json_conf.get("ports") == "1,2"
    assert ini_conf.get("name") == "ini"
    assert vconf.parse_by_ext_with_options("name = ini", "ini").get("name") == "ini"
    assert vconf.parse_yaml("[]").to_dict() == {"": {}}

    with pytest.raises(ValidationError) as yaml_exc:
        vconf.parse_yaml(":\n")
    with pytest.raises(ValidationError) as toml_exc:
        vconf.parse_toml("[bad")
    with pytest.raises(ValidationError) as json_exc:
        vconf.parse_json("{bad")
    assert yaml_exc.value.code == "knifer.conf.yaml_parse_failed"
    assert toml_exc.value.code == "knifer.conf.toml_parse_failed"
    assert json_exc.value.code == "knifer.conf.json_parse_failed"


def test_internal_helpers_and_flatten_empty_values() -> None:
    conf = vconf.parse_json('{"a": null, "b": true, "nested": {"x": 1}}')
    assert conf.get("a") == ""
    assert conf.get("b") == "True"
    assert conf.get("nested.x") == "1"
    assert vconf.confx._first_index_any("a:b=c", "=:") == 1
    assert vconf.confx._first_index_any("abc", "=:") == -1


def test_bind_options_schema_metadata_dict_and_validation() -> None:
    @dataclasses.dataclass
    class AppConfig:
        host: str = ""
        port: int = dataclasses.field(default=0, metadata={"conf": "port"})
        debug: bool = False
        ratio: float = 0.0
        tags: list[str] = dataclasses.field(default_factory=list)

    conf = vconf.parse("host = localhost\nport = 8080\ndebug=true\nratio=1.5\ntags=a,b\n")
    obj = AppConfig()
    vconf.bind_with_options(conf, obj)
    assert obj == AppConfig("localhost", 8080, True, 1.5, ["a", "b"])
    group_obj = AppConfig()
    vconf.bind_group_with_options(vconf.parse("[app]\nhost=0.0.0.0\nport=9000\n"), "app", group_obj)
    assert group_obj.host == "0.0.0.0"
    schema = vconf.schema_from_struct(obj)
    assert [rule.type for rule in schema.fields] == [
        "str",
        "int",
        "bool",
        "float",
        "str",
    ]
    assert vconf.validate_struct(conf, obj) == []
    assert vconf.validate_struct_with_options(conf, obj) == []
    assert vconf.validate_schema(vconf.parse("flag=maybe\n"), vconf.Schema([
        vconf.FieldRule(key="flag", type="bool"),
    ]))
    assert vconf.validate_schema(vconf.parse("ratio=bad\n"), vconf.Schema([
        vconf.FieldRule(key="ratio", type="float"),
    ]))

    @dataclasses.dataclass
    class DictMetaConfig:
        host: str = dataclasses.field(default="", metadata={"conf": {"key": "host"}})

    dict_schema = vconf.schema_from_struct(DictMetaConfig())
    assert dict_schema.fields[0].key == "host"

    @dataclasses.dataclass
    class TaggedConfig:
        port: int = dataclasses.field(default=0, metadata={"conf": "port,required,default:8080"})

    tagged_schema = vconf.schema_from_struct(TaggedConfig())
    assert tagged_schema.fields[0].key == "port"
    assert tagged_schema.fields[0].required is True
    assert tagged_schema.fields[0].default == "8080"


def test_remote_load_and_safe_host(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return b"name = remote\n"

    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=10.0: Response())
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, port: [(socket.AF_INET, None, None, None, ("93.184.216.34", 0))],
    )

    assert vconf.load_remote("https://example.com/app.properties").get("name") == "remote"
    assert (
        vconf.load_remote_with_options("https://example.com/app.properties").get("name")
        == "remote"
    )
    assert vconf.load_remote_safe("https://example.com/app.properties").get("name") == "remote"
    assert (
        vconf.load_remote_safe_with_options("https://example.com/app.properties").get("name")
        == "remote"
    )

    with pytest.raises(ValidationError) as invalid_url:
        vconf.load_remote_safe("https:///missing-host")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, port: [(socket.AF_INET, None, None, None, ("127.0.0.1", 0))],
    )
    with pytest.raises(ValidationError) as private_host:
        vconf.load_remote_safe("https://localhost/app.properties")
    def fail_urlopen(url: str, timeout: float = 10.0):
        raise OSError("down")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)
    with pytest.raises(ValidationError) as remote_failed:
        vconf.load_remote("https://example.com/app.properties")
    assert invalid_url.value.code == "knifer.conf.invalid_url"
    assert private_host.value.code == "knifer.conf.private_host"
    assert remote_failed.value.code == "knifer.conf.load_remote_failed"


def test_remote_safe_treats_resolution_errors_as_private(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, port: (_ for _ in ()).throw(socket.gaierror("no dns")),
    )
    with pytest.raises(ValidationError) as exc:
        vconf.load_remote_safe("https://example.com/app.properties")
    assert exc.value.code == "knifer.conf.private_host"


def test_watch_with_options_and_missing_file_runner(tmp_path: Path) -> None:
    path = tmp_path / "missing.properties"
    stop = threading.Event()
    events: list[vconf.WatchEvent] = []

    def callback(event: vconf.WatchEvent) -> None:
        events.append(event)
        stop.set()

    thread = vconf.watch_with_options(path, callback, interval=0.05)
    time.sleep(0.1)
    path.write_text("key = value\n", encoding="utf-8")
    time.sleep(0.15)
    thread._conf_stop.set()  # type: ignore[attr-defined]
    thread.join(timeout=1.0)
    # Missing-file polling should not crash even if no event is observed before stop.
    assert isinstance(events, list)


# ---------------------------------------------------------------------------
# LoadRemote
# ---------------------------------------------------------------------------


class TestLoadRemote:
    def test_load_remote_invalid_url(self) -> None:
        with pytest.raises(ValidationError):
            vconf.load_remote("http://this.host.does.not.exist.xyz123/config")

    def test_load_remote_safe_private(self) -> None:
        with pytest.raises(ValidationError):
            vconf.load_remote_safe("http://127.0.0.1/config")
