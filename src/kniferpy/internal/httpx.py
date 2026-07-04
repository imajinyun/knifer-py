from __future__ import annotations

import io
import json
import os
import re
import socket
import ssl
import threading
from dataclasses import dataclass, field
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Dict, List, Protocol, TypeAlias
from urllib.parse import urlencode, urlparse

import requests

from kniferpy.internal import filex, urlx
from kniferpy.verr import DecodeError, SecurityError

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


class ResponseLike(Protocol):
    text: str
    content: bytes
    status_code: int
    headers: Any

    def raise_for_status(self) -> None: ...


class SessionLike(Protocol):
    headers: Any


    def get(self, url: str, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def post(self, url: str, json: JSONValue, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def put(self, url: str, json: JSONValue, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def delete(self, url: str, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def patch(self, url: str, json: JSONValue, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def head(self, url: str, timeout: float, **kwargs: Any) -> ResponseLike: ...

    def options(self, url: str, timeout: float, **kwargs: Any) -> ResponseLike: ...


# ========== Method / Header / ContentType Constants ==========


class Method:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


class Header:
    AUTHORIZATION = "Authorization"
    PROXY_AUTHORIZATION = "Proxy-Authorization"
    DATE = "Date"
    CONNECTION = "Connection"
    MIME_VERSION = "MIME-Version"
    TRAILER = "Trailer"
    TRANSFER_ENCODING = "Transfer-Encoding"
    UPGRADE = "Upgrade"
    VIA = "Via"
    CACHE_CONTROL = "Cache-Control"
    PRAGMA = "Pragma"
    CONTENT_TYPE = "Content-Type"
    HOST = "Host"
    REFERER = "Referer"
    ORIGIN = "Origin"
    USER_AGENT = "User-Agent"
    ACCEPT = "Accept"
    ACCEPT_LANGUAGE = "Accept-Language"
    ACCEPT_ENCODING = "Accept-Encoding"
    ACCEPT_CHARSET = "Accept-Charset"
    COOKIE = "Cookie"
    CONTENT_LENGTH = "Content-Length"
    WWW_AUTHENTICATE = "WWW-Authenticate"
    SET_COOKIE = "Set-Cookie"
    CONTENT_ENCODING = "Content-Encoding"
    CONTENT_DISPOSITION = "Content-Disposition"
    ETAG = "ETag"
    LOCATION = "Location"


class ContentType:
    FORM_URL_ENCODED = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    JSON = "application/json"
    XML = "application/xml"
    TEXT_PLAIN = "text/plain"
    TEXT_XML = "text/xml"
    TEXT_HTML = "text/html"
    OCTET_STREAM = "application/octet-stream"
    EVENT_STREAM = "text/event-stream"


# ========== HTTPError ==========


class HTTPError(Exception):
    def __init__(self, msg: str, code: str = "", cause: Exception | None = None) -> None:
        super().__init__(msg)
        self.code = code
        self.cause = cause

    def __repr__(self) -> str:
        return f"HTTPError(code={self.code!r}, msg={self.args[0]!r})"


def new_error(msg: str, cause: Exception | None = None) -> HTTPError:
    return HTTPError(msg, "", cause)


def new_error_with_code(code: str, msg: str, cause: Exception | None = None) -> HTTPError:
    return HTTPError(msg, code, cause)


def errorf(format_str: str, *args: Any) -> HTTPError:
    return HTTPError(format_str % args)


def errorf_with_code(code: str, format_str: str, *args: Any) -> HTTPError:
    return HTTPError(format_str % args, code)


# ========== URLPolicy ==========


@dataclass
class URLPolicy:
    allowed_schemes: list[str] = field(default_factory=lambda: ["https", "http"])
    allowed_hosts: list[str] = field(default_factory=list)
    reject_private: bool = True
    lookup_ip: Callable[[str], list[str]] | None = None


# ========== RequestOption / ClientOption ==========

RequestOption = Callable[["HTTPRequest"], None]
ClientOption = Callable[["Client"], None]


def with_timeout(d: float) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.timeout = d
    return _apply


def with_header(name: str, value: str) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.headers[name] = value
    return _apply


def with_headers(headers: dict[str, str]) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.headers.update(headers)
    return _apply


def with_follow_redirects(b: bool) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.follow_redirects = b
    return _apply


def with_max_redirects(n: int) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.max_redirects = n
    return _apply


def with_tls_config(cfg: ssl.SSLContext) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.tls_config = cfg
    return _apply


def with_session(session: requests.Session) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.session = session
    return _apply


def with_user_agent(ua: str) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.headers[Header.USER_AGENT] = ua
    return _apply


def with_content_type(ct: str) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.headers[Header.CONTENT_TYPE] = ct
    return _apply


def with_charset(charset: str) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.charset = charset
    return _apply


def with_max_response_bytes(max_bytes: int) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.max_response_bytes = max_bytes
    return _apply


def with_url_policy(policy: URLPolicy) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.url_policy = policy
    return _apply


def with_allowed_hosts(*hosts: str) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.url_policy = URLPolicy(allowed_hosts=list(hosts))
    return _apply


def with_global_config(cfg: GlobalConfig) -> RequestOption:
    def _apply(r: HTTPRequest) -> None:
        r.timeout = cfg.timeout
        r.max_redirects = cfg.max_redirects
        r.max_response_bytes = cfg.max_response_bytes
        r.follow_redirects = cfg.follow_redirects
        if cfg.user_agent:
            r.headers.setdefault(Header.USER_AGENT, cfg.user_agent)
        for k, v in cfg.headers.items():
            r.headers.setdefault(k, v)
    return _apply


def with_client_global_config(cfg: GlobalConfig) -> ClientOption:
    def _apply(c: Client) -> None:
        c.global_config = cfg
    return _apply


def with_client_request_options(opts: list[RequestOption]) -> ClientOption:
    def _apply(c: Client) -> None:
        c.default_options = list(opts)
    return _apply


# ========== FormFile ==========


@dataclass
class FormFile:
    field_name: str
    file_name: str
    data: bytes
    content_type: str = ""


# ========== HTTPRequest (Builder) ==========


class HTTPRequest:
    def __init__(self) -> None:
        self.method: str = Method.GET
        self.raw_url: str = ""
        self.headers: dict[str, str] = {}
        self.query_params: dict[str, Any] = {}
        self.body: bytes | None = None
        self.body_reader: Any | None = None
        self.form_data: dict[str, Any] = {}
        self.form_files: list[FormFile] = []
        self.timeout: float = 30.0
        self.max_redirects: int = 10
        self.max_response_bytes: int = 10_485_760
        self.follow_redirects: bool = True
        self.charset: str = ""
        self.tls_config: ssl.SSLContext | None = None
        self.session: requests.Session | None = None
        self.url_policy: URLPolicy | None = None
        self._safe: bool = False
        self._allowed_hosts: set[str] = set()
        self._resolver: urlx.Resolver | None = None

    def set_method(self, m: str) -> HTTPRequest:
        self.method = m
        return self

    def set_url(self, u: str) -> HTTPRequest:
        self.raw_url = u
        return self

    def set_header(self, name: str, value: str) -> HTTPRequest:
        self.headers[name] = value
        return self

    def add_header(self, name: str, value: str) -> HTTPRequest:
        self.headers[name] = value
        return self

    def set_headers(self, h: dict[str, str]) -> HTTPRequest:
        self.headers.update(h)
        return self

    def set_cookie(self, name: str, value: str) -> HTTPRequest:
        existing = self.headers.get(Header.COOKIE, "")
        if existing:
            self.headers[Header.COOKIE] = f"{existing}; {name}={value}"
        else:
            self.headers[Header.COOKIE] = f"{name}={value}"
        return self

    def set_content_type(self, ct: str) -> HTTPRequest:
        self.headers[Header.CONTENT_TYPE] = ct
        return self

    def set_charset(self, c: str) -> HTTPRequest:
        self.charset = c
        return self

    def set_timeout(self, d: float) -> HTTPRequest:
        self.timeout = d
        return self

    def set_follow_redirects(self, b: bool) -> HTTPRequest:
        self.follow_redirects = b
        return self

    def set_max_redirects(self, n: int) -> HTTPRequest:
        self.max_redirects = n
        return self

    def set_tls_config(self, cfg: ssl.SSLContext) -> HTTPRequest:
        self.tls_config = cfg
        return self

    def set_basic_auth(self, user: str, password: str) -> HTTPRequest:
        self.headers[Header.AUTHORIZATION] = basic_auth_header(user, password)
        return self

    def set_bearer_auth(self, token: str) -> HTTPRequest:
        self.headers[Header.AUTHORIZATION] = bearer_auth_header(token)
        return self

    def set_query(self, key: str, value: Any) -> HTTPRequest:
        self.query_params[key] = value
        return self

    def set_query_map(self, m: dict[str, Any]) -> HTTPRequest:
        self.query_params.update(m)
        return self

    def set_body(self, data: bytes) -> HTTPRequest:
        self.body = data
        return self

    def set_body_string(self, s: str) -> HTTPRequest:
        self.body = s.encode("utf-8")
        return self

    def set_body_json(self, s: str) -> HTTPRequest:
        self.body = s.encode("utf-8")
        self.headers[Header.CONTENT_TYPE] = ContentType.JSON
        return self

    def set_body_reader(self, reader: Any) -> HTTPRequest:
        self.body_reader = reader
        return self

    def set_form(self, data: dict[str, Any]) -> HTTPRequest:
        self.form_data = data
        return self

    def set_form_file(self, field: str, file_name: str, data: bytes, content_type: str = "") -> HTTPRequest:
        self.form_files.append(FormFile(field, file_name, data, content_type))
        return self

    def clone(self) -> HTTPRequest:
        r = HTTPRequest()
        r.method = self.method
        r.raw_url = self.raw_url
        r.headers = dict(self.headers)
        r.query_params = dict(self.query_params)
        r.body = self.body
        r.body_reader = self.body_reader
        r.form_data = dict(self.form_data)
        r.form_files = list(self.form_files)
        r.timeout = self.timeout
        r.max_redirects = self.max_redirects
        r.max_response_bytes = self.max_response_bytes
        r.follow_redirects = self.follow_redirects
        r.charset = self.charset
        r.tls_config = self.tls_config
        r.session = self.session
        r.url_policy = self.url_policy
        r._safe = self._safe
        r._allowed_hosts = set(self._allowed_hosts)
        r._resolver = self._resolver
        return r

    def _build_url(self) -> str:
        url = self.raw_url
        if self.query_params:
            qs = urlencode(self.query_params)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{qs}"
        return url

    def _build_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"timeout": self.timeout}
        if self.headers:
            kwargs["headers"] = self.headers
        if self.body is not None:
            kwargs["data"] = self.body
        elif self.body_reader is not None:
            kwargs["data"] = self.body_reader
        elif self.form_data or self.form_files:
            if self.form_data:
                kwargs["data"] = self.form_data
            if self.form_files:
                files = {}
                for ff in self.form_files:
                    files[ff.field_name] = (ff.file_name, ff.data, ff.content_type or "application/octet-stream")
                kwargs["files"] = files
        if not self.follow_redirects:
            kwargs["allow_redirects"] = False
        return kwargs

    def execute(self) -> HTTPResponse:
        """Execute the request and return an HTTPResponse."""
        url = self._build_url()
        if self._safe:
            urlx.validate_http_url(
                url, allowed_hosts=self._allowed_hosts or None, resolver=self._resolver,
            )
        session = self.session or requests.Session()
        kwargs = self._build_kwargs()
        try:
            resp = session.request(self.method, url, **kwargs)
        except requests.RequestException as e:
            return HTTPResponse(_err=new_error(str(e), e), _status=0)
        resp.raise_for_status()
        if len(resp.content) > self.max_response_bytes:
            raise SecurityError(
                "response exceeds max_bytes",
                code="http.response_too_large",
                context={"size": len(resp.content), "max_bytes": self.max_response_bytes},
            )
        return HTTPResponse(_raw=resp)

    def must_execute(self) -> HTTPResponse:
        resp = self.execute()
        if resp.err is not None:
            raise resp.err
        return resp

    def execute_string(self) -> tuple[str, HTTPError | None]:
        resp = self.execute()
        if resp.err is not None:
            return "", resp.err
        return resp.body(), None

    def execute_bytes(self) -> tuple[bytes, HTTPError | None]:
        resp = self.execute()
        if resp.err is not None:
            return b"", resp.err
        return resp.bytes(), None


# ========== HTTPResponse ==========


class HTTPResponse:
    def __init__(
        self,
        _raw: ResponseLike | None = None,
        _err: HTTPError | None = None,
        _status: int = 0,
        _body: bytes | None = None,
    ) -> None:
        self._raw = _raw
        self.err = _err
        self._status = _status if _status else (_raw.status_code if _raw else 0)
        self._body = _body

    def status(self) -> int:
        return self._status

    def is_ok(self) -> bool:
        return 200 <= self._status < 300

    def header(self, name: str) -> str:
        if self._raw:
            return self._raw.headers.get(name, "")
        return ""

    def headers(self) -> dict[str, str]:
        if self._raw:
            return dict(self._raw.headers)
        return {}

    def cookies(self) -> dict[str, str]:
        """Parse Set-Cookie headers into a dict."""
        result: dict[str, str] = {}
        cookie_header = self.header(Header.SET_COOKIE)
        if not cookie_header:
            return result
        for part in cookie_header.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k.lower() not in ("path", "domain", "expires", "max-age", "secure", "httponly", "samesite"):
                    result[k] = v
        return result

    def content_type(self) -> str:
        return self.header(Header.CONTENT_TYPE)

    def content_length(self) -> int:
        val = self.header(Header.CONTENT_LENGTH)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def charset(self) -> str:
        return get_charset_from_content_type(self.content_type())

    def bytes(self) -> bytes:
        if self._body is not None:
            return self._body
        if self._raw:
            return self._raw.content
        return b""

    def body(self) -> str:
        b = self.bytes()
        cs = self.charset()
        if cs:
            try:
                return b.decode(cs)
            except (LookupError, UnicodeDecodeError):
                pass
        return b.decode("utf-8", errors="replace")

    def write_to(self, w: Any) -> int:
        """Write response body to a writer. Returns bytes written."""
        b = self.bytes()
        n = w.write(b)
        if hasattr(w, "flush"):
            w.flush()
        return n

    def save_as(self, dest: str | Path, overwrite: bool = True) -> int:
        """Save response body to a file. Returns bytes written."""
        dest = Path(dest)
        if not overwrite and dest.exists():
            raise FileExistsError(f"file already exists: {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        b = self.bytes()
        dest.write_bytes(b)
        return len(b)

    def close(self) -> None:
        if self._raw and hasattr(self._raw, "close"):
            self._raw.close()

    def raw(self) -> ResponseLike | None:
        return self._raw


# ========== Client ==========


class Client:
    def __init__(self) -> None:
        self.global_config: GlobalConfig | None = None
        self.default_options: list[RequestOption] = []
        self.session: requests.Session | None = None

    def _apply_global(self, r: HTTPRequest) -> None:
        if self.global_config:
            with_global_config(self.global_config)(r)
        for opt in self.default_options:
            opt(r)

    def new_request(self, method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        r = HTTPRequest()
        r.method = method
        r.raw_url = raw_url
        self._apply_global(r)
        for opt in opts:
            opt(r)
        return r

    def new_safe_request(self, method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        r = self.new_request(method, raw_url, *opts)
        r._safe = True
        return r

    def get(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.GET, raw_url, *opts)

    def get_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.GET, raw_url, *opts)

    def post(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.POST, raw_url, *opts)

    def post_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.POST, raw_url, *opts)

    def put(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.PUT, raw_url, *opts)

    def put_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.PUT, raw_url, *opts)

    def delete(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.DELETE, raw_url, *opts)

    def delete_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.DELETE, raw_url, *opts)

    def patch(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.PATCH, raw_url, *opts)

    def patch_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.PATCH, raw_url, *opts)

    def head(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.HEAD, raw_url, *opts)

    def head_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.HEAD, raw_url, *opts)

    def options(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_request(Method.OPTIONS, raw_url, *opts)

    def options_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        return self.new_safe_request(Method.OPTIONS, raw_url, *opts)


def new_client(*opts: ClientOption) -> Client:
    c = Client()
    for opt in opts:
        opt(c)
    return c


def new_isolated_client(*opts: ClientOption) -> Client:
    c = new_client(*opts)
    c.session = requests.Session()
    return c


def new_client_with_config(cfg: GlobalConfig, opts: list[RequestOption] | None = None) -> Client:
    c = Client()
    c.global_config = cfg
    if opts:
        c.default_options = list(opts)
    return c


# ========== Request Constructors ==========


def _new_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    r = HTTPRequest()
    r.method = method
    r.raw_url = raw_url
    _apply_global_defaults(r)
    for opt in opts:
        opt(r)
    return r


def _new_request_safe(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    r = _new_request(method, raw_url, *opts)
    r._safe = True
    return r


def _apply_global_defaults(r: HTTPRequest) -> None:
    g = _global_config
    r.timeout = g.timeout
    r.max_redirects = g.max_redirects
    r.max_response_bytes = g.max_response_bytes
    r.follow_redirects = g.follow_redirects
    if g.user_agent:
        r.headers.setdefault(Header.USER_AGENT, g.user_agent)
    for k, v in g.headers.items():
        r.headers.setdefault(k, v)


def get(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.GET, raw_url, *opts)


def get_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.GET, raw_url, *opts)


def post(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.POST, raw_url, *opts)


def post_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.POST, raw_url, *opts)


def put(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.PUT, raw_url, *opts)


def put_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.PUT, raw_url, *opts)


def delete(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.DELETE, raw_url, *opts)


def delete_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.DELETE, raw_url, *opts)


def patch(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.PATCH, raw_url, *opts)


def patch_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.PATCH, raw_url, *opts)


def head(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.HEAD, raw_url, *opts)


def head_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.HEAD, raw_url, *opts)


def options(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(Method.OPTIONS, raw_url, *opts)


def options_safe_r(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(Method.OPTIONS, raw_url, *opts)


def new_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request(method, raw_url, *opts)


def new_safe_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    return _new_request_safe(method, raw_url, *opts)


def new_isolated_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    r = _new_request(method, raw_url, *opts)
    r.session = requests.Session()
    return r


def new_request_with_config(method: str, raw_url: str, cfg: GlobalConfig, opts: list[RequestOption] | None = None) -> HTTPRequest:
    r = HTTPRequest()
    r.method = method
    r.raw_url = raw_url
    with_global_config(cfg)(r)
    if opts:
        for opt in opts:
            opt(r)
    return r


# ========== Shortcut Wrappers ==========


def get_string_e(raw_url: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get(raw_url, *opts)
    return r.execute_string()


def get_string_e_with_options(raw_url: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return get_string_e(raw_url, *opts)


def get_string_safe_e(raw_url: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get_safe_r(raw_url, *opts)
    return r.execute_string()


def get_with_timeout_e(raw_url: str, timeout: float, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get(raw_url, with_timeout(timeout), *opts)
    return r.execute_string()


def get_with_params_e(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get(raw_url, *opts)
    r.set_query_map(params)
    return r.execute_string()


def get_with_params_e_with_options(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return get_with_params_e(raw_url, params, *opts)


def post_form_e(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post(raw_url, *opts)
    r.set_form(params)
    return r.execute_string()


def post_form_e_with_options(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return post_form_e(raw_url, params, *opts)


def post_form_safe_e(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post_safe_r(raw_url, *opts)
    r.set_form(params)
    return r.execute_string()


def post_json_e(raw_url: str, json_str: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post(raw_url, *opts)
    r.set_body_json(json_str)
    return r.execute_string()


def post_json_e_with_options(raw_url: str, json_str: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return post_json_e(raw_url, json_str, *opts)


def post_json_safe_e(raw_url: str, json_str: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post_safe_r(raw_url, *opts)
    r.set_body_json(json_str)
    return r.execute_string()


def post_string_e(raw_url: str, body: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post(raw_url, *opts)
    r.set_body_string(body)
    return r.execute_string()


def post_string_e_with_options(raw_url: str, body: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return post_string_e(raw_url, body, *opts)


def post_string_safe_e(raw_url: str, body: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = post_safe_r(raw_url, *opts)
    r.set_body_string(body)
    return r.execute_string()


# ========== Download Helpers ==========


def download_string_e(raw_url: str, custom_charset: str = "", *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get(raw_url, *opts)
    if custom_charset:
        r.set_charset(custom_charset)
    return r.execute_string()


def download_string_e_with_options(raw_url: str, custom_charset: str = "", *opts: RequestOption) -> tuple[str, HTTPError | None]:
    return download_string_e(raw_url, custom_charset, *opts)


def download_string_safe_e(raw_url: str, custom_charset: str = "", *opts: RequestOption) -> tuple[str, HTTPError | None]:
    r = get_safe_r(raw_url, *opts)
    if custom_charset:
        r.set_charset(custom_charset)
    return r.execute_string()


def download_bytes_e(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    r = get(raw_url, *opts)
    return r.execute_bytes()


def download_bytes_e_with_options(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    return download_bytes_e(raw_url, *opts)


def download_bytes_safe_e(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    r = get_safe_r(raw_url, *opts)
    return r.execute_bytes()


# ========== Save to File / Writer ==========

SaveOption = Callable[["SaveConfig"], None]


@dataclass
class SaveConfig:
    file_perm: int = 0o644
    dir_perm: int = 0o755
    overwrite: bool = True
    create_parents: bool = True
    default_filename: str = ""


def with_save_file_perm(perm: int) -> SaveOption:
    def _apply(c: SaveConfig) -> None:
        c.file_perm = perm
    return _apply


def with_save_dir_perm(perm: int) -> SaveOption:
    def _apply(c: SaveConfig) -> None:
        c.dir_perm = perm
    return _apply


def with_save_overwrite(overwrite: bool) -> SaveOption:
    def _apply(c: SaveConfig) -> None:
        c.overwrite = overwrite
    return _apply


def with_save_create_parents(create: bool) -> SaveOption:
    def _apply(c: SaveConfig) -> None:
        c.create_parents = create
    return _apply


def with_save_default_filename(name: str) -> SaveOption:
    def _apply(c: SaveConfig) -> None:
        c.default_filename = name
    return _apply


def download(raw_url: str, w: Any, *opts: RequestOption) -> tuple[int, HTTPError | None]:
    r = get(raw_url, *opts)
    resp = r.execute()
    if resp.err is not None:
        return 0, resp.err
    try:
        n = resp.write_to(w)
        return n, None
    except IOError as e:
        return 0, new_error(str(e), e)


def download_with_options(raw_url: str, w: Any, *opts: RequestOption) -> tuple[int, HTTPError | None]:
    return download(raw_url, w, *opts)


def download_safe(raw_url: str, w: Any, *opts: RequestOption) -> tuple[int, HTTPError | None]:
    r = get_safe_r(raw_url, *opts)
    resp = r.execute()
    if resp.err is not None:
        return 0, resp.err
    try:
        n = resp.write_to(w)
        return n, None
    except IOError as e:
        return 0, new_error(str(e), e)


def download_file(raw_url: str, dest: str | Path, *save_opts: SaveOption) -> tuple[int, HTTPError | None]:
    return _download_file_impl(raw_url, dest, list(save_opts), safe=False)


def download_file_with_options(
    raw_url: str, dest: str | Path, request_opts: list[RequestOption] | None = None, *save_opts: SaveOption,
) -> tuple[int, HTTPError | None]:
    return _download_file_impl(raw_url, dest, list(save_opts), request_opts=request_opts or [], safe=False)


def download_file_safe(raw_url: str, dest: str | Path, *save_opts: SaveOption) -> tuple[int, HTTPError | None]:
    return _download_file_impl(raw_url, dest, list(save_opts), safe=True)


def download_file_safe_with_options(
    raw_url: str, dest: str | Path, request_opts: list[RequestOption] | None = None, *save_opts: SaveOption,
) -> tuple[int, HTTPError | None]:
    return _download_file_impl(raw_url, dest, list(save_opts), request_opts=request_opts or [], safe=True)


def _download_file_impl(
    raw_url: str,
    dest: str | Path,
    save_opts: list[SaveOption],
    request_opts: list[RequestOption] | None = None,
    safe: bool = False,
) -> tuple[int, HTTPError | None]:
    cfg = SaveConfig()
    for opt in save_opts:
        opt(cfg)
    dest = Path(dest)
    if dest.is_dir() or (not dest.suffix and cfg.default_filename):
        dest = dest / cfg.default_filename
    if not cfg.overwrite and dest.exists():
        return 0, new_error(f"file already exists: {dest}")
    if cfg.create_parents:
        dest.parent.mkdir(parents=True, exist_ok=True)
    if request_opts is None:
        request_opts = []
    if safe:
        r = get_safe_r(raw_url, *request_opts)
    else:
        r = get(raw_url, *request_opts)
    resp = r.execute()
    if resp.err is not None:
        return 0, resp.err
    try:
        n = resp.save_as(dest, overwrite=cfg.overwrite)
        if cfg.file_perm:
            os.chmod(dest, cfg.file_perm)
        return n, None
    except OSError as e:
        return 0, new_error(str(e), e)


# ========== UserAgent Parser ==========


@dataclass
class UserAgent:
    is_mobile: bool = False
    browser: str = ""
    version: str = ""
    os: str = ""
    engine: str = ""
    platform: str = ""
    raw: str = ""


def parse_user_agent(ua: str) -> UserAgent:
    result = UserAgent(raw=ua)
    ua_lower = ua.lower()
    result.is_mobile = _is_mobile_ua(ua_lower)
    result.os = _parse_os(ua_lower)
    result.browser, result.version = _parse_browser(ua_lower)
    result.engine = _parse_engine(ua_lower)
    return result


def _is_mobile_ua(ua: str) -> bool:
    return any(k in ua for k in ("mobile", "android", "iphone", "ipad", "ipod", "blackberry", "windows phone"))


def _parse_os(ua: str) -> str:
    if "windows nt 10" in ua:
        return "Windows 10"
    if "windows nt 6.3" in ua:
        return "Windows 8.1"
    if "windows nt 6.2" in ua:
        return "Windows 8"
    if "windows nt 6.1" in ua:
        return "Windows 7"
    if "windows nt" in ua:
        return "Windows"
    if "mac os x" in ua or "macintosh" in ua:
        return "macOS"
    if "android" in ua:
        m = re.search(r"android\s+([\d.]+)", ua)
        return f"Android {m.group(1)}" if m else "Android"
    if "iphone" in ua:
        return "iOS (iPhone)"
    if "ipad" in ua:
        return "iOS (iPad)"
    if "linux" in ua:
        return "Linux"
    return ""


def _parse_browser(ua: str) -> tuple[str, str]:
    browsers = [
        ("edg/", "Edge"),
        ("edge/", "Edge"),
        ("opr/", "Opera"),
        ("opera/", "Opera"),
        ("chrome/", "Chrome"),
        ("safari/", "Safari"),
        ("firefox/", "Firefox"),
        ("msie ", "IE"),
        ("trident/", "IE"),
    ]
    for key, name in browsers:
        if key in ua:
            m = re.search(re.escape(key) + r"([\d.]+)", ua)
            version = m.group(1) if m else ""
            return name, version
    return "", ""


def _parse_engine(ua: str) -> str:
    if "webkit" in ua:
        return "WebKit"
    if "gecko" in ua and "firefox" in ua:
        return "Gecko"
    if "trident" in ua:
        return "Trident"
    if "blink" in ua:
        return "Blink"
    return ""


# ========== SimpleServer ==========


class SimpleServer:
    def __init__(self, addr: str, server: HTTPServer | None = None) -> None:
        self._addr = addr
        self._server = server
        self._handlers: dict[str, Callable] = {}
        self._root_dir: str = ""
        self._static_handler: Callable | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._err_chan: list[Exception] = []

    def add_action(self, path: str, handler: Callable) -> SimpleServer:
        self._handlers[path] = handler
        return self

    def add_handler(self, path: str, handler: Callable) -> SimpleServer:
        self._handlers[path] = handler
        return self

    def set_root(self, dir_path: str) -> SimpleServer:
        self._root_dir = dir_path
        return self

    def set_root_with_options(self, dir_path: str, **opts: Any) -> SimpleServer:
        self._root_dir = dir_path
        return self

    def start(self) -> None:
        host, port_str = self._parse_addr()
        port = int(port_str)

        class _Handler(SimpleHTTPRequestHandler):
            def do_GET(self: Any) -> None:
                if self.path in self.server._handlers:
                    self.server._handlers[self.path](self)
                else:
                    super().do_GET()

            def do_POST(self: Any) -> None:
                if self.path in self.server._handlers:
                    self.server._handlers[self.path](self)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_PUT(self: Any) -> None:
                if self.path in self.server._handlers:
                    self.server._handlers[self.path](self)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_DELETE(self: Any) -> None:
                if self.path in self.server._handlers:
                    self.server._handlers[self.path](self)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self: Any, fmt: str, *args: Any) -> None:
                pass

        server = HTTPServer((host, port), _Handler)
        server._handlers = self._handlers
        self._server = server
        try:
            server.serve_forever()
        except Exception as e:
            self._err_chan.append(e)

    def start_async(self) -> threading.Thread:
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self, timeout: float = 5.0) -> None:
        if self._server:
            self._server.shutdown()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _parse_addr(self) -> tuple[str, str]:
        if ":" in self._addr:
            host, port = self._addr.rsplit(":", 1)
            return host, port
        return "0.0.0.0", self._addr


def new_simple_server(port: int) -> SimpleServer:
    return SimpleServer(str(port))


def new_simple_server_with_options(port: int, **opts: Any) -> SimpleServer:
    s = SimpleServer(str(port))
    return s


def new_simple_server_addr(addr: str) -> SimpleServer:
    return SimpleServer(addr)


def new_simple_server_addr_with_options(addr: str, **opts: Any) -> SimpleServer:
    return SimpleServer(addr)


def create_server(port: int) -> SimpleServer:
    return SimpleServer(str(port))


def create_server_with_options(port: int, **opts: Any) -> SimpleServer:
    return SimpleServer(str(port))


# ========== Scoped Global Config ==========


def with_scoped_global_config(cfg: GlobalConfig, fn: Callable[[], None]) -> None:
    old = snapshot_global_config()
    _apply_cfg(cfg)
    try:
        fn()
    finally:
        _apply_cfg(old)


def _apply_cfg(cfg: GlobalConfig) -> None:
    global _global_config
    set_global_timeout(cfg.timeout)
    set_global_max_redirects(cfg.max_redirects)
    set_global_max_response_bytes(cfg.max_response_bytes)
    set_global_follow_redirects(cfg.follow_redirects)
    set_user_agent(cfg.user_agent)
    _global_config.headers = dict(cfg.headers)
    _global_config.decode_url = cfg.decode_url


def _request_safe(
    method: str,
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
    json_body: JSONValue | None = None,
) -> bytes:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    if method == "GET":
        response = client.get(raw_url, timeout=timeout)
    elif method == "POST":
        response = client.post(raw_url, json=json_body, timeout=timeout)
    elif method == "PUT":
        response = client.put(raw_url, json=json_body, timeout=timeout)
    elif method == "DELETE":
        response = client.delete(raw_url, timeout=timeout)
    elif method == "PATCH":
        response = client.patch(raw_url, json=json_body, timeout=timeout)
    elif method == "HEAD":
        response = client.head(raw_url, timeout=timeout)
    elif method == "OPTIONS":
        response = client.options(raw_url, timeout=timeout)
    else:
        raise ValueError(f"unsupported HTTP method: {method}")
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise SecurityError(
            "response exceeds max_bytes",
            code="http.response_too_large",
            context={"size": len(response.content), "max_bytes": max_bytes},
        )
    return response.content


def get_string_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    body = _request_safe(
        "GET", raw_url,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )
    return body.decode("utf-8")


def get_bytes_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> bytes:
    return _request_safe(
        "GET", raw_url,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )


def download_file_safe(
    raw_url: str,
    dst: str | Path,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 10_485_760,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> Path:
    body = get_bytes_safe(
        raw_url,
        allowed_hosts=allowed_hosts,
        timeout=timeout,
        max_bytes=max_bytes,
        resolver=resolver,
        session=session,
    )
    filex.write_bytes(dst, body)
    return Path(dst)


def get_json_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> JSONValue:
    body = get_bytes_safe(
        raw_url,
        allowed_hosts=allowed_hosts,
        timeout=timeout,
        max_bytes=max_bytes,
        resolver=resolver,
        session=session,
    )
    try:
        return _to_json_value(json.loads(body))
    except json.JSONDecodeError as exc:
        raise DecodeError(str(exc), code="http.response_json_invalid") from exc


def post_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> dict[str, JSONValue]:
    body = _request_safe(
        "POST", raw_url, json_body=payload,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )
    decoded = _to_json_value(json.loads(body))
    if not isinstance(decoded, dict):
        raise SecurityError("response JSON is not an object", code="http.response_not_object")
    return decoded


def put_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> dict[str, JSONValue]:
    body = _request_safe(
        "PUT", raw_url, json_body=payload,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )
    decoded = _to_json_value(json.loads(body))
    if not isinstance(decoded, dict):
        raise SecurityError("response JSON is not an object", code="http.response_not_object")
    return decoded


def delete_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> bytes:
    return _request_safe(
        "DELETE", raw_url,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )


def patch_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> dict[str, JSONValue]:
    body = _request_safe(
        "PATCH", raw_url, json_body=payload,
        allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )
    decoded = _to_json_value(json.loads(body))
    if not isinstance(decoded, dict):
        raise SecurityError("response JSON is not an object", code="http.response_not_object")
    return decoded


def head_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> int:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.head(raw_url, timeout=timeout)
    response.raise_for_status()
    return response.status_code


def options_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> int:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.options(raw_url, timeout=timeout)
    response.raise_for_status()
    return response.status_code


def _to_json_value(value: object) -> JSONValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, dict):
        converted: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise DecodeError(
                    "JSON object key is not a string",
                    code="http.response_json_invalid",
                )
            converted[key] = _to_json_value(item)
        return converted
    raise DecodeError("response is not JSON-compatible", code="http.response_json_invalid")


# ========== MIME / Content-Type ==========

_MIME_TYPES: dict[str, str] = {
    "html": "text/html",
    "htm": "text/html",
    "css": "text/css",
    "js": "application/javascript",
    "json": "application/json",
    "xml": "application/xml",
    "txt": "text/plain",
    "csv": "text/csv",
    "pdf": "application/pdf",
    "zip": "application/zip",
    "gzip": "application/gzip",
    "tar": "application/x-tar",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "ico": "image/x-icon",
    "webp": "image/webp",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "webm": "video/webm",
    "woff": "font/woff",
    "woff2": "font/woff2",
    "ttf": "font/ttf",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "form": "application/x-www-form-urlencoded",
    "multipart": "multipart/form-data",
    "octet": "application/octet-stream",
}


def get_mime_type(ext: str) -> str:
    """Return MIME type for a file extension (without the dot)."""
    return _MIME_TYPES.get(ext.lower().lstrip("."), "application/octet-stream")


def get_ext_by_mime(mime_type: str) -> str:
    """Return file extension for a MIME type."""
    for ext, mt in _MIME_TYPES.items():
        if mt == mime_type:
            return ext
    return ""


def parse_content_type(header: str) -> tuple[str, dict[str, str]]:
    """Parse Content-Type header into (media_type, params)."""
    parts = header.split(";", 1)
    media_type = parts[0].strip().lower()
    params: dict[str, str] = {}
    if len(parts) > 1:
        for param in parts[1].split(";"):
            param = param.strip()
            if "=" in param:
                k, v = param.split("=", 1)
                params[k.strip()] = v.strip().strip('"')
    return media_type, params


# ========== Cookie ==========


def parse_cookies(cookie_header: str) -> dict[str, str]:
    """Parse Cookie header string into a dict."""
    result: dict[str, str] = {}
    if not cookie_header:
        return result
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def make_cookie_header(cookies: dict[str, str]) -> str:
    """Build a Cookie header string from a dict."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def make_set_cookie(
    name: str,
    value: str,
    *,
    path: str = "/",
    domain: str = "",
    max_age: int = 0,
    secure: bool = False,
    http_only: bool = False,
    same_site: str = "",
) -> str:
    """Build a Set-Cookie header string."""
    parts = [f"{name}={value}"]
    if path:
        parts.append(f"Path={path}")
    if domain:
        parts.append(f"Domain={domain}")
    if max_age > 0:
        parts.append(f"Max-Age={max_age}")
    if secure:
        parts.append("Secure")
    if http_only:
        parts.append("HttpOnly")
    if same_site:
        parts.append(f"SameSite={same_site}")
    return "; ".join(parts)


# ========== Auth Headers ==========

import base64 as _base64


def basic_auth_header(username: str, password: str) -> str:
    """Build a Basic Authorization header value."""
    credentials = f"{username}:{password}"
    encoded = _base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def bearer_auth_header(token: str) -> str:
    """Build a Bearer Authorization header value."""
    return f"Bearer {token}"


# ========== Status Codes ==========

HTTP_STATUS = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def http_status_text(code: int) -> str:
    """Return the reason phrase for an HTTP status code."""
    return HTTP_STATUS.get(code, "")


def is_ok(code: int) -> bool:
    return 200 <= code < 300


def is_client_error(code: int) -> bool:
    return 400 <= code < 500


def is_server_error(code: int) -> bool:
    return 500 <= code < 600


# ========== URL Building ==========


def build_url(
    scheme: str = "https",
    host: str = "",
    path: str = "",
    query: dict[str, str] | None = None,
    fragment: str = "",
) -> str:
    """Build a URL from components."""
    from urllib.parse import urlencode, quote
    url = f"{scheme}://{host}"
    if path:
        if not path.startswith("/"):
            url += "/"
        url += quote(path, safe="/@:+")
    if query:
        url += "?" + urlencode(query)
    if fragment:
        url += "#" + quote(fragment)
    return url


# ========== User Agent ==========

_DEFAULT_USER_AGENT = "knifer-py/1.0"


def get_user_agent() -> str:
    return _DEFAULT_USER_AGENT


def set_user_agent(ua: str) -> None:
    global _DEFAULT_USER_AGENT
    _DEFAULT_USER_AGENT = ua


# ========== Global Config ==========


class GlobalConfig:
    def __init__(self) -> None:
        self.timeout: float = 30.0
        self.max_redirects: int = 10
        self.max_response_bytes: int = 10_485_760
        self.follow_redirects: bool = True
        self.user_agent: str = "knifer-py/1.0"
        self.headers: dict[str, str] = {}
        self.decode_url: bool = True

    def clone(self) -> GlobalConfig:
        c = GlobalConfig()
        c.timeout = self.timeout
        c.max_redirects = self.max_redirects
        c.max_response_bytes = self.max_response_bytes
        c.follow_redirects = self.follow_redirects
        c.user_agent = self.user_agent
        c.headers = dict(self.headers)
        c.decode_url = self.decode_url
        return c


_global_config = GlobalConfig()


def snapshot_global_config() -> GlobalConfig:
    return _global_config.clone()


def reset_global_config() -> None:
    global _global_config
    _global_config = GlobalConfig()


def configure_global_config(**kwargs: Any) -> None:
    g = _global_config
    for k, v in kwargs.items():
        if hasattr(g, k):
            setattr(g, k, v)


def set_global_timeout(t: float) -> None:
    _global_config.timeout = t


def get_global_timeout() -> float:
    return _global_config.timeout


def set_global_max_redirects(n: int) -> None:
    _global_config.max_redirects = n


def get_global_max_redirects() -> int:
    return _global_config.max_redirects


def set_global_max_response_bytes(n: int) -> None:
    _global_config.max_response_bytes = n


def get_global_max_response_bytes() -> int:
    return _global_config.max_response_bytes


def set_global_follow_redirects(follow: bool) -> None:
    _global_config.follow_redirects = follow


def get_global_follow_redirects() -> bool:
    return _global_config.follow_redirects


def set_global_header(key: str, value: str) -> None:
    _global_config.headers[key] = value


def add_global_header(key: str, value: str) -> None:
    _global_config.headers[key] = value


def remove_global_header(key: str) -> None:
    _global_config.headers.pop(key, None)


def clone_global_headers() -> dict[str, str]:
    return dict(_global_config.headers)


# ========== Form / Multipart ==========


def post_form_safe(
    raw_url: str,
    data: dict[str, str],
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.post(raw_url, data=data, timeout=timeout)
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise SecurityError(
            "response exceeds max_bytes",
            code="http.response_too_large",
            context={"size": len(response.content), "max_bytes": max_bytes},
        )
    return response.text


def post_multipart_safe(
    raw_url: str,
    files: dict[str, tuple[str, bytes, str]],
    fields: dict[str, str] | None = None,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 30.0,
    max_bytes: int = 10_485_760,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.post(
        raw_url,
        files=files,
        data=fields,
        timeout=timeout,
    )
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise SecurityError(
            "response exceeds max_bytes",
            code="http.response_too_large",
            context={"size": len(response.content), "max_bytes": max_bytes},
        )
    return response.text


# ========== Content Decoding ==========


def decode_response_body(data: bytes, content_encoding: str = "") -> bytes:
    if not content_encoding:
        return data
    enc = content_encoding.strip().lower()
    if enc == "gzip":
        import gzip
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    if enc == "deflate":
        import zlib
        try:
            return zlib.decompress(data)
        except Exception:
            return data
    if enc == "br":
        try:
            import brotli
            return brotli.decompress(data)
        except ImportError:
            pass
        except Exception:
            return data
    return data


# ========== HTML Utilities ==========


def html_escape(s: str) -> str:
    import html
    return html.escape(s)


def html_unescape(s: str) -> str:
    import html
    return html.unescape(s)


_INLINE_TAGS = {
    "a", "abbr", "acronym", "b", "bdo", "big", "br", "button", "cite",
    "code", "dfn", "em", "i", "img", "input", "kbd", "label", "map",
    "object", "output", "q", "samp", "script", "select", "small", "span",
    "strong", "sub", "sup", "textarea", "time", "tt", "var",
}


def clean_html(html_content: str) -> str:
    import re as _re
    # Remove script/style and their contents
    html_content = _re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=_re.DOTALL | _re.IGNORECASE)
    html_content = _re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=_re.DOTALL | _re.IGNORECASE)
    # Remove all tags
    html_content = _re.sub(r"<[^>]+>", "", html_content)
    # Decode entities
    html_content = html_unescape(html_content)
    # Collapse whitespace
    html_content = _re.sub(r"\s+", " ", html_content)
    return html_content.strip()


def filter_html_tag(html_content: str, allowed_tags: set[str] | None = None) -> str:
    import re as _re
    if allowed_tags is None:
        allowed_tags = _INLINE_TAGS
    preserved: list[tuple[str, str]] = []
    counter = [0]

    def _save(m: Any) -> str:
        tag = f"__PRESERVED_{counter[0]}__"
        preserved.append((tag, m.group(0)))
        counter[0] += 1
        return tag

    # Save allowed tags
    pattern = r"</?(" + "|".join(re.escape(t) for t in sorted(allowed_tags, key=len, reverse=True)) + r")(\s[^>]*)?>"
    html_content = _re.sub(pattern, _save, html_content, flags=_re.IGNORECASE)
    # Remove all other tags
    html_content = _re.sub(r"<[^>]+>", "", html_content)
    # Restore preserved tags
    for tag, original in preserved:
        html_content = html_content.replace(tag, original)
    return html_content


# ========== URL Helpers ==========


def to_params(data: dict[str, Any] | None) -> str:
    if not data:
        return ""
    from urllib.parse import urlencode
    return urlencode(data)


def encode_params(params: dict[str, Any] | None) -> str:
    return to_params(params)


def decode_param_map(query: str) -> dict[str, list[str]]:
    from urllib.parse import parse_qs
    if not query:
        return {}
    return parse_qs(query.lstrip("?"))


def decode_params(query: str) -> dict[str, str]:
    from urllib.parse import parse_qs
    if not query:
        return {}
    raw = parse_qs(query.lstrip("?"))
    return {k: v[0] if v else "" for k, v in raw.items()}


def url_with_form(base_url: str, params: dict[str, Any] | None) -> str:
    if not params:
        return base_url
    qs = to_params(params)
    if not qs:
        return base_url
    return f"{base_url}?{qs}" if "?" not in base_url else f"{base_url}&{qs}"


def is_https(url_str: str) -> bool:
    return url_str.strip().lower().startswith("https://")


def is_http(url_str: str) -> bool:
    return url_str.strip().lower().startswith("http://")


def is_redirected(status_code: int) -> bool:
    return status_code in (301, 302, 303, 307, 308)


# ========== Charset Extraction ==========


def get_charset_from_content_type(content_type: str) -> str:
    _, params = parse_content_type(content_type)
    return params.get("charset", "")


def get_charset_from_html(html_content: str) -> str:
    """Extract charset from HTML meta tags."""
    import re as _re
    m = _re.search(r'<meta[^>]+charset\s*=\s*["\']?([^"\'>;\s]+)', html_content, _re.IGNORECASE)
    if m:
        return m.group(1)
    m = _re.search(
        r'<meta[^>]+http-equiv\s*=\s*["\']?content-type[^>]+content\s*=\s*["\'][^"\']*charset\s*=\s*([^"\'>;\s]+)',
        html_content, _re.IGNORECASE,
    )
    return m.group(1) if m else ""


def build_content_type(mime_type: str, charset: str = "") -> str:
    """Build a Content-Type header string with optional charset."""
    if charset:
        return f"{mime_type}; charset={charset}"
    return mime_type


def is_default_content_type(content_type: str) -> bool:
    """Check if content-type is a default/empty value."""
    if not content_type:
        return True
    ct = content_type.strip().lower()
    return ct in ("", "text/plain", "application/octet-stream")


def is_form_urlencoded(content_type: str) -> bool:
    ct = content_type.strip().lower()
    return ct == "application/x-www-form-urlencoded"


def guess_content_type(body: str) -> str:
    """Guess content-type from body text."""
    body = body.strip()
    if body.startswith("{") or body.startswith("["):
        return "application/json"
    if body.startswith("<"):
        return "application/xml"
    if body.startswith("#") or "=" in body.split("\n")[0] if body else False:
        return "text/plain"
    return "text/plain"


# ========== Cookie Jar ==========


class CookieJar:
    """Simple cookie jar for maintaining cookie state across requests."""

    def __init__(self) -> None:
        self._cookies: dict[str, str] = {}

    def set(self, name: str, value: str) -> None:
        self._cookies[name] = value

    def get(self, name: str) -> str:
        return self._cookies.get(name, "")

    def remove(self, name: str) -> None:
        self._cookies.pop(name, None)

    def clear(self) -> None:
        self._cookies.clear()

    def to_header(self) -> str:
        return make_cookie_header(self._cookies)

    def parse_set_cookie(self, header: str) -> None:
        for part in header.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k.lower() not in ("path", "domain", "expires", "max-age", "secure", "httponly", "samesite"):
                    self._cookies[k] = v

    def __len__(self) -> int:
        return len(self._cookies)

    def __contains__(self, name: str) -> bool:
        return name in self._cookies


_global_cookie_jar: CookieJar | None = None


def set_cookie_jar(jar: CookieJar) -> None:
    global _global_cookie_jar
    _global_cookie_jar = jar


def get_cookie_jar() -> CookieJar:
    global _global_cookie_jar
    if _global_cookie_jar is None:
        _global_cookie_jar = CookieJar()
    return _global_cookie_jar


def close_cookie() -> None:
    global _global_cookie_jar
    if _global_cookie_jar is not None:
        _global_cookie_jar.clear()
        _global_cookie_jar = None


# ========== Global Boundary / Decode / EOF ==========


_global_boundary: str = ""
_global_decode_url: bool = True
_ignore_eof_error: bool = False


def set_global_boundary(boundary: str) -> None:
    global _global_boundary
    _global_boundary = boundary


def get_global_boundary() -> str:
    return _global_boundary


def set_global_decode_url(decode: bool) -> None:
    global _global_decode_url
    _global_decode_url = decode


def is_global_decode_url() -> bool:
    return _global_decode_url


def set_ignore_eof_error(ignore: bool) -> None:
    global _ignore_eof_error
    _ignore_eof_error = ignore


def is_ignore_eof_error() -> bool:
    return _ignore_eof_error


# ========== URL encoded POST / GET with params ==========


def get_with_params_safe(
    raw_url: str,
    params: dict[str, Any] | None = None,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    full_url = url_with_form(raw_url, params)
    return get_string_safe(
        full_url, allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )


def post_form_encoded_safe(
    raw_url: str,
    data: dict[str, str],
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    return post_form_safe(
        raw_url, data, allowed_hosts=allowed_hosts, timeout=timeout,
        max_bytes=max_bytes, resolver=resolver, session=session,
    )