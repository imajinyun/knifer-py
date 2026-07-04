from __future__ import annotations

from urllib.parse import ParseResult

from kniferpy.internal import urlx
from kniferpy.internal.urlx import URLBuilder


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


def is_private_host(host: str, *, resolver: urlx.Resolver | None = None) -> bool:
    return urlx.is_private_host(host, resolver=resolver)


# ── URL encoding / decoding ─────────────────────────────────────────────────


def encode_query(value: str) -> str:
    return urlx.encode_query(value)


def decode_query(value: str) -> str:
    return urlx.decode_query(value)


def encode_path_segment(value: str) -> str:
    return urlx.encode_path_segment(value)


def encode_path(value: str) -> str:
    return urlx.encode_path(value)


def encode_fragment(value: str) -> str:
    return urlx.encode_fragment(value)


def decode(value: str) -> str:
    return urlx.decode(value)


def decode_for_path(value: str) -> str:
    return urlx.decode_for_path(value)


# ── URL builder ─────────────────────────────────────────────────────────────


def new_url_builder() -> URLBuilder:
    return urlx.new_url_builder()


def parse_url_builder(raw: str) -> URLBuilder:
    return urlx.parse_url_builder(raw)


# ── Data URI ────────────────────────────────────────────────────────────────


def data_uri(mime_type: str, charset: str, encoding: str, data: str) -> str:
    return urlx.data_uri(mime_type, charset, encoding, data)


def data_uri_base64(mime_type: str, data: str) -> str:
    return urlx.data_uri_base64(mime_type, data)


# ── URL helpers ─────────────────────────────────────────────────────────────


def is_http_url(raw: str) -> bool:
    return urlx.is_http_url(raw)


def is_https_url(raw: str) -> bool:
    return urlx.is_https_url(raw)


def is_absolute_url(raw: str) -> bool:
    return urlx.is_absolute_url(raw)


def build_query(params: dict[str, str | int | float | bool | None]) -> str:
    return urlx.build_query(params)


def append_query(raw_url: str, params: dict[str, str | int | float | bool | None]) -> str:
    return urlx.append_query(raw_url, params)