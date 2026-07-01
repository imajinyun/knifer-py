from __future__ import annotations

from urllib.parse import ParseResult

from kniferpy.internal import urlx


def parse(raw_url: str) -> ParseResult:
    return urlx.parse(raw_url)


def normalize_query(raw_url: str) -> str:
    return urlx.normalize_query(raw_url)


def add_query(raw_url: str, params: dict[str, str | int | float | bool | None]) -> str:
    return urlx.add_query(raw_url, params)


def get_query(raw_url: str) -> dict[str, str]:
    return urlx.get_query(raw_url)


def remove_query(raw_url: str, keys: set[str]) -> str:
    return urlx.remove_query(raw_url, keys)


def redact_userinfo(raw_url: str, *, replacement: str = "***") -> str:
    return urlx.redact_userinfo(raw_url, replacement=replacement)


def validate_http_url(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    resolver: urlx.Resolver | None = None,
) -> bool:
    return urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
