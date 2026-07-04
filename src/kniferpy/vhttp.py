from __future__ import annotations

from pathlib import Path

from kniferpy.internal import httpx
from kniferpy.internal.httpx import JSONValue


def get_string_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> str:
    return httpx.get_string_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def get_bytes_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> bytes:
    return httpx.get_bytes_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def download_file_safe(
    raw_url: str,
    dst: str | Path,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 10_485_760,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> Path:
    return httpx.download_file_safe(raw_url, dst, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def get_json_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> JSONValue:
    return httpx.get_json_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def post_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> dict[str, JSONValue]:
    return httpx.post_json_safe(raw_url, payload, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def put_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> dict[str, JSONValue]:
    return httpx.put_json_safe(raw_url, payload, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def delete_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> bytes:
    return httpx.delete_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def patch_json_safe(
    raw_url: str,
    payload: JSONValue,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> dict[str, JSONValue]:
    return httpx.patch_json_safe(raw_url, payload, allowed_hosts=allowed_hosts, timeout=timeout, max_bytes=max_bytes, resolver=resolver, session=session)


def head_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> int:
    return httpx.head_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, resolver=resolver, session=session)


def options_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    resolver: httpx.urlx.Resolver | None = None,
    session: httpx.SessionLike | None = None,
) -> int:
    return httpx.options_safe(raw_url, allowed_hosts=allowed_hosts, timeout=timeout, resolver=resolver, session=session)