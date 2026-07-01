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
