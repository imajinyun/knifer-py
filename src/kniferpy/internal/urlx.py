from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse, urlunparse

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
