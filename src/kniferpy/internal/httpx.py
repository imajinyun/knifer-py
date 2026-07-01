from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, TypeAlias

import requests

from kniferpy.internal import filex, urlx
from kniferpy.verr import DecodeError, SecurityError

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


class ResponseLike(Protocol):
    text: str
    content: bytes

    def raise_for_status(self) -> None: ...


class SessionLike(Protocol):
    def get(self, url: str, timeout: float) -> ResponseLike: ...

    def post(self, url: str, json: JSONValue, timeout: float) -> ResponseLike: ...


def get_string_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> str:
    response = get_bytes_safe(
        raw_url,
        allowed_hosts=allowed_hosts,
        timeout=timeout,
        max_bytes=max_bytes,
        resolver=resolver,
        session=session,
    )
    return response.decode("utf-8")


def get_bytes_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    max_bytes: int = 1_048_576,
    resolver: urlx.Resolver | None = None,
    session: SessionLike | None = None,
) -> bytes:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.get(raw_url, timeout=timeout)
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise SecurityError(
            "response exceeds max_bytes",
            code="http.response_too_large",
            context={"size": len(response.content), "max_bytes": max_bytes},
        )
    return response.content


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
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts, resolver=resolver)
    client = session or requests.Session()
    response = client.post(raw_url, json=payload, timeout=timeout)
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise SecurityError(
            "response exceeds max_bytes",
            code="http.response_too_large",
            context={"size": len(response.content), "max_bytes": max_bytes},
        )
    decoded = _to_json_value(json.loads(response.content))
    if not isinstance(decoded, dict):
        raise SecurityError("response JSON is not an object", code="http.response_not_object")
    return decoded


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
