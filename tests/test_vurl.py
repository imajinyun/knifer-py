import pytest

from kniferpy import vurl
from kniferpy.internal import urlx
from kniferpy.verr import SecurityError, ValidationError


def test_validate_http_url_allows_expected_host() -> None:
    assert vurl.validate_http_url(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
    )


def test_validate_http_url_rejects_private_host() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://127.0.0.1:8000")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_rejects_unlisted_host() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url(
            "https://evil.example.com",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
        )
    assert exc_info.value.code == "url.host_not_allowed"


def test_validate_http_url_rejects_non_http_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("file:///tmp/data.txt")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_rejects_ftp_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("ftp://example.com/file")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_no_hostname() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("http://")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_allowed_hosts_case_insensitive() -> None:
    assert vurl.validate_http_url(
        "https://API.Example.COM/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
    )


def test_validate_http_url_loopback_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://localhost:3000")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_link_local_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://169.254.1.1")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_private_range_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://10.0.0.1")
    assert exc_info.value.code == "url.private_host"


def test_is_private_host() -> None:
    assert vurl.is_private_host("127.0.0.1")
    assert vurl.is_private_host("10.0.0.1")
    assert vurl.is_private_host("192.168.1.1")
    assert vurl.is_private_host("172.16.0.1")
    assert vurl.is_private_host("::1")
    assert not vurl.is_private_host("93.184.216.34")


def test_normalize_query_sorts_parameters() -> None:
    assert vurl.normalize_query("https://example.com/path?b=2&a=1") == (
        "https://example.com/path?a=1&b=2"
    )


def test_normalize_query_no_query() -> None:
    assert vurl.normalize_query("https://example.com/path") == "https://example.com/path"


def test_add_and_get_query() -> None:
    url = vurl.add_query(
        "https://example.com/path?a=1",
        {"b": 2, "enabled": True, "skip": None},
    )
    assert url == "https://example.com/path?a=1&b=2&enabled=true"
    assert vurl.get_query(url) == {"a": "1", "b": "2", "enabled": "true"}


def test_add_query_bool_values() -> None:
    url = vurl.add_query("https://example.com/path", {"flag": False, "on": True})
    assert "flag=false" in url
    assert "on=true" in url


def test_add_query_float_value() -> None:
    url = vurl.add_query("https://example.com/path", {"pi": 3.14})
    assert "pi=3.14" in url


def test_remove_query_and_redact_userinfo() -> None:
    assert vurl.remove_query("https://example.com/path?a=1&b=2", {"a"}) == (
        "https://example.com/path?b=2"
    )
    assert vurl.redact_userinfo("https://user:pass@example.com:8443/path") == (
        "https://***@example.com:8443/path"
    )
    assert vurl.redact_userinfo("https://example.com/path") == "https://example.com/path"


def test_remove_query_all() -> None:
    assert vurl.remove_query("https://example.com/path?a=1&b=2", {"a", "b"}) == (
        "https://example.com/path"
    )


def test_redact_userinfo_custom_replacement() -> None:
    result = vurl.redact_userinfo(
        "https://user:pass@example.com/path", replacement="REDACTED"
    )
    assert result == "https://REDACTED@example.com/path"


def test_redact_userinfo_no_userinfo() -> None:
    assert vurl.redact_userinfo("https://example.com/path") == "https://example.com/path"


def test_parse_url() -> None:
    parsed = vurl.parse("https://example.com:8080/path?a=1")
    assert parsed.scheme == "https"
    assert parsed.hostname == "example.com"
    assert parsed.port == 8080
    assert parsed.path == "/path"
    assert parsed.query == "a=1"


def test_get_query_empty() -> None:
    assert vurl.get_query("https://example.com/path") == {}


def test_resolve_host_failure_is_wrapped() -> None:
    with pytest.raises(ValidationError) as exc_info:
        urlx._resolve_host("invalid.invalid.invalid")
    assert exc_info.value.code == "url.resolve_failed"


def test_url_encoding_and_decoding_variants() -> None:
    assert vurl.encode_query("a b+c") == "a+b%2Bc"
    assert vurl.decode_query("a+b%2Bc") == "a b+c"
    assert vurl.encode_path_segment("a/b c") == "a%2Fb%20c"
    assert vurl.encode_path("/a b/c") == "/a%20b/c"
    assert vurl.encode_fragment("a b#c") == "a%20b%23c"
    assert vurl.decode("a%20b") == "a b"
    assert vurl.decode_for_path("/a%20b") == "/a b"
    assert vurl.url_encode("a/b c") == "a%2Fb%20c"
    assert vurl.url_decode("a+b%2Fc") == "a b/c"
    assert vurl.decode_plus("a+b%2Bc") == "a b+c"
    assert vurl.decode_plus("a+b%2Bc", plus_to_space=False) == "a+b+c"
    assert vurl.encode_all("a/b c") == "a%2Fb%20c"
    assert vurl.form_url_encode("a b") == "a%20b"
    assert vurl.encode_blank("a\tb\nc\u3000d") == "a%20b%20c%20d"


def test_url_builder_builds_and_exposes_components() -> None:
    builder = (
        vurl.new_url_builder()
        .set_scheme("https")
        .set_host("api.example.com")
        .set_port(8443)
        .set_path("v1")
        .add_path("users/")
        .add_path_segment("42")
        .set_query("a=1&blank=")
        .add_query("enabled", True)
        .set_fragment("section")
        .set_with_end_tag(True)
    )

    assert builder.scheme() == "https"
    assert builder.scheme_with_default("http") == "https"
    assert builder.host() == "api.example.com"
    assert builder.port() == 8443
    assert builder.port_with_default(443) == 8443
    assert builder.authority() == "api.example.com:8443"
    assert builder.path_string() == "/v1/users/42"
    assert builder.query() == {"a": "1", "blank": "", "enabled": "true"}
    assert builder.query_string() == "a=1&blank=&enabled=true"
    assert builder.fragment() == "section"
    assert str(builder) == "https://api.example.com:8443/v1/users/42?a=1&blank=&enabled=true#section"


def test_url_builder_defaults_and_parse_url_builder() -> None:
    default_builder = vurl.new_url_builder().set_host("example.com")
    http_builder = vurl.new_http_url_builder("example.com")
    parsed = vurl.parse_url_builder("https://example.com:9443/a/b?x=1#frag")

    assert default_builder.scheme_with_default("https") == "https"
    assert default_builder.port_with_default(443) == 443
    assert default_builder.authority() == "example.com"
    assert http_builder.build() == "http://example.com"
    assert parsed.scheme() == "https"
    assert parsed.host() == "example.com"
    assert parsed.port() == 9443
    assert parsed.path_string() == "/a/b"
    assert parsed.query() == {"x": "1"}
    assert parsed.fragment() == "frag"


def test_data_uri_and_query_helpers() -> None:
    assert vurl.data_uri("text/plain", "utf-8", "", "hello") == (
        "data:text/plain;charset=utf-8,hello"
    )
    assert (
        vurl.data_uri("text/plain", "", "base64", "aGVsbG8=")
        == "data:text/plain;base64,aGVsbG8="
    )
    assert vurl.data_uri_base64("text/plain", "hello") == "data:text/plain;base64,aGVsbG8="
    assert vurl.build_query({"a": 1, "flag": False, "skip": None}) == "a=1&flag=false"
    assert vurl.append_query("https://example.com?a=1", {"b": "2"}) == "https://example.com?a=1&b=2"
    assert vurl.encode_query_map({"a": "x y", "enabled": True, "skip": None}) == (
        "a=x+y&enabled=true"
    )
    assert vurl.encode_params("https://example.com/path?a=1&b=x y") == (
        "https://example.com/path?a%3D1%26b%3Dx%20y"
    )
    assert vurl.encode_params("https://example.com/path") == "https://example.com/path"
    assert vurl.decode_query_first("a=1&a=2&blank=") == {"a": "1", "blank": ""}
    assert vurl.decode_query_map("a=1&a=2&blank=") == {"a": ["1", "2"], "blank": [""]}


def test_file_url_and_path_helpers(tmp_path) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")

    file_url = vurl.file_url(first)
    file_urls = vurl.file_urls(first, second)
    parsed = vurl.parse("https://example.com/a%20b?q=1")

    assert file_url.startswith("file://")
    assert file_urls == [vurl.file_url(first), vurl.file_url(second)]
    assert vurl.host("https://example.com:8443/path") == "https://example.com:8443"
    assert vurl.host("/relative/path") == ""
    assert vurl.complete("https://example.com/a/", "b") == "https://example.com/a/b"
    assert vurl.string_uri("hello world") == "string:hello%20world"
    assert vurl.parse_http("https://example.com/a b").path == "/a%20b"
    assert vurl.decoded_path("https://example.com/a%20b") == "/a b"
    assert vurl.url_path("https://example.com/a%20b") == "/a b"
    assert vurl.path("https://example.com/a%20b") == ("/a b", "")
    assert vurl.decoded_path_from_parsed(parsed) == "/a b"
    assert vurl.decoded_path_from_parsed(None) == ""  # type: ignore[arg-type]
    assert vurl.to_uri("https://example.com/a b", encode=True) == "https://example.com/a%20b"
    assert vurl.to_uri("relative path") == "relative path"


def test_url_type_checks_and_normalization(tmp_path) -> None:
    jar = tmp_path / "app.jar"
    jar.write_bytes(b"jar")
    jar_url = vurl.file_url(jar)

    assert vurl.is_http_url("http://example.com")
    assert vurl.is_http_url("https://example.com")
    assert vurl.is_https_url("https://example.com")
    assert vurl.is_absolute_url("https://example.com/path")
    assert not vurl.is_absolute_url("/path")
    assert vurl.is_file_url(jar_url)
    assert vurl.is_jar_url("jar:file:///app.jar!/a")
    assert vurl.is_jar_url("zip:file:///app.zip!/a")
    assert vurl.is_jar_file_url(jar_url)
    assert not vurl.is_jar_file_url("https://example.com/app.jar")
    assert vurl.is_http("http://example.com")
    assert vurl.is_https("https://example.com")
    assert vurl.is_web_url("https://example.com")
    assert not vurl.is_web_url("file:///tmp/a")
    assert urlx._is_http_url("http://example.com")
    assert urlx._is_https_url("https://example.com")
    assert vurl.normalize("https://example.com//a///b c", encode_path=True, replace_slash=True) == (
        "https://example.com/a/b%20c"
    )
    assert vurl.normalize_with_options("https://example.com//a", replace_slash=True) == (
        "https://example.com/a"
    )


def test_open_url_file_content_length_and_unsupported_scheme(tmp_path) -> None:
    path = tmp_path / "data.txt"
    missing = tmp_path / "missing.txt"
    path.write_bytes(b"hello")

    with vurl.open_url(str(path)) as handle:
        assert handle.read() == b"hello"
    with vurl.open_url(vurl.file_url(path)) as handle:
        assert handle.read() == b"hello"
    assert vurl.content_length(str(path)) == 5
    assert vurl.size(str(path)) == 5
    assert vurl.content_length(str(missing)) == -1
    with pytest.raises(ValidationError) as file_exc:
        vurl.open_url(vurl.file_url(missing))
    with pytest.raises(ValidationError) as scheme_exc:
        vurl.open_url("ftp://example.com/file")
    assert file_exc.value.code == "url.file_not_found"
    assert scheme_exc.value.code == "url.unsupported_scheme"


def test_open_http_and_content_length_with_monkeypatched_urlopen(monkeypatch) -> None:
    class FakeHTTPResponse:
        def __init__(self, body: bytes, status: int = 200) -> None:
            self._body = body
            self.status = status

        def read(self) -> bytes:
            return self._body

    calls: list[tuple[str, float | None]] = []

    def fake_urlopen(raw_url: str, timeout: float | None = None) -> FakeHTTPResponse:
        calls.append((raw_url, timeout))
        return FakeHTTPResponse(b"hello")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with vurl.open_url("https://example.com/data", timeout=1.5) as handle:
        assert handle.read() == b"hello"
    assert vurl.content_length("https://example.com/data") == 5
    assert calls[0] == ("https://example.com/data", 1.5)


def test_open_http_wraps_status_and_urlopen_errors(monkeypatch) -> None:
    class StatusResponse:
        status = 404

        def read(self) -> bytes:
            return b"missing"

    def status_urlopen(raw_url: str, timeout: float | None = None) -> StatusResponse:
        return StatusResponse()

    monkeypatch.setattr("urllib.request.urlopen", status_urlopen)
    with pytest.raises(ValidationError) as status_exc:
        vurl.open_url("https://example.com/missing")
    assert status_exc.value.code == "url.open_failed"

    def failing_urlopen(raw_url: str, timeout: float | None = None) -> StatusResponse:
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", failing_urlopen)
    with pytest.raises(ValidationError) as open_exc:
        vurl.open_url("https://example.com/fail")
    assert open_exc.value.code == "url.open_failed"


def test_open_safe_rejects_unsafe_inputs_and_supports_safe_http(monkeypatch) -> None:
    class FakeHTTPResponse:
        status = 200

        def read(self) -> bytes:
            return b"safe"

    monkeypatch.setattr("urllib.request.urlopen", lambda raw_url, timeout=None: FakeHTTPResponse())

    with pytest.raises(SecurityError) as scheme_exc:
        vurl.open_safe("file:///tmp/a")
    with pytest.raises(SecurityError) as host_exc:
        vurl.open_safe("http://127.0.0.1/a")
    with vurl.open_safe("https://example.com/a") as handle:
        assert handle.read() == b"safe"
    assert vurl.content_length_safe("file:///tmp/a") == -1
    assert vurl.content_length_safe("https://example.com/a") == 4
    assert scheme_exc.value.code == "url.scheme_not_allowed"
    assert host_exc.value.code == "url.private_host"


def test_constants_are_exported() -> None:
    assert vurl.ClasspathURLPrefix == "classpath:"
    assert vurl.FileURLPrefix == "file:"
    assert vurl.JarURLPrefix == "jar:"
    assert vurl.WarURLPrefix == "war:"
    assert vurl.URLProtocolFile == "file"
    assert vurl.URLProtocolJar == "jar"
    assert vurl.URLProtocolZip == "zip"
    assert vurl.URLProtocolWSJar == "wsjar"
    assert vurl.URLProtocolVFSZip == "vfszip"
    assert vurl.URLProtocolVFSFile == "vfsfile"
    assert vurl.URLProtocolVFS == "vfs"
    assert vurl.JarURLSeparator == "!/"
    assert vurl.WarURLSeparator == "*/"
    assert vurl.DefaultMaxBytes == 64 << 20
