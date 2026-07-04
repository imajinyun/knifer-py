from __future__ import annotations

import ipaddress
import os
import re
import socket
import unicodedata
from collections.abc import Callable, Mapping
from io import IOBase
from pathlib import Path
from urllib.parse import ParseResult, parse_qsl, quote, unquote, urlencode, urljoin, urlparse, urlunparse

from kniferpy.verr import SecurityError, ValidationError

Resolver = Callable[[str], list[str]]


def parse(raw_url: str) -> ParseResult:
    return urlparse(raw_url)


def normalize_query(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    return urlunparse(parsed._replace(query=query))


def add_query(raw_url: str, params: dict[str, str | int | float | bool | None]) -> str:
    parsed = urlparse(raw_url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    pairs.extend(
        (key, _format_query_value(value)) for key, value in params.items() if value is not None
    )
    return urlunparse(parsed._replace(query=urlencode(pairs, doseq=True)))


def get_query(raw_url: str) -> dict[str, str]:
    parsed = urlparse(raw_url)
    return dict(parse_qsl(parsed.query, keep_blank_values=True))


def remove_query(raw_url: str, keys: set[str]) -> str:
    parsed = urlparse(raw_url)
    pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in keys
    ]
    return urlunparse(parsed._replace(query=urlencode(pairs, doseq=True)))


def redact_userinfo(raw_url: str, *, replacement: str = "***") -> str:
    parsed = urlparse(raw_url)
    if parsed.username is None and parsed.password is None:
        return raw_url
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=f"{replacement}@{host}"))


def validate_http_url(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    resolver: Resolver | None = None,
) -> bool:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("URL must be http(s) with a hostname", code="url.invalid")

    host = parsed.hostname.lower()
    normalized_allowed = (
        {item.lower() for item in allowed_hosts} if allowed_hosts is not None else None
    )
    if normalized_allowed is not None and host not in normalized_allowed:
        raise SecurityError(
            "host is not allowed",
            code="url.host_not_allowed",
            context={"host": host},
        )
    if is_private_host(host, resolver=resolver):
        raise SecurityError(
            "private host is not allowed",
            code="url.private_host",
            context={"host": host},
        )
    return True


def is_private_host(host: str, *, resolver: Resolver | None = None) -> bool:
    return any(_is_private_address(address) for address in _resolve_host(host, resolver=resolver))


def _resolve_host(host: str, *, resolver: Resolver | None = None) -> list[str]:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if resolver is not None:
            return resolver(host)
        try:
            return [str(item[4][0]) for item in socket.getaddrinfo(host, None)]
        except socket.gaierror as exc:
            raise ValidationError(
                "host cannot be resolved",
                code="url.resolve_failed",
                context={"host": host},
            ) from exc
    return [host]


def _is_private_address(address: str) -> bool:
    parsed = ipaddress.ip_address(address)
    return parsed.is_private or parsed.is_loopback or parsed.is_link_local


def _format_query_value(value: str | int | float | bool | None) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


# ── URL encoding / decoding ─────────────────────────────────────────────────


def encode_query(value: str) -> str:
    from urllib.parse import quote_plus

    return quote_plus(value)


def decode_query(value: str) -> str:
    from urllib.parse import unquote_plus

    return unquote_plus(value)


def encode_path_segment(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")


def encode_path(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="/")


def encode_fragment(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")


def decode(value: str) -> str:
    from urllib.parse import unquote

    return unquote(value)


def decode_for_path(value: str) -> str:
    from urllib.parse import unquote

    return unquote(value)


# ── URL builder ─────────────────────────────────────────────────────────────


class URLBuilder:
    def __init__(self) -> None:
        self._scheme: str = ""
        self._host: str = ""
        self._port: int = -1
        self._path: str = ""
        self._query_params: dict[str, str] = {}
        self._fragment: str = ""
        self._with_end_tag: bool = False

    def set_scheme(self, scheme: str) -> URLBuilder:
        self._scheme = scheme
        return self

    def scheme(self) -> str:
        return self._scheme

    def scheme_with_default(self, default_scheme: str) -> str:
        return self._scheme or default_scheme

    def set_host(self, host: str) -> URLBuilder:
        self._host = host
        return self

    def host(self) -> str:
        return self._host

    def set_port(self, port: int) -> URLBuilder:
        self._port = port
        return self

    def port(self) -> int:
        return self._port

    def port_with_default(self, default_port: int) -> int:
        return self._port if self._port >= 0 else default_port

    def authority(self) -> str:
        if self._port >= 0:
            return f"{self._host}:{self._port}"
        return self._host

    def set_with_end_tag(self, with_end_tag: bool) -> URLBuilder:
        self._with_end_tag = with_end_tag
        return self

    def set_path(self, path: str) -> URLBuilder:
        self._path = path if path.startswith("/") else f"/{path}"
        return self

    def add_path(self, path: str) -> URLBuilder:
        if not self._path.endswith("/"):
            self._path += "/"
        self._path += path.strip("/")
        return self

    def add_path_segment(self, segment: str) -> URLBuilder:
        return self.add_path(segment)

    def path_string(self) -> str:
        return self._path

    def set_query(self, raw_query: str) -> URLBuilder:
        from urllib.parse import parse_qsl

        self._query_params = dict(parse_qsl(raw_query, keep_blank_values=True))
        return self

    def add_query(self, key: str, value: str | int | float | bool) -> URLBuilder:
        self._query_params[key] = _format_query_value(value)
        return self

    def query(self) -> dict[str, str]:
        return dict(self._query_params)

    def query_string(self) -> str:
        return urlencode(self._query_params, doseq=True)

    def set_fragment(self, fragment: str) -> URLBuilder:
        self._fragment = fragment
        return self

    def fragment(self) -> str:
        return self._fragment

    def build(self) -> str:
        from urllib.parse import urlunparse

        netloc = self.authority()
        fragment = self._fragment
        return urlunparse((
            self._scheme,
            netloc,
            self._path,
            "",
            self.query_string(),
            fragment,
        ))

    def __str__(self) -> str:
        return self.build()


def new_url_builder() -> URLBuilder:
    return URLBuilder()


def new_http_url_builder(host: str) -> URLBuilder:
    """Create a URLBuilder pre-initialized with scheme 'http' and given host."""
    return URLBuilder().set_scheme("http").set_host(host)


def parse_url_builder(raw: str) -> URLBuilder:
    parsed = urlparse(raw)
    builder = URLBuilder()
    builder.set_scheme(parsed.scheme)
    if parsed.hostname:
        builder.set_host(parsed.hostname)
    if parsed.port is not None:
        builder.set_port(parsed.port)
    builder.set_path(parsed.path)
    if parsed.query:
        builder.set_query(parsed.query)
    if parsed.fragment:
        builder.set_fragment(parsed.fragment)
    return builder


# ── Data URI ────────────────────────────────────────────────────────────────


def data_uri(mime_type: str, charset: str, encoding: str, data: str) -> str:
    charset_part = f";charset={charset}" if charset else ""
    if encoding:
        return f"data:{mime_type}{charset_part};{encoding},{data}"
    return f"data:{mime_type}{charset_part},{data}"


def data_uri_base64(mime_type: str, data: str) -> str:
    import base64

    encoded = base64.b64encode(data.encode("utf-8")).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


# ── URL helpers ─────────────────────────────────────────────────────────────


def is_http_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme == "http" or parsed.scheme == "https"


def is_https_url(raw: str) -> bool:
    return urlparse(raw).scheme == "https"


def is_absolute_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme != "" and parsed.netloc != ""


def build_query(params: dict[str, str | int | float | bool | None]) -> str:
    return urlencode({k: _format_query_value(v) for k, v in params.items() if v is not None}, doseq=True)


def append_query(raw_url: str, params: dict[str, str | int | float | bool | None]) -> str:
    return add_query(raw_url, params)


# ── File URL ──────────────────────────────────────────────────────────────────


def file_url(path: str | Path) -> str:
    """Convert a filesystem path to a ``file://`` URL."""
    p = Path(path).resolve()
    return p.as_uri()


def file_urls(*paths: str | Path) -> list[str]:
    """Convert filesystem paths to ``file://`` URLs."""
    return [file_url(p) for p in paths]


# ── URL helpers ───────────────────────────────────────────────────────────────


def host(raw_url: str) -> str:
    """Return scheme + host from a URL."""
    parsed = urlparse(raw_url)
    if parsed.scheme and parsed.hostname:
        result = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port is not None:
            result += f":{parsed.port}"
        return result
    return ""


def complete(base_url: str, relative_path: str) -> str:
    """Resolve ``relative_path`` against ``base_url``."""
    return urljoin(base_url, relative_path)


def encode_blank(raw: str) -> str:
    """Encode all Unicode blank characters as ``%20``."""
    result: list[str] = []
    for ch in raw:
        cat = unicodedata.category(ch)
        if cat == "Zs" or ch in ("\t", "\n", "\r", "\x0b", "\x0c"):
            result.append("%20")
        else:
            result.append(ch)
    return "".join(result)


def string_uri(content: str) -> str:
    """Build a ``string:`` scheme URI for content."""
    encoded = quote(content, safe="")
    return f"string:{encoded}"


def parse_http(raw: str) -> ParseResult:
    """Parse raw after encoding blank characters."""
    return urlparse(encode_blank(raw))


# ── URL encoding variants ─────────────────────────────────────────────────────


def url_encode(s: str) -> str:
    """Encode a string for URL query components."""
    return quote(s, safe="")


def url_decode(s: str) -> str:
    """Decode a URL query component; plus signs become spaces."""
    return unquote(s.replace("+", " "))


def decode_plus(s: str, *, plus_to_space: bool = True) -> str:
    """Decode percent-encoded text with control over plus-to-space conversion."""
    if plus_to_space:
        s = s.replace("+", " ")
    return unquote(s)


def encode_all(s: str) -> str:
    """Percent-encode every non-unreserved character."""
    return quote(s, safe="")


def form_url_encode(s: str) -> str:
    """Encode text for ``application/x-www-form-urlencoded``."""
    return quote(s, safe="")


# ── Path extraction ───────────────────────────────────────────────────────────


def decoded_path(raw: str) -> str:
    """Return the decoded path part of a URL."""
    parsed = urlparse(raw)
    return unquote(parsed.path)


def url_path(raw: str) -> str:
    """Return the decoded path part of a URL."""
    return decoded_path(raw)


def path(raw: str) -> tuple[str, str]:
    """Return the decoded path of a URL (Go-compat: (path, error_str))."""
    parsed = urlparse(raw)
    return unquote(parsed.path), ""


def decoded_path_from_parsed(u: ParseResult) -> str:
    """Return the decoded path from an already-parsed URL (Go DecodedPath compat)."""
    if u is None:
        return ""
    return unquote(u.path)


def to_uri(location: str, *, encode: bool = False) -> str:
    """Parse a location as a URI, optionally encoding blank characters first."""
    if encode:
        location = encode_blank(location)
    parsed = urlparse(location)
    return parsed.geturl() if parsed.scheme else location


# ── URL type checks ───────────────────────────────────────────────────────────


def is_file_url(raw: str) -> bool:
    """Check if raw uses a file-like scheme."""
    return urlparse(raw).scheme == "file"


def is_jar_url(raw: str) -> bool:
    """Check if raw uses an archive-like scheme (jar, zip, etc.)."""
    return urlparse(raw).scheme in ("jar", "zip", "vfszip", "wsjar")


def is_jar_file_url(raw: str) -> bool:
    """Check if raw is a file URL ending with ``.jar``."""
    parsed = urlparse(raw)
    if parsed.scheme != "file":
        return False
    return parsed.path.lower().endswith(".jar")


def is_http(raw: str) -> bool:
    """Check if raw uses the http scheme."""
    return urlparse(raw).scheme == "http"


def is_https(raw: str) -> bool:
    """Check if raw uses the https scheme."""
    return urlparse(raw).scheme == "https"


def _is_http_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme == "http" and parsed.netloc != ""


def _is_https_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme == "https" and parsed.netloc != ""


def is_web_url(raw: str) -> bool:
    """Check if raw is an absolute http or https URL with a host."""
    parsed = urlparse(raw)
    return parsed.scheme in ("http", "https") and parsed.netloc != ""


# ── URL normalization ─────────────────────────────────────────────────────────


def normalize(raw: str, *, encode_path: bool = False, replace_slash: bool = False) -> str:
    """Normalize a URL string with optional path encoding and slash collapsing."""
    parsed = urlparse(raw)
    path = parsed.path
    if replace_slash:
        path = re.sub(r"/+", "/", path)
    if encode_path:
        path = quote(path, safe="/")
    return urlunparse(parsed._replace(path=path))


def normalize_with_options(raw: str, *, encode_path: bool = False, replace_slash: bool = False) -> str:
    """Normalize a URL string (alias for normalize)."""
    return normalize(raw, encode_path=encode_path, replace_slash=replace_slash)


# ── Query encoding/decoding ───────────────────────────────────────────────────


def encode_query_map(m: dict[str, str | int | float | bool | None]) -> str:
    """Encode a map into a URL query string."""
    return urlencode({k: _format_query_value(v) for k, v in m.items() if v is not None}, doseq=True)


def encode_params(raw_url: str) -> str:
    """Encode the query part of a URL; leaves URLs without query unchanged."""
    parsed = urlparse(raw_url)
    if not parsed.query:
        return raw_url
    return urlunparse(parsed._replace(query=quote(parsed.query, safe="")))


def decode_query_first(params_str: str) -> dict[str, str]:
    """Parse a query string into a single-value map (first value wins)."""
    result: dict[str, str] = {}
    for key, value in parse_qsl(params_str, keep_blank_values=True):
        if key not in result:
            result[key] = value
    return result


def decode_query_map(params_str: str) -> dict[str, list[str]]:
    """Parse a query string into a multi-value map."""
    result: dict[str, list[str]] = {}
    for key, value in parse_qsl(params_str, keep_blank_values=True):
        result.setdefault(key, []).append(value)
    return result


# ── URL resource opening ──────────────────────────────────────────────────────


def _open_file(path: str) -> IOBase:
    p = Path(path).resolve()
    if not p.exists():
        raise ValidationError(message=f"file not found: {path}", code="url.file_not_found")
    return p.open("rb")


def _open_http(raw_url: str, *, timeout: float | None = None, check_status: bool = True) -> IOBase:
    import io
    import urllib.request

    try:
        resp = urllib.request.urlopen(raw_url, timeout=timeout)  # noqa: S310
        if check_status and resp.status >= 400:
            raise ValidationError(
                message=f"HTTP {resp.status} for {raw_url}",
                code="url.http_status",
                context={"status": resp.status},
            )
        return io.BytesIO(resp.read())
    except Exception as exc:
        raise ValidationError(
            message=f"failed to open {raw_url}",
            code="url.open_failed",
            context={"cause": str(exc)},
        ) from exc


def open_url(raw: str, *, timeout: float | None = None, check_status: bool = True) -> IOBase:
    """Open a URL resource for reading.

    Supports http, https, and file URLs.
    """
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        return _open_http(raw, timeout=timeout, check_status=check_status)
    if parsed.scheme == "file" or (not parsed.scheme and Path(raw).exists()):
        path = parsed.path if parsed.scheme == "file" else raw
        return _open_file(path)
    raise ValidationError(message=f"unsupported scheme: {parsed.scheme}", code="url.unsupported_scheme")


def open_safe(raw: str, *, timeout: float | None = None, check_status: bool = True) -> IOBase:
    """Open an HTTP(S) URL with secure defaults."""
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise SecurityError(
            message=f"scheme not allowed for safe open: {parsed.scheme}",
            code="url.scheme_not_allowed",
        )
    if parsed.hostname and is_private_host(parsed.hostname):
        raise SecurityError(
            message="private host not allowed for safe open",
            code="url.private_host",
            context={"host": parsed.hostname},
        )
    return _open_http(raw, timeout=timeout, check_status=check_status)


def content_length(raw: str, *, timeout: float | None = None) -> int:
    """Get the resource content length. Returns -1 if unknown."""
    try:
        f = open_url(raw, timeout=timeout, check_status=True)
        f.seek(0, 2)
        size = f.tell()
        f.close()
        return size
    except Exception:
        return -1


def content_length_safe(raw: str, *, timeout: float | None = None) -> int:
    """Get an HTTP(S) resource content length with secure defaults."""
    try:
        f = open_safe(raw, timeout=timeout, check_status=True)
        f.seek(0, 2)
        size = f.tell()
        f.close()
        return size
    except Exception:
        return -1


def size(raw: str, *, timeout: float | None = None) -> int:
    """Get the resource size (alias for content_length)."""
    return content_length(raw, timeout=timeout)


# ── Constants ─────────────────────────────────────────────────────────────────

FileURLPrefix = "file:"
URLProtocolFile = "file"
URLProtocolJar = "jar"
URLProtocolZip = "zip"
JarURLSeparator = "!/"
