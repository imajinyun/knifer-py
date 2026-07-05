import gzip
import io
import re
import ssl
import time
import zlib
from pathlib import Path
from typing import Any

import pytest

from kniferpy import vhttp
from kniferpy.internal import httpx
from kniferpy.verr import DecodeError, SecurityError


class FakeResponse:
    def __init__(
        self,
        text: str = "ok",
        content: bytes = b"ok",
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.text = text
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.closed = False

    def raise_for_status(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeSession:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse()
        self.called_with: str | None = None
        self.timeout: float | None = None
        self.post_payload: Any = None
        self.data_payload: Any = None
        self.files_payload: Any = None
        self.request_call: tuple[str, str, dict[str, Any]] | None = None
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.timeout = kwargs.get("timeout")
        self.request_call = (method, url, kwargs)
        self.calls.append((method, url, kwargs))
        return self.response

    def get(self, url: str, timeout: float, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.timeout = timeout
        self.calls.append(("GET", url, {"timeout": timeout, **kwargs}))
        return self.response

    def post(
        self,
        url: str,
        json: Any = None,
        timeout: float = 10.0,
        **kwargs: Any,
    ) -> FakeResponse:
        self.called_with = url
        self.post_payload = json
        self.data_payload = kwargs.get("data")
        self.files_payload = kwargs.get("files")
        self.calls.append(("POST", url, {"json": json, "timeout": timeout, **kwargs}))
        self.timeout = timeout
        return self.response

    def put(self, url: str, json: Any = None, timeout: float = 10.0, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.post_payload = json
        self.timeout = timeout
        self.calls.append(("PUT", url, {"json": json, "timeout": timeout, **kwargs}))
        return self.response

    def delete(self, url: str, timeout: float = 10.0, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.timeout = timeout
        self.calls.append(("DELETE", url, {"timeout": timeout, **kwargs}))
        return self.response

    def patch(
        self,
        url: str,
        json: Any = None,
        timeout: float = 10.0,
        **kwargs: Any,
    ) -> FakeResponse:
        self.called_with = url
        self.post_payload = json
        self.timeout = timeout
        self.calls.append(("PATCH", url, {"json": json, "timeout": timeout, **kwargs}))
        return self.response

    def head(self, url: str, timeout: float = 10.0, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.timeout = timeout
        self.calls.append(("HEAD", url, {"timeout": timeout, **kwargs}))
        return self.response

    def options(self, url: str, timeout: float = 10.0, **kwargs: Any) -> FakeResponse:
        self.called_with = url
        self.timeout = timeout
        self.calls.append(("OPTIONS", url, {"timeout": timeout, **kwargs}))
        return self.response


def allow_example_host(request: vhttp.HTTPRequest) -> None:
    request._allowed_hosts = {"api.example.com"}
    request._resolver = lambda host: ["93.184.216.34"]


def test_get_string_safe_uses_provider_and_timeout() -> None:
    session = FakeSession()

    body = vhttp.get_string_safe(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
        timeout=1.0,
    )

    assert body == "ok"
    assert session.called_with == "https://api.example.com/health"
    assert session.timeout == 1.0


def test_get_string_safe_rejects_large_response() -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))

    try:
        vhttp.get_string_safe(
            "https://api.example.com/health",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
            max_bytes=3,
        )
    except SecurityError as err:
        assert err.code == "http.response_too_large"
    else:
        raise AssertionError("expected SecurityError")


def test_get_bytes_safe_returns_content() -> None:
    session = FakeSession(FakeResponse(text="ignored", content=b"\x00\x01"))

    body = vhttp.get_bytes_safe(
        "https://api.example.com/file",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert body == b"\x00\x01"


def test_download_file_safe_writes_content(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    target = tmp_path / "nested" / "download.txt"

    written = vhttp.download_file_safe(
        "https://api.example.com/file",
        target,
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert written == target
    assert target.read_bytes() == b"hello"


def test_get_json_safe_decodes_response() -> None:
    session = FakeSession(FakeResponse(text='{"ok": true}', content=b'{"ok": true}'))

    body = vhttp.get_json_safe(
        "https://api.example.com/status",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert body == {"ok": True}


def test_get_json_safe_wraps_decode_errors() -> None:
    session = FakeSession(FakeResponse(text="{bad", content=b"{bad"))

    try:
        vhttp.get_json_safe(
            "https://api.example.com/status",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
        )
    except DecodeError as err:
        assert err.code == "http.response_json_invalid"
    else:
        raise AssertionError("expected DecodeError")


def test_post_json_safe_returns_object() -> None:
    session = FakeSession(FakeResponse(text='{"ok": true}', content=b'{"ok": true}'))

    body = vhttp.post_json_safe(
        "https://api.example.com/create",
        {"name": "kniferpy"},
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
        timeout=2.0,
    )

    assert body == {"ok": True}
    assert session.called_with == "https://api.example.com/create"
    assert session.post_payload == {"name": "kniferpy"}
    assert session.timeout == 2.0


def test_post_json_safe_rejects_non_object_response() -> None:
    session = FakeSession(FakeResponse(text="[1]", content=b"[1]"))

    try:
        vhttp.post_json_safe(
            "https://api.example.com/create",
            {"name": "kniferpy"},
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
        )
    except SecurityError as err:
        assert err.code == "http.response_not_object"
    else:
        raise AssertionError("expected SecurityError")


def test_content_type_value_and_charset_helpers() -> None:
    content_type = vhttp.ContentType(vhttp.ContentType.JSON)

    assert content_type.string() == "application/json"
    assert content_type.with_charset("utf-8") == "application/json; charset=utf-8"


def test_http_error_builders_preserve_code_message_and_cause() -> None:
    cause = RuntimeError("downstream")

    err = vhttp.new_error("failed", cause)
    coded = vhttp.new_error_with_code("http.failed", "failed", cause)
    formatted = vhttp.errorf("bad %s", "input")
    formatted_coded = vhttp.errorf_with_code("http.bad", "bad %s", "input")

    assert repr(coded) == "HTTPError(code='http.failed', msg='failed')"
    assert err.code == ""
    assert err.cause is cause
    assert coded.code == "http.failed"
    assert formatted.args[0] == "bad input"
    assert formatted_coded.code == "http.bad"


def test_request_options_apply_expected_builder_state() -> None:
    request = vhttp.HTTPRequest()
    tls_context = ssl.create_default_context()
    session = FakeSession()
    policy = vhttp.URLPolicy(allowed_hosts=["api.example.com"], reject_private=False)
    cfg = vhttp.GlobalConfig()
    cfg.timeout = 3.5
    cfg.max_redirects = 2
    cfg.max_response_bytes = 99
    cfg.follow_redirects = False
    cfg.user_agent = "cfg-agent"
    cfg.headers = {"X-Global": "yes"}

    for option in (
        vhttp.with_timeout(1.2),
        vhttp.with_header("X-One", "1"),
        vhttp.with_headers({"X-Two": "2"}),
        vhttp.with_follow_redirects(True),
        vhttp.with_max_redirects(7),
        vhttp.with_tls_config(tls_context),
        vhttp.with_session(session),
        vhttp.with_user_agent("agent"),
        vhttp.with_content_type(vhttp.ContentType.JSON),
        vhttp.with_charset("utf-8"),
        vhttp.with_max_response_bytes(128),
        vhttp.with_url_policy(policy),
        vhttp.with_allowed_hosts("allowed.example.com"),
        vhttp.with_global_config(cfg),
    ):
        option(request)

    assert request.timeout == 3.5
    assert request.headers["X-One"] == "1"
    assert request.headers["X-Two"] == "2"
    assert request.headers[vhttp.Header.USER_AGENT] == "agent"
    assert request.headers[vhttp.Header.CONTENT_TYPE] == vhttp.ContentType.JSON
    assert request.headers["X-Global"] == "yes"
    assert request.follow_redirects is False
    assert request.max_redirects == 2
    assert request.tls_config is tls_context
    assert request.session is session
    assert request.charset == "utf-8"
    assert request.max_response_bytes == 99
    assert request.url_policy is not None
    assert request.url_policy.allowed_hosts == ["allowed.example.com"]


def test_client_options_apply_global_config_and_defaults() -> None:
    cfg = vhttp.GlobalConfig()
    cfg.timeout = 6.0
    client = vhttp.new_client(
        vhttp.with_client_global_config(cfg),
        vhttp.with_client_request_options([vhttp.with_header("X-Default", "yes")]),
    )

    request = client.get("https://api.example.com", vhttp.with_header("X-Local", "ok"))

    assert request.method == vhttp.Method.GET
    assert request.raw_url == "https://api.example.com"
    assert request.timeout == 6.0
    assert request.headers["X-Default"] == "yes"
    assert request.headers["X-Local"] == "ok"


def test_http_request_builder_sets_headers_query_body_form_and_clone() -> None:
    request = (
        vhttp.HTTPRequest()
        .set_method(vhttp.Method.POST)
        .set_url("https://api.example.com/items")
        .set_header("X-One", "1")
        .add_header("X-Two", "2")
        .set_headers({"X-Three": "3"})
        .set_cookie("a", "1")
        .set_cookie("b", "2")
        .set_content_type(vhttp.ContentType.TEXT_PLAIN)
        .set_charset("utf-8")
        .set_timeout(1.5)
        .set_follow_redirects(False)
        .set_max_redirects(1)
        .set_basic_auth("user", "pass")
        .set_bearer_auth("token")
        .set_query("q", "knifer py")
        .set_query_map({"page": 2})
        .set_body_string("payload")
    )
    request.set_tls_config(ssl.create_default_context())

    clone = request.clone()

    assert request.method == vhttp.Method.POST
    assert request._build_url() == "https://api.example.com/items?q=knifer+py&page=2"
    assert request.headers["X-One"] == "1"
    assert request.headers[vhttp.Header.COOKIE] == "a=1; b=2"
    assert request.headers[vhttp.Header.AUTHORIZATION] == "Bearer token"
    assert request.body == b"payload"
    assert request.follow_redirects is False
    assert clone is not request
    assert clone.headers == request.headers
    assert clone.query_params == request.query_params
    assert clone._allowed_hosts == request._allowed_hosts


def test_http_request_body_json_reader_form_file_and_transport_aliases() -> None:
    request = vhttp.HTTPRequest()
    session = FakeSession()

    request.set_body_json('{"ok": true}')
    assert request.body == b'{"ok": true}'
    assert request.headers[vhttp.Header.CONTENT_TYPE] == vhttp.ContentType.JSON

    reader = io.BytesIO(b"reader-body")
    request.set_body(None)  # type: ignore[arg-type]
    request.set_body_reader(reader)
    assert request._build_kwargs()["data"] is reader

    request = vhttp.HTTPRequest().set_form({"name": "kniferpy"})
    request.set_form_file("file", "a.txt", b"abc", "text/plain")
    kwargs = request._build_kwargs()
    assert kwargs["data"] == {"name": "kniferpy"}
    assert kwargs["files"]["file"] == ("a.txt", b"abc", "text/plain")

    request.cookie_string("a=1")
    request.transport(session)
    assert request.headers[vhttp.Header.COOKIE] == "a=1"
    assert request.session is session
    request.client(session)
    assert request.session is session

    request.form_file_reader("upload", "b.txt", io.BytesIO(b"xyz"))
    assert request.form_files[-1] == vhttp.FormFile("upload", "b.txt", b"xyz", "")


def test_http_request_execute_success_and_response_methods(tmp_path: Path) -> None:
    raw = FakeResponse(
        text="caf\xe9",
        content="caf\xe9".encode("latin-1"),
        status_code=201,
        headers={
            vhttp.Header.CONTENT_TYPE: "text/plain; charset=latin-1",
            vhttp.Header.CONTENT_LENGTH: "4",
            vhttp.Header.SET_COOKIE: "sid=abc; Path=/; HttpOnly",
            "X-Test": "yes",
        },
    )
    session = FakeSession(raw)
    request = (
        vhttp.HTTPRequest()
        .set_method(vhttp.Method.POST)
        .set_url("https://api.example.com/items")
        .set_query("a", "1")
    )
    request.session = session  # type: ignore[assignment]

    response = request.execute()
    writer = io.BytesIO()
    target = tmp_path / "download.txt"

    assert response.err is None
    assert response.status() == 201
    assert response.is_ok()
    assert response.header("X-Test") == "yes"
    assert response.headers()["X-Test"] == "yes"
    assert response.cookies() == {"sid": "abc"}
    assert response.content_type() == "text/plain; charset=latin-1"
    assert response.content_length() == 4
    assert response.charset() == "latin-1"
    assert response.bytes() == "caf\xe9".encode("latin-1")
    assert response.body() == "caf\xe9"
    assert response.write_to(writer) == 4
    assert writer.getvalue() == "caf\xe9".encode("latin-1")
    assert response.save_as(target) == 4
    assert target.read_bytes() == "caf\xe9".encode("latin-1")
    assert response.raw() is raw
    response.close()
    assert raw.closed
    assert session.request_call is not None
    assert session.request_call[1] == "https://api.example.com/items?a=1"


def test_http_request_execute_returns_error_for_request_exception() -> None:
    class FailingSession(FakeSession):
        def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
            import requests

            raise requests.RequestException("network down")

    request = vhttp.HTTPRequest().set_url("https://api.example.com")
    request.session = FailingSession()  # type: ignore[assignment]

    response = request.execute()

    assert response.status() == 0
    assert response.err is not None
    assert "network down" in str(response.err)
    with pytest.raises(vhttp.HTTPError):
        request.must_execute()


def test_http_request_execute_rejects_oversized_response() -> None:
    request = vhttp.HTTPRequest().set_url("https://api.example.com")
    request.session = FakeSession(FakeResponse(content=b"abcdef"))  # type: ignore[assignment]
    request.max_response_bytes = 3

    with pytest.raises(SecurityError) as exc_info:
        request.execute()

    assert exc_info.value.code == "http.response_too_large"


def test_http_request_execute_string_and_bytes() -> None:
    request = vhttp.HTTPRequest().set_url("https://api.example.com")
    request.session = FakeSession(FakeResponse(text="ok", content=b"ok"))  # type: ignore[assignment]

    assert request.execute_string() == ("ok", None)
    assert request.execute_bytes() == (b"ok", None)


@pytest.mark.parametrize(
    ("factory", "method", "safe"),
    [
        (vhttp.get, vhttp.Method.GET, False),
        (vhttp.get_safe_r, vhttp.Method.GET, True),
        (vhttp.post, vhttp.Method.POST, False),
        (vhttp.post_safe_r, vhttp.Method.POST, True),
        (vhttp.put, vhttp.Method.PUT, False),
        (vhttp.put_safe_r, vhttp.Method.PUT, True),
        (vhttp.delete, vhttp.Method.DELETE, False),
        (vhttp.delete_safe_r, vhttp.Method.DELETE, True),
        (vhttp.patch, vhttp.Method.PATCH, False),
        (vhttp.patch_safe_r, vhttp.Method.PATCH, True),
        (vhttp.head, vhttp.Method.HEAD, False),
        (vhttp.head_safe_r, vhttp.Method.HEAD, True),
        (vhttp.options, vhttp.Method.OPTIONS, False),
        (vhttp.options_safe_r, vhttp.Method.OPTIONS, True),
    ],
)
def test_request_constructor_factories(factory: Any, method: str, safe: bool) -> None:
    request = factory("https://api.example.com", vhttp.with_header("X-Test", "yes"))

    assert request.method == method
    assert request.raw_url == "https://api.example.com"
    assert request.headers["X-Test"] == "yes"
    assert request._safe is safe


def test_new_request_variants_apply_config_and_isolated_session() -> None:
    cfg = vhttp.GlobalConfig()
    cfg.timeout = 4.0
    cfg.headers = {"X-Global": "yes"}

    request = vhttp.new_request(vhttp.Method.GET, "https://api.example.com")
    safe_request = vhttp.new_safe_request(vhttp.Method.POST, "https://api.example.com")
    isolated = vhttp.new_isolated_request(vhttp.Method.PUT, "https://api.example.com")
    with_config = vhttp.new_request_with_config(
        vhttp.Method.PATCH,
        "https://api.example.com",
        cfg,
        [vhttp.with_header("X-Local", "ok")],
    )

    assert request.method == vhttp.Method.GET
    assert safe_request._safe
    assert isolated.session is not None
    assert with_config.timeout == 4.0
    assert with_config.headers["X-Global"] == "yes"
    assert with_config.headers["X-Local"] == "ok"


def test_client_factories_and_methods() -> None:
    cfg = vhttp.GlobalConfig()
    cfg.timeout = 9.0

    isolated = vhttp.new_isolated_client()
    configured = vhttp.new_client_with_config(cfg, [vhttp.with_header("X-Default", "yes")])

    assert isolated.session is not None
    for request in (
        configured.get("https://api.example.com"),
        configured.get_safe("https://api.example.com"),
        configured.post("https://api.example.com"),
        configured.post_safe("https://api.example.com"),
        configured.put("https://api.example.com"),
        configured.put_safe("https://api.example.com"),
        configured.delete("https://api.example.com"),
        configured.delete_safe("https://api.example.com"),
        configured.patch("https://api.example.com"),
        configured.patch_safe("https://api.example.com"),
        configured.head("https://api.example.com"),
        configured.head_safe("https://api.example.com"),
        configured.options("https://api.example.com"),
        configured.options_safe("https://api.example.com"),
    ):
        assert request.timeout == 9.0
        assert request.headers["X-Default"] == "yes"


def test_shortcut_wrappers_execute_with_fake_session() -> None:
    session = FakeSession(FakeResponse(text="ok", content=b"ok"))
    opts = [vhttp.with_session(session)]  # type: ignore[list-item]

    assert vhttp.get_string_e("https://api.example.com", *opts) == ("ok", None)
    assert vhttp.get_string_e_with_options("https://api.example.com", *opts) == ("ok", None)
    assert vhttp.get_with_timeout_e("https://api.example.com", 0.5, *opts) == ("ok", None)
    assert vhttp.get_with_params_e("https://api.example.com", {"a": "1"}, *opts) == ("ok", None)
    assert vhttp.get_with_params_e_with_options(
        "https://api.example.com", {"a": "1"}, *opts
    ) == ("ok", None)
    assert vhttp.post_form_e("https://api.example.com", {"a": "1"}, *opts) == ("ok", None)
    assert vhttp.post_form_e_with_options("https://api.example.com", {"a": "1"}, *opts) == (
        "ok",
        None,
    )
    assert vhttp.post_json_e("https://api.example.com", "{}", *opts) == ("ok", None)
    assert vhttp.post_json_e_with_options("https://api.example.com", "{}", *opts) == ("ok", None)
    assert vhttp.post_string_e("https://api.example.com", "body", *opts) == ("ok", None)
    assert vhttp.post_string_e_with_options("https://api.example.com", "body", *opts) == (
        "ok",
        None,
    )
    assert session.request_call is not None


def test_safe_shortcut_wrappers_execute_after_url_validation() -> None:
    session = FakeSession(FakeResponse(text="ok", content=b"ok"))
    opts = [
        vhttp.with_session(session),  # type: ignore[list-item]
        allow_example_host,
    ]

    assert vhttp.get_string_safe_e("https://api.example.com", *opts) == ("ok", None)
    assert vhttp.post_form_safe_e("https://api.example.com", {"a": "1"}, *opts) == ("ok", None)
    assert vhttp.post_json_safe_e("https://api.example.com", "{}", *opts) == ("ok", None)
    assert vhttp.post_string_safe_e("https://api.example.com", "body", *opts) == ("ok", None)


def test_download_wrappers_to_writer_string_bytes_and_file(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    opts = [vhttp.with_session(session)]  # type: ignore[list-item]
    writer = io.BytesIO()

    assert vhttp.download("https://api.example.com/file", writer, *opts) == (5, None)
    assert writer.getvalue() == b"hello"
    assert vhttp.download_with_options("https://api.example.com/file", io.BytesIO(), *opts) == (
        5,
        None,
    )
    assert vhttp.download_safe(
        "https://api.example.com/file",
        io.BytesIO(),
        allow_example_host,
        *opts,
    ) == (5, None)
    assert vhttp.download_string_e("https://api.example.com/file", "", *opts) == ("hello", None)
    assert vhttp.download_string_e_with_options("https://api.example.com/file", "", *opts) == (
        "hello",
        None,
    )
    assert vhttp.download_bytes_e("https://api.example.com/file", *opts) == (b"hello", None)
    assert vhttp.download_bytes_e_with_options("https://api.example.com/file", *opts) == (
        b"hello",
        None,
    )

    target = tmp_path / "file.txt"
    assert httpx.download_file_with_options(
        "https://api.example.com/file",
        target,
        [vhttp.with_session(session)],  # type: ignore[list-item]
        vhttp.with_save_file_perm(0o600),
    ) == (5, None)
    assert target.read_bytes() == b"hello"


def test_download_file_save_options_handle_default_name_and_overwrite(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    target_dir = tmp_path / "downloads"

    written, err = httpx.download_file_with_options(
        "https://api.example.com/file",
        target_dir,
        [vhttp.with_session(session)],  # type: ignore[list-item]
        vhttp.with_save_default_filename("fallback.txt"),
        vhttp.with_save_dir_perm(0o755),
        vhttp.with_save_create_parents(True),
    )

    assert (written, err) == (5, None)
    assert (target_dir / "fallback.txt").read_bytes() == b"hello"

    written_again, err_again = httpx.download_file_with_options(
        "https://api.example.com/file",
        target_dir / "fallback.txt",
        [vhttp.with_session(session)],  # type: ignore[list-item]
        vhttp.with_save_overwrite(False),
    )
    assert written_again == 0
    assert err_again is not None


def test_user_agent_parser_detects_common_browsers_os_and_engines() -> None:
    chrome = vhttp.parse_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    firefox = vhttp.parse_user_agent(
        "Mozilla/5.0 (X11; Linux x86_64; rv:120) Gecko/20100101 Firefox/120.0"
    )
    iphone = vhttp.parse_user_agent(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148 Safari/604.1"
    )
    android = vhttp.parse_user_agent("Mozilla/5.0 (Linux; Android 14) AppleWebKit Chrome/124")
    edge = vhttp.parse_user_agent("Mozilla/5.0 Edg/124.0")
    opera = vhttp.parse_user_agent("Mozilla/5.0 OPR/100.0")
    ie = vhttp.parse_user_agent("Mozilla/5.0 Trident/7.0")

    assert chrome.browser == "Chrome"
    assert chrome.version == "124.0.0.0"
    assert chrome.os == "Windows 10"
    assert chrome.engine == "WebKit"
    assert firefox.browser == "Firefox"
    assert firefox.engine == "Gecko"
    assert firefox.os == "Linux"
    assert iphone.is_mobile
    assert iphone.os == "macOS"
    assert android.os == "Android 14"
    assert edge.browser == "Edge"
    assert opera.browser == "Opera"
    assert ie.browser == "IE"
    assert ie.engine == "Trident"


def test_simple_server_constructors_and_builder_methods() -> None:
    def handler(req: Any) -> None:
        return None

    server = vhttp.new_simple_server_addr("127.0.0.1:0")

    assert server.add_action("/health", handler) is server
    assert server.add_handler("/ready", handler) is server
    assert server.set_root("/tmp") is server
    assert server.set_root_with_options("/var/tmp") is server
    assert server._parse_addr() == ("127.0.0.1", "0")
    assert vhttp.new_simple_server(8080)._parse_addr() == ("0.0.0.0", "8080")
    assert vhttp.new_simple_server_with_options(8081)._parse_addr() == ("0.0.0.0", "8081")
    assert vhttp.new_simple_server_addr_with_options("localhost:9000")._parse_addr() == (
        "localhost",
        "9000",
    )
    assert vhttp.create_server(8082)._parse_addr() == ("0.0.0.0", "8082")
    assert vhttp.create_server_with_options(8083)._parse_addr() == ("0.0.0.0", "8083")
    server.stop_with_context(None)


def test_scoped_global_config_restores_previous_values() -> None:
    vhttp.reset_global_config()
    original = vhttp.snapshot_global_config()
    cfg = vhttp.GlobalConfig()
    cfg.timeout = 0.7
    cfg.max_redirects = 3
    cfg.max_response_bytes = 256
    cfg.follow_redirects = False
    cfg.user_agent = "scoped-agent"
    cfg.headers = {"X-Scoped": "yes"}
    seen: dict[str, Any] = {}

    def fn() -> None:
        seen["timeout"] = vhttp.get_global_timeout()
        seen["headers"] = vhttp.clone_global_headers()

    vhttp.with_scoped_global_config(cfg, fn)

    assert seen == {"timeout": 0.7, "headers": {"X-Scoped": "yes"}}
    assert vhttp.get_global_timeout() == original.timeout
    assert vhttp.clone_global_headers() == original.headers


def test_safe_json_methods_for_put_delete_patch_head_options_and_params() -> None:
    session = FakeSession(FakeResponse(text='{"ok": true}', content=b'{"ok": true}'))
    kwargs = {
        "allowed_hosts": {"api.example.com"},
        "resolver": lambda host: ["93.184.216.34"],
        "session": session,
    }

    assert vhttp.put_json_safe("https://api.example.com/items", {"a": 1}, **kwargs) == {"ok": True}
    assert vhttp.patch_json_safe("https://api.example.com/items", {"a": 2}, **kwargs) == {
        "ok": True
    }
    assert vhttp.delete_safe("https://api.example.com/items", **kwargs) == b'{"ok": true}'
    assert vhttp.head_safe("https://api.example.com/items", **kwargs) == 200
    assert vhttp.options_safe("https://api.example.com/items", **kwargs) == 200
    assert (
        vhttp.get_with_params_safe("https://api.example.com/items", {"q": "x y"}, **kwargs)
        == '{"ok": true}'
    )
    assert session.calls[-1][1] == "https://api.example.com/items?q=x+y"


def test_safe_json_methods_reject_non_object_for_put_and_patch() -> None:
    session = FakeSession(FakeResponse(text="[1]", content=b"[1]"))
    kwargs = {
        "allowed_hosts": {"api.example.com"},
        "resolver": lambda host: ["93.184.216.34"],
        "session": session,
    }

    with pytest.raises(SecurityError):
        vhttp.put_json_safe("https://api.example.com/items", {"a": 1}, **kwargs)
    with pytest.raises(SecurityError):
        vhttp.patch_json_safe("https://api.example.com/items", {"a": 1}, **kwargs)


def test_safe_form_and_multipart_methods_use_session_payloads() -> None:
    session = FakeSession(FakeResponse(text="accepted", content=b"accepted"))
    kwargs = {
        "allowed_hosts": {"api.example.com"},
        "resolver": lambda host: ["93.184.216.34"],
        "session": session,
    }

    assert vhttp.post_form_safe("https://api.example.com/form", {"a": "1"}, **kwargs) == "accepted"
    assert session.data_payload == {"a": "1"}
    assert (
        vhttp.post_form_encoded_safe("https://api.example.com/form", {"a": "1"}, **kwargs)
        == "accepted"
    )
    assert (
        vhttp.post_multipart_safe(
            "https://api.example.com/upload",
            {"file": ("a.txt", b"abc", "text/plain")},
            {"name": "file"},
            **kwargs,
        )
        == "accepted"
    )
    assert session.files_payload == {"file": ("a.txt", b"abc", "text/plain")}


def test_mime_content_type_cookie_auth_and_status_helpers() -> None:
    assert vhttp.get_mime_type(".JSON") == "application/json"
    assert vhttp.get_mime_type("unknown") == "application/octet-stream"
    assert vhttp.get_ext_by_mime("application/json") == "json"
    assert vhttp.get_ext_by_mime("missing/type") == ""
    assert vhttp.parse_content_type('Text/HTML; charset="utf-8"; boundary=abc') == (
        "text/html",
        {"charset": "utf-8", "boundary": "abc"},
    )
    assert vhttp.parse_cookies("a=1; b=2") == {"a": "1", "b": "2"}
    assert vhttp.parse_cookies("") == {}
    assert vhttp.make_cookie_header({"a": "1", "b": "2"}) == "a=1; b=2"
    assert vhttp.make_set_cookie(
        "sid",
        "abc",
        domain="example.com",
        max_age=60,
        secure=True,
        http_only=True,
        same_site="Lax",
    ) == "sid=abc; Path=/; Domain=example.com; Max-Age=60; Secure; HttpOnly; SameSite=Lax"
    assert vhttp.basic_auth_header("user", "pass") == "Basic dXNlcjpwYXNz"
    assert vhttp.bearer_auth_header("token") == "Bearer token"
    assert vhttp.http_status_text(404) == "Not Found"
    assert vhttp.http_status_text(499) == ""
    assert vhttp.is_ok(204)
    assert vhttp.is_client_error(429)
    assert vhttp.is_server_error(503)
    assert vhttp.is_redirected(308)
    assert not vhttp.is_redirected(200)


def test_url_user_agent_and_global_config_helpers() -> None:
    vhttp.reset_global_config()
    vhttp.set_user_agent("unit-agent")
    assert vhttp.get_user_agent() == "unit-agent"
    assert (
        vhttp.build_url(
            "https",
            "api.example.com",
            "v1/a b",
            {"q": "knifer py"},
            "frag ment",
        )
        == "https://api.example.com/v1/a%20b?q=knifer+py#frag%20ment"
    )
    assert vhttp.to_params({"b": 2, "a": 1}) == "b=2&a=1"
    assert vhttp.encode_params({"a": "x y"}) == "a=x+y"
    assert vhttp.decode_param_map("?a=1&a=2&b=3") == {"a": ["1", "2"], "b": ["3"]}
    assert vhttp.decode_params("?a=1&a=2&b=3") == {"a": "1", "b": "3"}
    assert vhttp.url_with_form("https://api.example.com", {"a": 1}) == "https://api.example.com?a=1"
    assert (
        vhttp.url_with_form("https://api.example.com?x=1", {"a": 1})
        == "https://api.example.com?x=1&a=1"
    )
    assert vhttp.url_with_form("https://api.example.com", None) == "https://api.example.com"
    assert vhttp.is_https(" HTTPS://api.example.com")
    assert vhttp.is_http(" http://api.example.com")

    vhttp.configure_global_config(timeout=2.0, max_redirects=4)
    vhttp.set_global_max_response_bytes(1000)
    vhttp.set_global_follow_redirects(False)
    vhttp.set_global_header("X-One", "1")
    vhttp.add_global_header("X-Two", "2")
    assert vhttp.get_global_timeout() == 2.0
    assert vhttp.get_global_max_redirects() == 4
    assert vhttp.get_global_max_response_bytes() == 1000
    assert vhttp.get_global_follow_redirects() is False
    assert vhttp.clone_global_headers() == {"X-One": "1", "X-Two": "2"}
    vhttp.remove_global_header("X-One")
    assert vhttp.clone_global_headers() == {"X-Two": "2"}


def test_content_decoding_html_url_charset_content_type_helpers() -> None:
    html = "<div>Hello <strong>World</strong><!-- hidden --></div>"

    assert vhttp.decode_response_body(b"plain") == b"plain"
    assert vhttp.decode_response_body(gzip.compress(b"gz"), "gzip") == b"gz"
    assert vhttp.decode_response_body(b"bad", "gzip") == b"bad"
    assert vhttp.decode_response_body(zlib.compress(b"deflate"), "deflate") == b"deflate"
    assert vhttp.decode_response_body(b"bad", "deflate") == b"bad"
    assert vhttp.decode_response_body(b"body", "unknown") == b"body"
    assert vhttp.html_escape("<a&>") == "&lt;a&amp;&gt;"
    assert vhttp.html_unescape("&lt;a&amp;&gt;") == "<a&>"
    assert vhttp.clean_html(html) == "Hello World"
    assert vhttp.clean_html_with_options(
        "<x>keep</x>",
        vhttp.with_html_tag_regexp(re.compile(r"</?x>")),
        vhttp.with_html_comment_regexp(re.compile(r"$^")),
    ) == "keep"
    assert vhttp.filter_html_tag("<div><b>ok</b><script>x</script></div>", {"b"}) == (
        "<b>ok</b>x"
    )
    assert vhttp.filter_html_tag_with_options("<b>drop</b><i>keep</i>", ["b"]) == "<i>keep</i>"
    assert vhttp.filter_html_tag_with_options(
        "<x>drop</x>",
        ["x"],
        vhttp.with_html_filter_compile_func(re.compile),
    ) == ""
    assert vhttp.get_charset_from_content_type("text/html; charset=utf-8") == "utf-8"
    assert (
        vhttp.get_charset_from_content_type_with_options(
            "encoding=gbk",
            vhttp.with_charset_regexp(re.compile(r"encoding=([\w-]+)")),
        )
        == "gbk"
    )
    assert vhttp.get_charset_from_html('<meta charset="utf-8">') == "utf-8"
    assert (
        vhttp.get_charset_from_html_with_options(
            "<meta data-charset='gbk'>",
            vhttp.with_meta_charset_regexp(re.compile(r"data-charset='([^']+)'")),
        )
        == "gbk"
    )
    assert vhttp.build_content_type("text/plain", "utf-8") == "text/plain; charset=utf-8"
    assert vhttp.build_content_type("text/plain") == "text/plain"
    assert vhttp.is_default_content_type("")
    assert vhttp.is_default_content_type("application/octet-stream")
    assert vhttp.is_form_urlencoded("application/x-www-form-urlencoded")
    assert vhttp.guess_content_type('{"ok": true}') == "application/json"
    assert vhttp.guess_content_type("<xml>") == "application/xml"
    assert vhttp.guess_content_type("a=b") == "text/plain"


def test_cookie_jar_and_global_flags() -> None:
    jar = vhttp.CookieJar()

    jar.set("a", "1")
    jar.parse_set_cookie("sid=abc; Path=/; HttpOnly; theme=dark")
    assert jar.get("a") == "1"
    assert jar.get("missing") == ""
    assert "sid" in jar
    assert len(jar) == 3
    assert jar.to_header() == "a=1; sid=abc; theme=dark"
    jar.remove("a")
    assert "a" not in jar
    jar.clear()
    assert len(jar) == 0

    vhttp.set_cookie_jar(jar)
    assert vhttp.get_cookie_jar() is jar
    vhttp.close_cookie()
    assert len(jar) == 0
    assert isinstance(vhttp.get_cookie_jar(), vhttp.CookieJar)

    vhttp.set_global_boundary("BOUNDARY")
    vhttp.set_global_decode_url(False)
    vhttp.set_ignore_eof_error(True)
    assert vhttp.get_global_boundary() == "BOUNDARY"
    assert vhttp.is_global_decode_url() is False
    assert vhttp.is_ignore_eof_error() is True


def test_transport_provider_configuration_and_go_compat_aliases() -> None:
    session = FakeSession()

    vhttp.configure_default_transport_provider(lambda: session)  # type: ignore[return-value]
    assert httpx._default_transport_provider is not None
    assert httpx._default_transport_provider() is session
    vhttp.reset_default_transport()
    assert httpx._default_transport_provider is None

    vhttp.set_global_user_agent("compat-agent")
    assert vhttp.get_global_user_agent() == "compat-agent"
    assert vhttp.get_with_timeout_e_with_options(
        "https://api.example.com",
        0.1,
        vhttp.with_session(FakeSession()),  # type: ignore[arg-type]
    ) == ("ok", None)
    assert vhttp.reset_server_starters() is None


def test_http_request_url_policy_alias_can_be_invoked_unbound() -> None:
    request = vhttp.HTTPRequest()
    policy = vhttp.URLPolicy(allowed_hosts=["api.example.com"])

    returned = vhttp.HTTPRequest.url_policy(request, policy)

    assert returned is request
    assert request.url_policy is policy


def test_http_response_empty_raw_invalid_headers_and_body_fallbacks(tmp_path: Path) -> None:
    empty = vhttp.HTTPResponse()
    direct = vhttp.HTTPResponse(_body=b"direct")
    bad_charset = vhttp.HTTPResponse(
        _raw=FakeResponse(
            content=b"\xff",
            headers={
                vhttp.Header.CONTENT_TYPE: "text/plain; charset=missing-charset",
                vhttp.Header.CONTENT_LENGTH: "bad",
            },
        )
    )
    no_cookie = vhttp.HTTPResponse(
        _raw=FakeResponse(headers={vhttp.Header.CONTENT_LENGTH: "not-an-int"})
    )
    target = tmp_path / "exists.txt"
    target.write_text("old", encoding="utf-8")

    assert empty.header("X-Test") == ""
    assert empty.headers() == {}
    assert empty.bytes() == b""
    assert no_cookie.cookies() == {}
    assert no_cookie.content_length() == 0
    assert direct.bytes() == b"direct"
    assert bad_charset.body() == "\ufffd"
    with pytest.raises(FileExistsError):
        direct.save_as(target, overwrite=False)


def test_execute_string_and_bytes_return_error_tuple() -> None:
    class RequestFailingSession(FakeSession):
        def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
            import requests

            raise requests.RequestException("network down")

    request = vhttp.HTTPRequest().set_url("https://api.example.com")
    request.session = RequestFailingSession()  # type: ignore[assignment]

    text, text_err = request.execute_string()
    body, body_err = request.execute_bytes()

    assert text == ""
    assert text_err is not None
    assert body == b""
    assert body_err is not None


def test_download_helpers_cover_error_paths(tmp_path: Path) -> None:
    class FailingWriter:
        def write(self, data: bytes) -> int:
            raise OSError("disk full")

    class RequestFailingSession(FakeSession):
        def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
            import requests

            raise requests.RequestException("bad status")

    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    failing_status_session = RequestFailingSession()
    oversize_session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    opts = [vhttp.with_session(session)]  # type: ignore[list-item]

    assert vhttp.download_string_e(
        "https://api.example.com/file",
        "latin-1",
        *opts,
    ) == ("hello", None)
    assert vhttp.download_string_safe_e(
        "https://api.example.com/file",
        "utf-8",
        allow_example_host,
        *opts,
    ) == ("hello", None)
    assert vhttp.download_bytes_safe_e(
        "https://api.example.com/file",
        allow_example_host,
        *opts,
    ) == (b"hello", None)
    assert vhttp.download("https://api.example.com/file", FailingWriter(), *opts)[1] is not None
    assert vhttp.download_safe(
        "https://api.example.com/file",
        FailingWriter(),
        allow_example_host,
        *opts,
    )[1] is not None
    assert vhttp.download(
        "https://api.example.com/file",
        io.BytesIO(),
        vhttp.with_session(failing_status_session),  # type: ignore[arg-type]
    )[1] is not None
    assert httpx.download_file(
        "https://api.example.com/file",
        tmp_path / "plain.txt",
        vhttp.with_save_file_perm(0o600),
    )[1] is not None
    assert httpx.download_file_safe_with_options(
        "https://api.example.com/file",
        tmp_path / "safe-options.txt",
        [allow_example_host, vhttp.with_session(session)],  # type: ignore[list-item]
    ) == (5, None)
    with pytest.raises(SecurityError):
        httpx.download_file_with_options(
            "https://api.example.com/file",
            tmp_path / "oversize.txt",
            [
                vhttp.with_session(oversize_session),  # type: ignore[list-item]
                vhttp.with_max_response_bytes(3),
            ],
        )


def test_more_user_agent_and_request_safe_branches() -> None:
    windows_81 = vhttp.parse_user_agent("Mozilla/5.0 (Windows NT 6.3)")
    windows_8 = vhttp.parse_user_agent("Mozilla/5.0 (Windows NT 6.2)")
    windows_7 = vhttp.parse_user_agent("Mozilla/5.0 (Windows NT 6.1)")
    windows = vhttp.parse_user_agent("Mozilla/5.0 (Windows NT 5.1)")
    ipad = vhttp.parse_user_agent("Mozilla/5.0 (iPad) Mobile/15E148")
    unknown = vhttp.parse_user_agent("custom-agent")
    blink = httpx._parse_engine("blink")
    session = FakeSession(FakeResponse(status_code=204))

    assert windows_81.os == "Windows 8.1"
    assert windows_8.os == "Windows 8"
    assert windows_7.os == "Windows 7"
    assert windows.os == "Windows"
    assert ipad.os == "iOS (iPad)"
    assert unknown.browser == ""
    assert blink == "Blink"
    assert httpx._request_safe(
        "HEAD",
        "https://api.example.com",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    ) == b"ok"
    with pytest.raises(ValueError):
        httpx._request_safe(
            "TRACE",
            "https://api.example.com",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
        )


def test_json_value_internal_rejects_non_string_keys_and_non_json_values() -> None:
    with pytest.raises(DecodeError) as key_exc:
        httpx._to_json_value({1: "bad"})
    with pytest.raises(DecodeError) as value_exc:
        httpx._to_json_value(object())

    assert key_exc.value.code == "http.response_json_invalid"
    assert value_exc.value.code == "http.response_json_invalid"


def test_safe_form_and_multipart_reject_oversized_response() -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    kwargs = {
        "allowed_hosts": {"api.example.com"},
        "resolver": lambda host: ["93.184.216.34"],
        "session": session,
        "max_bytes": 3,
    }

    with pytest.raises(SecurityError) as form_exc:
        vhttp.post_form_safe("https://api.example.com/form", {"a": "1"}, **kwargs)
    with pytest.raises(SecurityError) as multipart_exc:
        vhttp.post_multipart_safe(
            "https://api.example.com/upload",
            {"file": ("a.txt", b"abc", "text/plain")},
            None,
            **kwargs,
        )

    assert form_exc.value.code == "http.response_too_large"
    assert multipart_exc.value.code == "http.response_too_large"


def test_content_decoding_brotli_and_option_default_fallbacks() -> None:
    try:
        import brotli
    except ImportError:
        compressed = b"body"
        expected = b"body"
    else:
        compressed = brotli.compress(b"br")
        expected = b"br"

    assert vhttp.decode_response_body(compressed, "br") == expected
    assert vhttp.decode_response_body(b"bad", "br") == b"bad"
    assert httpx._apply_html_clean_options(
        [vhttp.with_html_tag_regexp(None), vhttp.with_html_comment_regexp(None)]  # type: ignore[arg-type]
    ).tag_re is not None
    assert httpx._apply_html_filter_options(
        [vhttp.with_html_filter_compile_func(None)]  # type: ignore[arg-type]
    ).compile is re.compile
    assert httpx._apply_charset_options(
        [vhttp.with_charset_regexp(None), vhttp.with_meta_charset_regexp(None)]  # type: ignore[arg-type]
    ).charset_pattern is not None


def test_html_url_charset_empty_and_error_tolerant_branches() -> None:
    def bad_compile(pattern: str) -> re.Pattern[str]:
        raise re.error("bad pattern")

    assert vhttp.filter_html_tag("<div><b>ok</b></div>") == "<b>ok</b>"
    assert vhttp.filter_html_tag_with_options("<b>keep</b>", None) == ""
    assert vhttp.filter_html_tag_with_options(
        "<x>keep</x>",
        ["x"],
        vhttp.with_html_filter_compile_func(bad_compile),
    ) == "<x>keep</x>"
    assert vhttp.to_params(None) == ""
    assert vhttp.decode_param_map("") == {}
    assert vhttp.decode_params("") == {}
    assert vhttp.url_with_form("https://api.example.com", {}) == "https://api.example.com"
    assert (
        vhttp.get_charset_from_html_with_options(
            "<html></html>",
            vhttp.with_meta_charset_regexp(None),  # type: ignore[arg-type]
        )
        == ""
    )
    assert vhttp.guess_content_type("") == "text/plain"


def test_simple_server_start_async_and_stop() -> None:
    server = vhttp.SimpleServer("127.0.0.1:0")
    thread = server.start_async()

    for _ in range(100):
        if server._server is not None:
            break
        time.sleep(0.01)

    assert thread.is_alive()
    assert server._server is not None
    server.stop(timeout=1.0)
    assert not thread.is_alive()
