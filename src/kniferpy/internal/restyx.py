from __future__ import annotations

import io
import ipaddress
import json as json_lib
import os
import re
import socket
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, TypeVar
from urllib.parse import urlencode, urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.cookies import RequestsCookieJar

from kniferpy.verr import ValidationError

T = TypeVar('T')


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


HeaderValues = Dict[str, List[str]]


@dataclass
class URLPolicy:
    """URLPolicy controls SSRF-oriented request validation for untrusted URLs."""
    allowed_schemes: list[str] = field(default_factory=lambda: ["http", "https"])
    allowed_hosts: list[str] = field(default_factory=list)
    reject_private: bool = True
    lookup_ip: Callable[[str], list[str]] | None = None


@dataclass
class GlobalConfig:
    """GlobalConfig captures package-level defaults for explicit request construction."""
    timeout: float = 0.0
    max_redirects: int = 10
    follow_redirects: bool = True
    max_response_bytes: int = 0
    default_user_agent: str = ""
    cookie_disabled: bool = False
    headers: HeaderValues = field(default_factory=dict)


@dataclass
class Cookie:
    """Cookie contains a response cookie name and value."""
    name: str
    value: str
    domain: str = ""
    path: str = "/"
    expires: float | None = None
    secure: bool = False
    http_only: bool = False


@dataclass
class FormFile:
    """FormFile represents a file to be uploaded in a multipart form."""
    field: str
    file_name: str
    data: bytes | None = None
    reader: io.IOBase | None = None


@dataclass
class HTTPError(Exception):
    """HTTPError is the HTTP module error type."""
    message: str
    cause: Exception | None = None

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message}: {self.cause}"
        return self.message


def new_http_error(msg: str, cause: Exception | None = None) -> HTTPError:
    """Create a new HTTP error."""
    return HTTPError(msg, cause)


def http_errorf(format_str: str, *args: Any) -> HTTPError:
    """Create an HTTP error with a formatted message."""
    return HTTPError(format_str % args)


@dataclass
class HTTPResponse:
    """HTTPResponse wraps an HTTP response."""
    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    cookies: list[Cookie] = field(default_factory=list)
    body: bytes = field(default_factory=bytes)
    text: str = ""
    json_result: Any | None = None
    err: HTTPError | None = None
    raw_response: requests.Response | None = None

    def is_ok(self) -> bool:
        """Returns True if status code is 2xx."""
        return 200 <= self.status_code < 300

    def body_bytes(self) -> bytes:
        """Returns the raw response body bytes."""
        return self.body

    def body_text(self) -> str:
        """Returns the response body as string."""
        return self.text

    def json(self) -> Any | None:
        """Returns the parsed JSON response."""
        return self.json_result

    def error(self) -> HTTPError | None:
        """Returns any error that occurred during the request."""
        return self.err

    def content_length(self) -> int:
        """Returns the content length header value."""
        cl = self.headers.get('Content-Length')
        if cl:
            try:
                return int(cl)
            except ValueError:
                pass
        return 0

    # ── Go-compat methods ────────────────────────────────────────────────────

    def write_to(self, writer):
        """Write the response body to a writer and return bytes written (Go compat)."""
        return writer.write(self.body)

    def save_as(self, dest, **opts):
        """Save the response body to a file and return bytes written (Go compat)."""
        path = dest
        if opts.get('default_filename'):
            path = os.path.join(dest, opts['default_filename'])
        if not path:
            raise ValidationError('destination path is required', code='knifer.resty.save_as')
        parent = os.path.dirname(os.path.abspath(path))
        if opts.get('create_parents', True) and parent:
            os.makedirs(parent, exist_ok=True)
        if not opts.get('overwrite', True) and os.path.exists(path):
            raise ValidationError(f'file already exists: {path}', code='knifer.resty.save_as')
        with open(path, 'wb') as f:
            return f.write(self.body)

    def close(self):
        """Close the underlying raw response (Go compat)."""
        if self.raw_response is not None:
            self.raw_response.close()

    def result(self):
        """Return the decoded response result (Go compat)."""
        return self.json_result

    def error_result(self):
        """Return the decoded error response result (Go compat)."""
        return self.err


@dataclass
class SaveOptions:
    """SaveOptions customizes response file saving."""
    file_perm: int = 0o644
    dir_perm: int = 0o755
    overwrite: bool = True
    create_parents: bool = True
    default_filename: str = ""
    stat: Callable[[str], os.stat_result] | None = None
    mkdir_all: Callable[[str, int], None] | None = None
    open_file: Callable[[str, int, int], io.IOBase] | None = None


RequestOption = Callable[['HTTPRequest'], None]
ClientOption = Callable[['Client'], None]
CharsetOption = Callable[['CharsetContext'], None]


@dataclass
class CharsetContext:
    """CharsetContext holds options for charset extraction."""
    charset_re: re.Pattern = field(default_factory=lambda: re.compile(
        r'charset\s*=\s*["\']?\s*([^\s"\';]+)', re.IGNORECASE))
    meta_charset_re: re.Pattern = field(default_factory=lambda: re.compile(
        r'<meta[^>]+charset\s*=\s*["\']?\s*([^\s"\'>]+)', re.IGNORECASE))


class HTTPRequest:
    """HTTPRequest is a chainable HTTP request builder backed by requests."""

    def __init__(self):
        self.method: str = Method.GET
        self.raw_url: str = ""
        self.query_params: dict[str, list[str]] = {}
        self._headers: HeaderValues = {}
        self._body: Any = None
        self._form: dict[str, Any] = {}
        self.files: list[FormFile] = []
        self._content_type: str = ""
        self._charset: str = "UTF-8"
        self._timeout: float = 0.0
        self._follow_redirects: bool | None = None
        self._max_redirects: int = 10
        self._tls_config: ssl.SSLContext | None = None
        self._user_agent: str = ""
        self.cookie_off: bool = False
        self.basic_user: str = ""
        self.basic_pass: str = ""
        self.has_basic: bool = False
        self._session: requests.Session | None = None
        self._session_factory: Callable[[], requests.Session] | None = None
        self.json_marshal: Callable[[Any], bytes] | None = None
        self.json_unmarshal: Callable[[bytes], Any] | None = None
        self.max_decode: int = 0
        self.max_response: int = 0
        self._url_policy: URLPolicy | None = None
        self._result: Any = None
        self._error_result: Any = None

    def method(self, m: str) -> HTTPRequest:
        """Set the HTTP method."""
        self.method = m
        return self

    def url(self, u: str) -> HTTPRequest:
        """Set the request URL."""
        self.raw_url = u
        return self

    def header(self, name: str, value: str) -> HTTPRequest:
        """Set a single request header, replacing existing values."""
        self._headers[name] = [value]
        return self

    def add_header(self, name: str, value: str) -> HTTPRequest:
        """Append a single request header value."""
        if name not in self._headers:
            self._headers[name] = []
        self._headers[name].append(value)
        return self

    def headers(self, h: dict[str, str]) -> HTTPRequest:
        """Set request headers in batch."""
        for k, v in h.items():
            self._headers[k] = [v]
        return self

    def cookie(self, name: str, value: str) -> HTTPRequest:
        """Add a cookie by name and value."""
        if name:
            self.add_header(Header.COOKIE, f"{name}={value}")
        return self

    def cookie_string(self, s: str) -> HTTPRequest:
        """Add a Cookie header from a raw string."""
        self.header(Header.COOKIE, s)
        return self

    def content_type(self, ct: str) -> HTTPRequest:
        """Set Content-Type."""
        self._content_type = ct
        return self

    def charset(self, c: str) -> HTTPRequest:
        """Set the request charset."""
        self._charset = c
        return self

    def timeout(self, d: float) -> HTTPRequest:
        """Set the request timeout in seconds."""
        self._timeout = d
        return self

    def follow_redirects(self, b: bool) -> HTTPRequest:
        """Set whether redirects are followed."""
        self._follow_redirects = b
        return self

    def max_redirects(self, n: int) -> HTTPRequest:
        """Set the maximum redirect count."""
        self._max_redirects = n
        return self

    def tls_config(self, cfg: ssl.SSLContext) -> HTTPRequest:
        """Set a custom TLS config."""
        self._tls_config = cfg
        return self

    def session_client(self, session: requests.Session) -> HTTPRequest:
        """Set a custom requests session."""
        self._session = session
        return self

    def session_factory(self, factory: Callable[[], requests.Session]) -> HTTPRequest:
        """Set a per-request session factory."""
        self._session_factory = factory
        return self

    def set_url_policy(self, policy: URLPolicy) -> HTTPRequest:
        """Set SSRF-oriented validation for this request."""
        self._url_policy = URLPolicy(
            allowed_schemes=list(policy.allowed_schemes),
            allowed_hosts=list(policy.allowed_hosts),
            reject_private=policy.reject_private,
            lookup_ip=policy.lookup_ip
        )
        return self

    def basic_auth(self, user: str, password: str) -> HTTPRequest:
        """Set Basic Auth."""
        self.basic_user = user
        self.basic_pass = password
        self.has_basic = True
        return self

    def bearer_auth(self, token: str) -> HTTPRequest:
        """Set the Bearer Token."""
        self.header(Header.AUTHORIZATION, f"Bearer {token}")
        return self

    def query(self, key: str, value: Any) -> HTTPRequest:
        """Add a single URL query parameter."""
        if key not in self.query_params:
            self.query_params[key] = []
        self.query_params[key].append(str(value))
        return self

    def query_map(self, params: dict[str, Any]) -> HTTPRequest:
        """Add URL query parameters in batch."""
        for k, v in params.items():
            if k not in self.query_params:
                self.query_params[k] = []
            self.query_params[k].append(str(v))
        return self

    def body(self, body: bytes) -> HTTPRequest:
        """Set the raw request body."""
        self._body = body
        if not self._content_type:
            ct = guess_content_type(body.decode(errors='ignore'))
            if ct:
                self._content_type = build_content_type(ct, self._charset)
        return self

    def body_string(self, s: str) -> HTTPRequest:
        """Set a string request body."""
        return self.body(s.encode(self._charset or 'utf-8'))

    def body_json(self, json_str: str) -> HTTPRequest:
        """Set a JSON request body from string."""
        self._content_type = build_content_type(ContentType.JSON, self._charset)
        return self.body(json_str.encode(self._charset or 'utf-8'))

    def body_json_value(self, value: Any) -> HTTPRequest:
        """Set a JSON request body value to be encoded."""
        self._content_type = build_content_type(ContentType.JSON, self._charset)
        self._body = value
        return self

    def result(self, v: Any) -> HTTPRequest:
        """Register a value for automatic response decoding."""
        self._result = v
        return self

    def error_result(self, v: Any) -> HTTPRequest:
        """Register a value for automatic error response decoding."""
        self._error_result = v
        return self

    def body_reader(self, reader: io.IOBase) -> HTTPRequest:
        """Set the request body from an io.Reader."""
        self._body = reader
        return self

    def form(self, data: dict[str, Any]) -> HTTPRequest:
        """Set form parameters."""
        for k, v in data.items():
            self._form[k] = v
        return self

    def form_file(self, field: str, file_name: str, data: bytes) -> HTTPRequest:
        """Add a file upload field and enables multipart automatically."""
        self.files.append(FormFile(field=field, file_name=file_name, data=data))
        return self

    def form_file_reader(self, field: str, file_name: str, reader: io.IOBase) -> HTTPRequest:
        """Add a file upload field from a reader."""
        self.files.append(FormFile(field=field, file_name=file_name, reader=reader))
        return self

    def execute(self) -> HTTPResponse:
        """Send the request and returns the response."""
        try:
            return self._do_execute()
        except HTTPError as e:
            return HTTPResponse(err=e)
        except Exception as e:
            return HTTPResponse(err=new_http_error("request failed", e))

    def must_execute(self) -> HTTPResponse:
        """Send the request and panics on failure."""
        resp = self.execute()
        if resp.err:
            raise resp.err
        return resp

    def _do_execute(self) -> HTTPResponse:
        parsed = urlparse(self.raw_url)
        self._validate_request_url(parsed)

        session = self._build_session()
        prepared_request = self._prepare_request(session, parsed)

        if self._timeout > 0:
            response = session.send(prepared_request, timeout=self._timeout)
        else:
            response = session.send(prepared_request)

        return self._wrap_response(response)

    def _validate_request_url(self, parsed: urlparse.ParseResult) -> None:
        """Validate the request URL against the URL policy for SSRF safety."""
        if self._url_policy is None:
            return

        scheme = parsed.scheme.lower().strip() if parsed.scheme else ""
        if scheme and (self._url_policy.allowed_schemes and
            scheme not in [s.lower() for s in self._url_policy.allowed_schemes]):
            raise http_errorf(f"url scheme {repr(scheme)} is not allowed")

        if scheme not in ('http', 'https'):
            return

        host = (parsed.hostname or "").lower().strip()
        if not host:
            raise http_errorf("http url host is blank")

        if self._url_policy.allowed_hosts and not any(
            h.lower().strip() == host for h in self._url_policy.allowed_hosts
        ):
            raise http_errorf(f"url host {repr(host)} is not allowed")

        if self._url_policy.reject_private:
            private = self._is_private_host(host)
            if private:
                raise http_errorf(f"url host {repr(host)} resolves to a private address")

    def _is_private_host(self, host: str) -> bool:
        """Check if the host resolves to a private IP address."""
        if host.lower() == 'localhost':
            return True

        try:
            ip = ipaddress.ip_address(host)
            return self._is_private_ip(ip)
        except ValueError:
            pass

        if self._url_policy and self._url_policy.lookup_ip:
            ips = self._url_policy.lookup_ip(host)
        else:
            try:
                _, ips = socket.gethostbyname_ex(host)
            except socket.gaierror:
                return False
        if not ips:
            return False

        for ip_str in ips:
            try:
                ip = ipaddress.ip_address(ip_str)
                if self._is_private_ip(ip):
                    return True
            except ValueError:
                continue
        return False

    def _is_private_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if the IP address is private/non-global unicast."""
        return (
            ip.is_private or
            not ip.is_global or
            ip.is_link_local or
            ip.is_loopback or
            ip.is_reserved or
            ip.is_unspecified
        )

    def _build_session(self) -> requests.Session:
        """Build the requests session with all configured options."""
        if self._session:
            return self._session

        if self._session_factory:
            session = self._session_factory()
            if session:
                return session

        session = requests.Session()

        if self.cookie_off:
            session.cookies = RequestsCookieJar()

        if self.max_response > 0:
            pass

        if self._tls_config:
            session.mount('https://', SSLAdapter(self._tls_config))

        if self._url_policy:
            adapter = SafeHTTPAdapter(self._url_policy)
            session.mount('http://', adapter)
            session.mount('https://', adapter)

        follow = True if self._follow_redirects is None else self._follow_redirects
        if not follow:
            session.max_redirects = 0
        elif self._max_redirects > 0:
            session.max_redirects = self._max_redirects

        return session

    def _prepare_request(self, session: requests.Session, parsed: urlparse.ParseResult) -> requests.PreparedRequest:
        """Prepare the request with all configured data."""
        url = self.raw_url
        if self.query_params:
            query_parts = []
            for k, values in sorted(self.query_params.items()):
                for v in values:
                    query_parts.append((k, v))
            query_string = urlencode(query_parts)
            url = url + '&' + query_string if parsed.query else url + '?' + query_string

        req = requests.Request(method=self.method, url=url)

        for k, vs in self._headers.items():
            for v in vs:
                req.headers[k] = v

        if self._content_type:
            req.headers['Content-Type'] = self._content_type

        if self._user_agent and 'User-Agent' not in req.headers:
            req.headers['User-Agent'] = self._user_agent

        if self.has_basic:
            req.auth = (self.basic_user, self.basic_pass)

        files: dict[str, tuple[str, Any]] = {}
        for f in self.files:
            if f.reader:
                files[f.field] = (f.file_name, f.reader)
            elif f.data:
                files[f.field] = (f.file_name, f.data)

        if files:
            for k, v in self._form.items():
                if k not in files:
                    files[k] = (None, str(v))
            req.files = files
        elif self._form:
            if self.method in (Method.POST, Method.PUT, Method.PATCH):
                req.data = {k: str(v) for k, v in self._form.items()}
            else:
                for k, v in self._form.items():
                    req.params[k] = str(v)
        elif self._body is not None:
            if isinstance(self._body, (bytes, io.IOBase)):
                req.data = self._body
            elif isinstance(self._body, (dict, list)):
                if self.json_marshal:
                    data = self.json_marshal(self._body)
                    req.data = data
                else:
                    req.json = self._body

        return session.prepare_request(req)

    def _wrap_response(self, resp: requests.Response) -> HTTPResponse:
        """Wrap a requests.Response into our HTTPResponse."""
        response = HTTPResponse()
        response.status_code = resp.status_code
        response.headers = dict(resp.headers)
        response.raw_response = resp

        for name, cookie in resp.cookies.items():
            response.cookies.append(Cookie(name=name, value=cookie))

        try:
            response.body = resp.content
        except Exception as e:
            raise new_http_error("failed to read response body", e) from e

        if self.charset:
            encoding = resp.apparent_encoding or self._charset
        else:
            encoding = resp.apparent_encoding or 'utf-8'
        try:
            response.text = response.body.decode(encoding)
        except UnicodeDecodeError:
            response.text = response.body.decode('utf-8', errors='replace')

        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                if self.json_unmarshal:
                    response.json_result = self.json_unmarshal(response.body)
                else:
                    response.json_result = json_lib.loads(response.body)
            except json_lib.JSONDecodeError:
                pass

        return response


class SSLAdapter(HTTPAdapter):
    """HTTPAdapter with custom SSL context."""

    def __init__(self, ssl_context: ssl.SSLContext, **kwargs: Any):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


class SafeHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that enforces SSRF safety checks."""

    def __init__(self, policy: URLPolicy, **kwargs: Any):
        self.policy = policy
        super().__init__(**kwargs)

    def get_connection(self, url: str, proxies: dict[str, str] | None = None):
        """Override to validate URL before connecting."""
        parsed = urlparse(url)
        self._validate_url(parsed)
        return super().get_connection(url, proxies)

    def _validate_url(self, parsed: urlparse.ParseResult) -> None:
        """Validate the URL against the SSRF policy."""
        scheme = parsed.scheme.lower().strip()
        if self.policy.allowed_schemes and scheme not in [s.lower() for s in self.policy.allowed_schemes]:
            raise http_errorf(f"url scheme {repr(scheme)} is not allowed")

        if scheme not in ('http', 'https'):
            return

        host = (parsed.hostname or "").lower().strip()
        if not host:
            raise http_errorf("http url host is blank")

        if self.policy.allowed_hosts and not any(h.lower().strip() == host for h in self.policy.allowed_hosts):
            raise http_errorf(f"url host {repr(host)} is not allowed")

        if self.policy.reject_private:
            private = self._is_private_host(host)
            if private:
                raise http_errorf(f"url host {repr(host)} resolves to a private address")

    def _is_private_host(self, host: str) -> bool:
        """Check if host resolves to private IP."""
        if host.lower() == 'localhost':
            return True

        try:
            ip = ipaddress.ip_address(host)
            return self._is_private_ip(ip)
        except ValueError:
            pass

        if self.policy.lookup_ip:
            ips = self.policy.lookup_ip(host)
        else:
            try:
                _, ips = socket.gethostbyname_ex(host)
            except socket.gaierror:
                return False

        for ip_str in ips:
            try:
                ip = ipaddress.ip_address(ip_str)
                if self._is_private_ip(ip):
                    return True
            except ValueError:
                continue
        return False

    def _is_private_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if IP is private."""
        return (
            ip.is_private or
            not ip.is_global or
            ip.is_link_local or
            ip.is_loopback or
            ip.is_reserved or
            ip.is_unspecified
        )


# Default global configuration
def _new_default_global_config() -> GlobalConfig:
    return GlobalConfig(
        timeout=0.0,
        max_redirects=10,
        follow_redirects=True,
        max_response_bytes=0,
        default_user_agent="kniferpy/vresty",
        cookie_disabled=False,
        headers={}
    )

_global_config = _new_default_global_config()
default_global_max_response_bytes = 100 * 1024 * 1024  # 100MB


def _clone_headers(headers: HeaderValues) -> HeaderValues:
    """Clone header values."""
    cloned: HeaderValues = {}
    for k, v in headers.items():
        cloned[k] = list(v)
    return cloned


def _isolated_global_config() -> GlobalConfig:
    """Create an isolated global config with defaults."""
    cfg = GlobalConfig(
        timeout=0.0,
        max_redirects=10,
        follow_redirects=True,
        max_response_bytes=0,
        default_user_agent="kniferpy/vresty",
        cookie_disabled=False,
        headers={}
    )
    return cfg


class Client:
    """Client is an explicit request factory with a captured configuration snapshot.
    Use it when code should not read package-level global defaults on every request.
    """

    def __init__(self, cfg: GlobalConfig, opts: list[RequestOption]):
        self.cfg = cfg
        self.opts = list(opts)

    def new_request(self, method: str, raw_url: str, opts: list[RequestOption]) -> HTTPRequest:
        """Create a new request from the Client's captured configuration."""
        all_opts = list(self.opts) + list(opts)
        return new_request_with_config(method, raw_url, self.cfg, *all_opts)

    def new_safe_request(self, method: str, raw_url: str, opts: list[RequestOption]) -> HTTPRequest:
        """Create a safe request from the Client's captured configuration."""
        safe_opts: list[RequestOption] = [
            lambda r: with_url_policy(URLPolicy(
                allowed_schemes=["http", "https"],
                reject_private=True
            ))(r),
            lambda r: r.timeout(10.0),
            lambda r: r.max_redirects(10),
            lambda r: (setattr(r, 'max_response', default_global_max_response_bytes) or r),
        ]
        all_opts = safe_opts + list(self.opts) + list(opts)
        return new_request_with_config(method, raw_url, self.cfg, *all_opts)

    def get(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        """Create a GET request from the Client's captured configuration."""
        return self.new_request(Method.GET, raw_url, list(opts))

    def get_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        """Create a safe GET request from the Client's captured configuration."""
        return self.new_safe_request(Method.GET, raw_url, list(opts))

    def post(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        """Create a POST request from the Client's captured configuration."""
        return self.new_request(Method.POST, raw_url, list(opts))

    def post_safe(self, raw_url: str, *opts: RequestOption) -> HTTPRequest:
        """Create a safe POST request from the Client's captured configuration."""
        return self.new_safe_request(Method.POST, raw_url, list(opts))


def new_client(*opts: ClientOption) -> Client:
    """NewClient creates a request factory using the current global configuration snapshot."""
    c = Client(cfg=snapshot_global_config(), opts=[])
    for opt in opts:
        if opt:
            opt(c)
    return c


def new_isolated_client(*opts: ClientOption) -> Client:
    """NewIsolatedClient creates a request factory without reading package-level global defaults."""
    c = Client(cfg=_isolated_global_config(), opts=[])
    for opt in opts:
        if opt:
            opt(c)
    return c


def new_client_with_config(cfg: GlobalConfig, opts: list[RequestOption]) -> Client:
    """NewClientWithConfig creates a request factory from an explicit configuration snapshot."""
    return Client(cfg=cfg, opts=list(opts))


def with_client_global_config(cfg: GlobalConfig) -> ClientOption:
    """WithClientGlobalConfig sets the configuration snapshot used by a Client."""
    def _opt(c: Client) -> None:
        c.cfg = cfg
    return _opt


def with_client_request_options(opts: list[RequestOption]) -> ClientOption:
    """WithClientRequestOptions sets request options applied to every request created by a Client."""
    def _opt(c: Client) -> None:
        c.opts = list(opts)
    return _opt


def with_global_config(cfg: GlobalConfig) -> RequestOption:
    """WithGlobalConfig initializes request defaults from a captured global configuration snapshot."""
    def _opt(r: HTTPRequest) -> None:
        follow = cfg.follow_redirects
        r._headers = _clone_headers(cfg.headers)
        r._timeout = cfg.timeout
        r._follow_redirects = follow
        r._max_redirects = cfg.max_redirects
        r.max_response = cfg.max_response_bytes
        r._user_agent = cfg.default_user_agent
        r.cookie_off = cfg.cookie_disabled
    return _opt


def with_timeout(d: float) -> RequestOption:
    """WithTimeout sets a per-request timeout in seconds."""
    return lambda r: r.timeout(d)


def with_header(name: str, value: str) -> RequestOption:
    """WithHeader sets one per-request header."""
    return lambda r: r.header(name, value)


def with_headers(headers: dict[str, str]) -> RequestOption:
    """WithHeaders sets per-request headers in batch."""
    return lambda r: r.headers(headers)


def with_follow_redirects(b: bool) -> RequestOption:
    """WithFollowRedirects sets per-request redirect behavior."""
    return lambda r: r.follow_redirects(b)


def with_max_redirects(n: int) -> RequestOption:
    """WithMaxRedirects sets the per-request redirect limit."""
    return lambda r: r.max_redirects(n)


def with_tls_config(cfg: ssl.SSLContext) -> RequestOption:
    """WithTLSConfig sets a per-request TLS config."""
    return lambda r: r.tls_config(cfg)


def with_session(session: requests.Session) -> RequestOption:
    """WithSession sets a per-request requests session."""
    return lambda r: r.session_client(session)


def with_session_factory(factory: Callable[[], requests.Session]) -> RequestOption:
    """WithSessionFactory sets a per-request session factory."""
    return lambda r: r.session_factory(factory)


def with_user_agent(ua: str) -> RequestOption:
    """WithUserAgent sets a per-request User-Agent."""
    def _opt(r: HTTPRequest) -> None:
        r._user_agent = ua
        if r._user_agent and Header.USER_AGENT not in r._headers:
            r.header(Header.USER_AGENT, ua)
    return _opt


def with_cookie_disabled(disabled: bool) -> RequestOption:
    """WithCookieDisabled sets per-request cookie management behavior."""
    return lambda r: setattr(r, 'cookie_off', disabled) or r


def with_content_type(ct: str) -> RequestOption:
    """WithContentType sets a per-request Content-Type at construction time."""
    return lambda r: r.content_type(ct)


def with_charset(charset: str) -> RequestOption:
    """WithCharset sets a per-request charset at construction time."""
    return lambda r: r.charset(charset)


def with_json_marshal_func(marshal: Callable[[Any], bytes]) -> RequestOption:
    """WithJSONMarshalFunc sets the JSON marshal provider used by request body encoding."""
    return lambda r: setattr(r, 'json_marshal', marshal) or r


def with_json_unmarshal_func(unmarshal: Callable[[bytes], Any]) -> RequestOption:
    """WithJSONUnmarshalFunc sets the JSON unmarshal provider used by response decoding."""
    return lambda r: setattr(r, 'json_unmarshal', unmarshal) or r


def with_max_decode_bytes(max_bytes: int) -> RequestOption:
    """WithMaxDecodeBytes limits bytes read before custom JSON unmarshalling. Non-positive means unlimited."""
    return lambda r: setattr(r, 'max_decode', max_bytes) or r


def with_max_response_bytes(max_bytes: int) -> RequestOption:
    """WithMaxResponseBytes limits response bytes read into memory. Non-positive means unlimited."""
    return lambda r: setattr(r, 'max_response', max_bytes) or r


def with_url_policy(policy: URLPolicy) -> RequestOption:
    """WithURLPolicy sets SSRF-oriented validation for the request URL and redirect targets."""
    p = URLPolicy(
        allowed_schemes=list(policy.allowed_schemes),
        allowed_hosts=list(policy.allowed_hosts),
        reject_private=policy.reject_private,
        lookup_ip=policy.lookup_ip
    )
    return lambda r: r.set_url_policy(p)


def with_allowed_hosts(*hosts: str) -> RequestOption:
    """WithAllowedHosts restricts Safe requests to the provided host names."""
    def _opt(r: HTTPRequest) -> None:
        if r._url_policy is None:
            r._url_policy = URLPolicy(
                allowed_schemes=["http", "https"],
                reject_private=True
            )
        r._url_policy.allowed_hosts = list(hosts)
    return _opt


def get(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Get creates a GET request.

    Security: Get is for trusted URLs. Use GetSafe for untrusted URLs.
    """
    return new_request(Method.GET, raw_url, *opts)


def get_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """GetSafe creates a GET request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.GET, raw_url, *opts)


def post(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Post creates a POST request.

    Security: Post is for trusted URLs. Use PostSafe for untrusted URLs.
    """
    return new_request(Method.POST, raw_url, *opts)


def post_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """PostSafe creates a POST request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.POST, raw_url, *opts)


def put(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Put creates a PUT request.

    Security: Put is for trusted URLs. Use PutSafe when the URL is untrusted.
    """
    return new_request(Method.PUT, raw_url, *opts)


def put_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """PutSafe creates a PUT request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.PUT, raw_url, *opts)


def delete(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Delete creates a DELETE request.

    Security: Delete is for trusted URLs. Use DeleteSafe when the URL is untrusted.
    """
    return new_request(Method.DELETE, raw_url, *opts)


def delete_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """DeleteSafe creates a DELETE request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.DELETE, raw_url, *opts)


def patch(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Patch creates a PATCH request.

    Security: Patch is for trusted URLs. Use PatchSafe when the URL is untrusted.
    """
    return new_request(Method.PATCH, raw_url, *opts)


def patch_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """PatchSafe creates a PATCH request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.PATCH, raw_url, *opts)


def head(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Head creates a HEAD request.

    Security: Head is for trusted URLs. Use HeadSafe when the URL is untrusted.
    """
    return new_request(Method.HEAD, raw_url, *opts)


def head_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """HeadSafe creates a HEAD request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.HEAD, raw_url, *opts)


def options(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """Options creates an OPTIONS request.

    Security: Options is for trusted URLs. Use OptionsSafe for untrusted URLs.
    """
    return new_request(Method.OPTIONS, raw_url, *opts)


def options_safe(raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """OptionsSafe creates an OPTIONS request with SSRF-oriented safety checks enabled."""
    return new_safe_request(Method.OPTIONS, raw_url, *opts)


def new_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """NewRequest creates a request by method.

    Security: NewRequest is for trusted URLs unless callers provide WithURLPolicy
    with RejectPrivate enabled. Use NewSafeRequest for untrusted URLs.
    """
    return new_request_with_config(method, raw_url, snapshot_global_config(), *opts)


def new_safe_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """NewSafeRequest creates a request with SSRF-oriented safety checks enabled."""
    safe_opts: list[RequestOption] = [
        with_url_policy(URLPolicy(
            allowed_schemes=["http", "https"],
            reject_private=True
        )),
        with_timeout(10.0),
        with_max_redirects(10),
        with_max_response_bytes(default_global_max_response_bytes),
    ]
    all_opts = safe_opts + list(opts)
    return new_request_with_config(method, raw_url, snapshot_global_config(), *all_opts)


def new_isolated_request(method: str, raw_url: str, *opts: RequestOption) -> HTTPRequest:
    """NewIsolatedRequest creates a request without reading package-level global defaults."""
    return new_request_with_config(method, raw_url, _isolated_global_config(), *opts)


def new_request_with_config(method: str, raw_url: str, cfg: GlobalConfig, *opts: RequestOption) -> HTTPRequest:
    """NewRequestWithConfig creates a request from an explicit global configuration snapshot.

    Security: NewRequestWithConfig is for trusted URLs unless callers provide
    WithURLPolicy with RejectPrivate enabled. Use NewSafeRequest for untrusted URLs.
    """
    follow = cfg.follow_redirects
    r = HTTPRequest()
    r.method = method
    r.raw_url = raw_url
    r.query_params = {}
    r._headers = _clone_headers(cfg.headers)
    r._charset = "UTF-8"
    r._timeout = cfg.timeout
    r._follow_redirects = follow
    r._max_redirects = cfg.max_redirects
    r.max_response = cfg.max_response_bytes
    r._user_agent = cfg.default_user_agent
    r.cookie_off = cfg.cookie_disabled

    for opt in opts:
        if opt:
            opt(r)

    return r


def get_string_e(raw_url: str) -> tuple[str, HTTPError | None]:
    """GetStringE sends a GET request and returns response body as string or an error."""
    return get_string_e_with_options(raw_url)


def get_string_e_with_options(raw_url: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """GetStringEWithOptions sends a GET request with options and returns response body as string or an error."""
    req = get(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def get_string_safe_e(raw_url: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """GetStringSafeE sends a safe GET request and returns response body as string or an error."""
    req = get_safe(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def get_with_timeout_e(raw_url: str, timeout: float) -> tuple[str, HTTPError | None]:
    """GetWithTimeoutE sends a GET request with a timeout and returns response body or an error."""
    return get_with_timeout_e_with_options(raw_url, timeout)


def get_with_timeout_e_with_options(raw_url: str, timeout: float, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """GetWithTimeoutEWithOptions sends a GET request with a timeout and custom options."""
    all_opts = list(opts) + [with_timeout(timeout)]
    return get_string_e_with_options(raw_url, *all_opts)


def get_with_params_e(raw_url: str, params: dict[str, Any]) -> tuple[str, HTTPError | None]:
    """GetWithParamsE sends a GET request with form parameters and returns response body or an error."""
    return get_with_params_e_with_options(raw_url, params)


def get_with_params_e_with_options(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """GetWithParamsEWithOptions sends a GET request with form parameters and custom options."""
    all_opts: list[RequestOption] = []
    for k, v in params.items():
        all_opts.append(lambda r, k=k, v=v: r.query(k, v))
    all_opts.extend(opts)
    return get_string_e_with_options(raw_url, *all_opts)


def post_string_e(raw_url: str, body: str) -> tuple[str, HTTPError | None]:
    """PostStringE posts a string body and returns response body or an error."""
    return post_string_e_with_options(raw_url, body)


def post_string_e_with_options(raw_url: str, body: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostStringEWithOptions posts a string body with options and returns response body or an error."""
    req = post(raw_url, *opts)
    req.body_string(body)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def post_string_safe_e(raw_url: str, body: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostStringSafeE posts a string body with SSRF-oriented safety checks enabled."""
    req = post_safe(raw_url, *opts)
    req.body_string(body)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def post_form_e(raw_url: str, params: dict[str, Any]) -> tuple[str, HTTPError | None]:
    """PostFormE posts form parameters and returns response body or an error."""
    return post_form_e_with_options(raw_url, params)


def post_form_e_with_options(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostFormEWithOptions posts form parameters with options and returns response body or an error."""
    req = post(raw_url, *opts)
    req.form(params)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def post_form_safe_e(raw_url: str, params: dict[str, Any], *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostFormSafeE posts form parameters with SSRF-oriented safety checks enabled."""
    req = post_safe(raw_url, *opts)
    req.form(params)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def post_json_e(raw_url: str, json_str: str) -> tuple[str, HTTPError | None]:
    """PostJSONE posts JSON body and returns response body or an error."""
    return post_json_e_with_options(raw_url, json_str)


def post_json_e_with_options(raw_url: str, json_str: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostJSONEWithOptions posts JSON body with options and returns response body or an error."""
    req = post(raw_url, *opts)
    req.body_json(json_str)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def post_json_safe_e(raw_url: str, json_str: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """PostJSONSafeE posts JSON body with SSRF-oriented safety checks enabled."""
    req = post_safe(raw_url, *opts)
    req.body_json(json_str)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def download(raw_url: str, writer: io.IOBase) -> tuple[int, HTTPError | None]:
    """Download downloads rawURL into writer."""
    return download_with_options(raw_url, writer)


def download_with_options(raw_url: str, writer: io.IOBase, *opts: RequestOption) -> tuple[int, HTTPError | None]:
    """DownloadWithOptions downloads rawURL into writer with per-request options."""
    req = get(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return 0, resp.err
    writer.write(resp.body_bytes())
    return len(resp.body_bytes()), None


def download_safe(raw_url: str, writer: io.IOBase, *opts: RequestOption) -> tuple[int, HTTPError | None]:
    """DownloadSafe downloads rawURL into writer with SSRF-oriented safety checks enabled."""
    req = get_safe(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return 0, resp.err
    writer.write(resp.body_bytes())
    return len(resp.body_bytes()), None


def download_file(raw_url: str, dest: str, *save_opts: SaveOptions) -> tuple[int, HTTPError | None]:
    """DownloadFile downloads rawURL to dest."""
    return download_file_with_options(raw_url, dest, [], *save_opts)


def download_file_with_options(
    raw_url: str,
    dest: str,
    request_opts: list[RequestOption],
    *save_opts: SaveOptions
) -> tuple[int, HTTPError | None]:
    """DownloadFileWithOptions downloads rawURL to dest with per-request and per-save options."""
    opts = SaveOptions()
    opts.file_perm = 0o644
    opts.dir_perm = 0o755
    opts.overwrite = True
    opts.create_parents = True

    for opt in save_opts:
        if opt:
            for k, v in opt.__dict__.items():
                if v is not None:
                    setattr(opts, k, v)

    dest_path = Path(dest)

    if dest_path.is_dir():
        if opts.default_filename:
            dest_path = dest_path / opts.default_filename
        else:
            parsed = urlparse(raw_url)
            filename = parsed.path.split('/')[-1]
            if not filename:
                filename = 'download'
            dest_path = dest_path / filename

    if dest_path.exists() and not opts.overwrite:
        return 0, new_http_error(f"file {dest} already exists and overwrite is false", None)

    parent = dest_path.parent
    if not parent.exists():
        if opts.create_parents:
            parent.mkdir(parents=True, exist_ok=True)
        else:
            return 0, new_http_error(f"parent directory {parent} does not exist", None)

    req = get(raw_url, *request_opts)
    resp = req.execute()
    if resp.err:
        return 0, resp.err

    dest_path.write_bytes(resp.body_bytes())
    return len(resp.body_bytes()), None


def download_file_safe(raw_url: str, dest: str, *save_opts: SaveOptions) -> tuple[int, HTTPError | None]:
    """DownloadFileSafe downloads rawURL to dest with SSRF-oriented safety checks enabled."""
    return download_file_safe_with_options(raw_url, dest, [], *save_opts)


def download_file_safe_with_options(
    raw_url: str,
    dest: str,
    request_opts: list[RequestOption],
    *save_opts: SaveOptions
) -> tuple[int, HTTPError | None]:
    """DownloadFileSafeWithOptions downloads rawURL to dest with SSRF-oriented safety checks enabled."""
    safe_opts = list(request_opts)
    safe_opts.insert(0, lambda r: with_url_policy(URLPolicy(
        allowed_schemes=["http", "https"],
        reject_private=True
    ))(r))
    return download_file_with_options(raw_url, dest, safe_opts, *save_opts)


def download_bytes_e(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    """DownloadBytesE downloads and returns bytes or an error."""
    return download_bytes_e_with_options(raw_url, *opts)


def download_bytes_e_with_options(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    """DownloadBytesEWithOptions downloads and returns bytes with per-request options or an error."""
    req = get(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return b'', resp.err
    return resp.body_bytes(), None


def download_bytes_safe_e(raw_url: str, *opts: RequestOption) -> tuple[bytes, HTTPError | None]:
    """DownloadBytesSafeE downloads and returns bytes with SSRF-oriented safety checks enabled."""
    req = get_safe(raw_url, *opts)
    resp = req.execute()
    if resp.err:
        return b'', resp.err
    return resp.body_bytes(), None


def download_string_e(raw_url: str, custom_charset: str = "") -> tuple[str, HTTPError | None]:
    """DownloadStringE downloads remote text and returns an error on request failure."""
    return download_string_e_with_options(raw_url, custom_charset)


def download_string_e_with_options(raw_url: str, custom_charset: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """DownloadStringEWithOptions downloads remote text with per-request options and returns an error on failure."""
    req = get(raw_url, *opts)
    if custom_charset:
        req.charset(custom_charset)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def download_string_safe_e(raw_url: str, custom_charset: str, *opts: RequestOption) -> tuple[str, HTTPError | None]:
    """DownloadStringSafeE downloads remote text with SSRF-oriented safety checks enabled."""
    req = get_safe(raw_url, *opts)
    if custom_charset:
        req.charset(custom_charset)
    resp = req.execute()
    if resp.err:
        return "", resp.err
    return resp.body_text(), None


def set_global_timeout(d: float) -> None:
    """SetGlobalTimeout sets the global HTTP timeout in seconds."""
    global _global_config
    _global_config.timeout = d


def get_global_timeout() -> float:
    """GetGlobalTimeout returns the global HTTP timeout."""
    return _global_config.timeout


def set_global_max_redirects(n: int) -> None:
    """SetGlobalMaxRedirects sets the global maximum redirect count."""
    global _global_config
    _global_config.max_redirects = n


def get_global_max_redirects() -> int:
    """GetGlobalMaxRedirects returns the global maximum redirect count."""
    return _global_config.max_redirects


def set_global_max_response_bytes(n: int) -> None:
    """SetGlobalMaxResponseBytes sets the global maximum response bytes read into memory.
    Non-positive values disable the limit.
    """
    global _global_config
    _global_config.max_response_bytes = n


def get_global_max_response_bytes() -> int:
    """GetGlobalMaxResponseBytes returns the global maximum response bytes read into memory."""
    return _global_config.max_response_bytes


def set_global_follow_redirects(b: bool) -> None:
    """SetGlobalFollowRedirects sets whether redirects are followed globally."""
    global _global_config
    _global_config.follow_redirects = b


def get_global_follow_redirects() -> bool:
    """GetGlobalFollowRedirects reports whether redirects are followed globally."""
    return _global_config.follow_redirects


def set_global_user_agent(ua: str) -> None:
    """SetGlobalUserAgent sets the global default User-Agent."""
    global _global_config
    _global_config.default_user_agent = ua


def get_global_user_agent() -> str:
    """GetGlobalUserAgent returns the global default User-Agent."""
    return _global_config.default_user_agent


def snapshot_global_config() -> GlobalConfig:
    """SnapshotGlobalConfig returns a copy of the package-level resty defaults."""
    return GlobalConfig(
        timeout=_global_config.timeout,
        max_redirects=_global_config.max_redirects,
        follow_redirects=_global_config.follow_redirects,
        max_response_bytes=_global_config.max_response_bytes,
        default_user_agent=_global_config.default_user_agent,
        cookie_disabled=_global_config.cookie_disabled,
        headers=_clone_headers(_global_config.headers)
    )


def reset_global_config() -> None:
    """ResetGlobalConfig restores package-level resty defaults, including headers and cookies."""
    global _global_config
    _global_config = _new_default_global_config()


def configure_global_config(cfg: GlobalConfig) -> None:
    """ConfigureGlobalConfig replaces package-level resty defaults with cfg."""
    global _global_config
    _global_config = GlobalConfig(
        timeout=cfg.timeout,
        max_redirects=cfg.max_redirects,
        follow_redirects=cfg.follow_redirects,
        max_response_bytes=cfg.max_response_bytes,
        default_user_agent=cfg.default_user_agent,
        cookie_disabled=cfg.cookie_disabled,
        headers=_clone_headers(cfg.headers)
    )


def with_scoped_global_config(cfg: GlobalConfig, fn: Callable[[], None]) -> None:
    """WithScopedGlobalConfig runs fn with cfg installed as package-level resty defaults,
    then restores the previous defaults.
    """
    old = snapshot_global_config()
    try:
        configure_global_config(cfg)
        fn()
    finally:
        configure_global_config(old)


def set_global_header(name: str, value: str) -> None:
    """SetGlobalHeader sets a global HTTP header."""
    _global_config.headers[name] = [value]


def add_global_header(name: str, value: str) -> None:
    """AddGlobalHeader adds a global HTTP header value."""
    if name not in _global_config.headers:
        _global_config.headers[name] = []
    _global_config.headers[name].append(value)


def remove_global_header(name: str) -> None:
    """RemoveGlobalHeader removes a global HTTP header."""
    if name in _global_config.headers:
        del _global_config.headers[name]


def clone_global_headers() -> HeaderValues:
    """CloneGlobalHeaders returns cloned global headers."""
    return _clone_headers(_global_config.headers)


def close_cookie() -> None:
    """CloseCookie disables global cookie management."""
    _global_config.cookie_disabled = True


def build_basic_auth(user: str, password: str) -> str:
    """BuildBasicAuth builds a Basic authorization value."""
    import base64
    return f"Basic {base64.b64encode(f'{user}:{password}'.encode()).decode()}"


def with_charset_regexp(re_obj: re.Pattern) -> CharsetOption:
    """WithCharsetRegexp sets the regexp used by GetCharsetFromContentTypeWithOptions."""
    def _opt(ctx: CharsetContext) -> None:
        ctx.charset_re = re_obj
    return _opt


def with_meta_charset_regexp(re_obj: re.Pattern) -> CharsetOption:
    """WithMetaCharsetRegexp sets the regexp used by GetCharsetFromHTMLWithOptions."""
    def _opt(ctx: CharsetContext) -> None:
        ctx.meta_charset_re = re_obj
    return _opt


def is_https(raw_url: str) -> bool:
    """IsHTTPS reports whether the given URL is https."""
    parsed = urlparse(raw_url)
    return parsed.scheme.lower() == 'https'


def is_http(raw_url: str) -> bool:
    """IsHTTP reports whether the given URL is http."""
    parsed = urlparse(raw_url)
    return parsed.scheme.lower() == 'http'


def to_params(m: dict[str, Any]) -> str:
    """ToParams converts a map to a URL query string."""
    params: list[tuple[str, str]] = []
    for k, v in m.items():
        params.append((k, str(v)))
    return urlencode(params)


def url_with_form(raw_url: str, form: dict[str, Any]) -> str:
    """URLWithForm appends form values to a URL."""
    query = to_params(form)
    if '?' in raw_url:
        return raw_url + '&' + query
    return raw_url + '?' + query


def build_content_type(content_type: str, charset: str) -> str:
    """BuildContentType builds a Content-Type string with charset."""
    if not charset:
        return content_type
    return f"{content_type}; charset={charset}"


def guess_content_type(body: str) -> str:
    """GuessContentType guesses Content-Type from the body."""
    body = body.lstrip()
    if not body:
        return ""
    if body.startswith('{') or body.startswith('['):
        return ContentType.JSON
    if body.startswith('<!DOCTYPE') or body.startswith('<html'):
        return ContentType.TEXT_HTML
    if body.startswith('<?xml'):
        return ContentType.XML
    return ContentType.TEXT_PLAIN


def is_default_content_type(content_type: str) -> bool:
    """IsDefaultContentType reports whether the value is a default Content-Type."""
    ct = content_type.split(';')[0].strip().lower()
    return ct in (
        ContentType.TEXT_PLAIN.lower(),
        ContentType.TEXT_HTML.lower(),
        ContentType.TEXT_XML.lower(),
        ContentType.XML.lower(),
        ContentType.JSON.lower(),
    )


def is_form_url_encoded(content_type: str) -> bool:
    """IsFormURLEncoded reports whether the value is application/x-www-form-urlencoded."""
    ct = content_type.split(';')[0].strip().lower()
    return ct == ContentType.FORM_URL_ENCODED.lower()


def get_charset_from_content_type(ct: str) -> str:
    """GetCharsetFromContentType extracts charset from Content-Type."""
    return get_charset_from_content_type_with_options(ct)


def get_charset_from_content_type_with_options(ct: str, *opts: CharsetOption) -> str:
    """GetCharsetFromContentTypeWithOptions extracts charset from Content-Type with options."""
    ctx = CharsetContext()
    for opt in opts:
        opt(ctx)
    if not ct:
        return ""
    match = ctx.charset_re.search(ct)
    if match:
        return match.group(1)
    return ""


def get_charset_from_html(html: str) -> str:
    """GetCharsetFromHTML extracts charset from HTML meta tags."""
    return get_charset_from_html_with_options(html)


def get_charset_from_html_with_options(html: str, *opts: CharsetOption) -> str:
    """GetCharsetFromHTMLWithOptions extracts charset from HTML meta tags with options."""
    ctx = CharsetContext()
    for opt in opts:
        opt(ctx)
    match = ctx.meta_charset_re.search(html)
    if match:
        return match.group(1)
    return ""


# MIME type mapping by extension
_mime_types: dict[str, str] = {
    '.html': ContentType.TEXT_HTML,
    '.htm': ContentType.TEXT_HTML,
    '.json': ContentType.JSON,
    '.xml': ContentType.XML,
    '.txt': ContentType.TEXT_PLAIN,
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.pdf': 'application/pdf',
    '.zip': 'application/zip',
    '.gz': 'application/gzip',
    '.tar': 'application/x-tar',
    '.webp': 'image/webp',
}


def get_mime_type(filename: str) -> str:
    """GetMimeType returns the MIME type by file extension."""
    ext = Path(filename).suffix.lower()
    return _mime_types.get(ext, ContentType.OCTET_STREAM)


# ---------------------------------------------------------------------------
# Default client provider
# ---------------------------------------------------------------------------

_default_client_provider: Callable[[], "Client"] | None = None


def configure_default_resty_client_provider(provider: Callable[[], "Client"] | None) -> None:
    global _default_client_provider
    _default_client_provider = provider


def reset_default_resty_client_provider() -> None:
    global _default_client_provider
    _default_client_provider = None
