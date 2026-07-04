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

    def put(self, url: str, json: JSONValue, timeout: float) -> ResponseLike: ...

    def delete(self, url: str, timeout: float) -> ResponseLike: ...

    def patch(self, url: str, json: JSONValue, timeout: float) -> ResponseLike: ...

    def head(self, url: str, timeout: float) -> ResponseLike: ...

    def options(self, url: str, timeout: float) -> ResponseLike: ...


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


# ========== HTTPResponse ==========


class HTTPResponse:
    def __init__(self, response: ResponseLike) -> None:
        self._response = response

    def bytes(self) -> bytes:
        return self._response.content

    def body(self) -> str:
        return self._response.text

    def status_code(self) -> int:
        return self._response.status_code

    def headers(self) -> dict[str, str]:
        return dict(self._response.headers)

    def content_type(self) -> str:
        return self._response.headers.get("content-type", "")

    def content_length(self) -> int:
        val = self._response.headers.get("content-length", "0")
        try:
            return int(val)
        except ValueError:
            return 0

    def cookies(self) -> dict[str, str]:
        cookie_header = self._response.headers.get("set-cookie", "")
        if not cookie_header:
            return {}
        result: dict[str, str] = {}
        for part in cookie_header.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                result[k.strip()] = v.strip()
        return result

    def is_ok(self) -> bool:
        return is_ok(self.status_code())

    def close(self) -> None:
        if hasattr(self._response, "close"):
            self._response.close()

    def raw(self) -> ResponseLike:
        return self._response


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