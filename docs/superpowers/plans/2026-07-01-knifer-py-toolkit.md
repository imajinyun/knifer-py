# kniferpy Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `kniferpy` as a Python utility toolkit aligned with `knifer-go`'s public `v*` domain facade style, using Poetry for dependency management and a local `.venv` with pytest for validation.

**Architecture:** Public APIs live in focused modules such as `kniferpy.vstr`, `kniferpy.vjson`, `kniferpy.vfile`, `kniferpy.vcrypto`, and `kniferpy.vhttp`. Internal implementation details live under `kniferpy.internal`, so application code imports stable facade modules while tests can target both facade behavior and selected internal safety contracts.

**Tech Stack:** Python 3.11+, Poetry, pytest, pytest-cov, requests, cryptography, pyjwt, ruff, mypy.

---

## Reference Model From knifer-go

`knifer-go` uses public `v*` facade packages and internal implementation packages. The Python version should keep that mental model but adapt it to Python package conventions:

| Go reference | Python package | First-release intent |
| --- | --- | --- |
| `vstr` | `kniferpy.vstr` | String predicates, trimming, case conversion, substring helpers, similarity basics. |
| `vjson` | `kniferpy.vjson` | Safe JSON parse/dump, path lookup, defaults, pretty formatting. |
| `vfile` | `kniferpy.vfile` | Bounded read/write, safe path joining, copy helpers. |
| `vcrypto`, `vrand`, `vjwt` | `kniferpy.vcrypto`, `kniferpy.vrand`, `kniferpy.vjwt` | SHA/HMAC, secure random bytes/tokens, JWT sign/verify. |
| `vhttp`, `vurl` | `kniferpy.vhttp`, `kniferpy.vurl` | Safe GET/download, allow-list checks, private-host rejection, bounded responses. |
| `vslice`, `vmap`, `vset` | `kniferpy.vseq`, `kniferpy.vdict`, `kniferpy.vset` | Pythonic collection helpers, only where they reduce repeated boilerplate. |
| `verr` | `kniferpy.verr` | Shared exception hierarchy with explicit domain errors. |

The first version should not chase full feature parity. It should make the three `knifer-go` star domains useful in Python first:

1. Safe HTTP and URL handling.
2. Safe crypto and token workflows.
3. Daily JSON and file workflows.

## Target Repository Layout

```text
kniferpy/
  pyproject.toml
  README.md
  LICENSE
  Makefile
  src/
    kniferpy/
      __init__.py
      py.typed
      verr.py
      vstr.py
      vjson.py
      vfile.py
      vcrypto.py
      vrand.py
      vjwt.py
      vurl.py
      vhttp.py
      vseq.py
      vdict.py
      vset.py
      internal/
        __init__.py
        jsonx.py
        filex.py
        cryptox.py
        urlx.py
        httpx.py
  tests/
    test_verr.py
    test_vstr.py
    test_vjson.py
    test_vfile.py
    test_vcrypto.py
    test_vrand.py
    test_vjwt.py
    test_vurl.py
    test_vhttp.py
  docs/
    architecture.md
    api-policy.md
    security.md
```

## Task 1: Bootstrap Poetry Project

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/kniferpy/__init__.py`
- Create: `src/kniferpy/py.typed`
- Create: `src/kniferpy/internal/__init__.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Create the local virtual environment**

Run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip poetry
```

Expected:

```text
Successfully installed ...
```

- [ ] **Step 2: Add Poetry metadata**

Write `pyproject.toml`:

```toml
[tool.poetry]
name = "kniferpy"
version = "0.1.0"
description = "A Python utility toolkit with focused v* domain facades."
authors = ["imajinyun"]
readme = "README.md"
license = "MIT"
packages = [{ include = "kniferpy", from = "src" }]

[tool.poetry.dependencies]
python = ">=3.11,<4.0"
requests = "^2.32.0"
cryptography = "^42.0.0"
pyjwt = "^2.8.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-cov = "^5.0.0"
ruff = "^0.5.0"
mypy = "^1.10.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
mypy_path = "src"

[build-system]
requires = ["poetry-core>=1.8.0"]
build-backend = "poetry.core.masonry.api"
```

- [ ] **Step 3: Install dependencies through Poetry into `.venv`**

Run:

```bash
.venv/bin/poetry config virtualenvs.in-project true
.venv/bin/poetry install
```

Expected:

```text
Installing dependencies from lock file
Installing the current project: kniferpy
```

- [ ] **Step 4: Add import smoke test**

Write `src/kniferpy/__init__.py`:

```python
"""Focused utility facades for daily Python development."""

__all__ = [
    "verr",
    "vstr",
    "vjson",
    "vfile",
    "vcrypto",
    "vrand",
    "vjwt",
    "vurl",
    "vhttp",
]
```

Write `src/kniferpy/internal/__init__.py`:

```python
"""Private implementation modules for kniferpy facades."""
```

Create `src/kniferpy/py.typed` as an empty marker file.

Write `tests/test_imports.py`:

```python
def test_package_imports() -> None:
    import kniferpy

    assert "vjson" in kniferpy.__all__
```

- [ ] **Step 5: Verify pytest in the local venv**

Run:

```bash
.venv/bin/python -m pytest tests/test_imports.py -q
```

Expected:

```text
1 passed
```

## Task 2: Shared Error Contract

**Files:**
- Create: `src/kniferpy/verr.py`
- Create: `tests/test_verr.py`

- [ ] **Step 1: Add failing tests for domain errors**

Write `tests/test_verr.py`:

```python
from kniferpy.verr import KniferError, ValidationError


def test_validation_error_keeps_code_and_context() -> None:
    err = ValidationError("invalid URL", code="url.invalid", context={"url": "ftp://x"})

    assert isinstance(err, KniferError)
    assert str(err) == "invalid URL"
    assert err.code == "url.invalid"
    assert err.context == {"url": "ftp://x"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_verr.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'kniferpy.verr'
```

- [ ] **Step 3: Implement error types**

Write `src/kniferpy/verr.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KniferError(Exception):
    message: str
    code: str = "knifer.error"
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class ValidationError(KniferError):
    pass


class SecurityError(KniferError):
    pass


class DecodeError(KniferError):
    pass


class CryptoError(KniferError):
    pass
```

- [ ] **Step 4: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_verr.py -q
```

Expected:

```text
1 passed
```

## Task 3: Daily String Facade

**Files:**
- Create: `src/kniferpy/vstr.py`
- Create: `tests/test_vstr.py`

- [ ] **Step 1: Add tests for the Python `vstr` baseline**

Write `tests/test_vstr.py`:

```python
from kniferpy import vstr


def test_blank_helpers() -> None:
    assert vstr.is_empty("")
    assert not vstr.is_empty(" ")
    assert vstr.is_blank(" \t\n")
    assert vstr.is_not_blank("knifer")


def test_case_helpers() -> None:
    assert vstr.to_snake_case("HelloWorld") == "hello_world"
    assert vstr.to_kebab_case("hello_world") == "hello-world"
    assert vstr.to_pascal_case("hello world") == "HelloWorld"


def test_sub_before_after() -> None:
    assert vstr.sub_before("a/b/c", "/", last=False) == "a"
    assert vstr.sub_before("a/b/c", "/", last=True) == "a/b"
    assert vstr.sub_after("a/b/c", "/", last=False) == "b/c"
    assert vstr.sub_after("a/b/c", "/", last=True) == "c"
```

- [ ] **Step 2: Implement `vstr`**

Write `src/kniferpy/vstr.py`:

```python
from __future__ import annotations

import re


def is_empty(value: str | None) -> bool:
    return value == "" or value is None


def is_not_empty(value: str | None) -> bool:
    return not is_empty(value)


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def is_not_blank(value: str | None) -> bool:
    return not is_blank(value)


def trim(value: str | None) -> str:
    return "" if value is None else value.strip()


def sub_before(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return value
    index = value.rfind(separator) if last else value.find(separator)
    return value if index < 0 else value[:index]


def sub_after(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return ""
    index = value.rfind(separator) if last else value.find(separator)
    return "" if index < 0 else value[index + len(separator) :]


def to_snake_case(value: str) -> str:
    normalized = re.sub(r"[\s\-]+", "_", value.strip())
    normalized = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", normalized)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    return normalized.lower().strip("_")


def to_kebab_case(value: str) -> str:
    return to_snake_case(value).replace("_", "-")


def to_pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[\s_\-]+", value.strip()) if part)
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vstr.py -q
```

Expected:

```text
3 passed
```

## Task 4: Daily JSON Facade

**Files:**
- Create: `src/kniferpy/internal/jsonx.py`
- Create: `src/kniferpy/vjson.py`
- Create: `tests/test_vjson.py`

- [ ] **Step 1: Add JSON tests**

Write `tests/test_vjson.py`:

```python
from kniferpy import vjson
from kniferpy.verr import DecodeError


def test_parse_obj_and_get_path() -> None:
    obj = vjson.parse_obj('{"user":{"name":"kniferpy","roles":["dev"]}}')

    assert vjson.get_path(obj, "user.name") == "kniferpy"
    assert vjson.get_path(obj, "user.roles.0") == "dev"
    assert vjson.get_path(obj, "missing", default="fallback") == "fallback"


def test_parse_obj_rejects_array() -> None:
    try:
        vjson.parse_obj("[1, 2]")
    except DecodeError as err:
        assert err.code == "json.not_object"
    else:
        raise AssertionError("expected DecodeError")


def test_dumps_pretty_is_stable() -> None:
    assert vjson.dumps_pretty({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}'
```

- [ ] **Step 2: Implement JSON internals and facade**

Write `src/kniferpy/internal/jsonx.py`:

```python
from __future__ import annotations

import json
from typing import Any

from kniferpy.verr import DecodeError


def loads(value: str | bytes | bytearray) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise DecodeError(str(exc), code="json.invalid", context={"position": exc.pos}) from exc


def dumps(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
```

Write `src/kniferpy/vjson.py`:

```python
from __future__ import annotations

from typing import Any

from kniferpy.internal import jsonx
from kniferpy.verr import DecodeError


def parse(value: str | bytes | bytearray) -> Any:
    return jsonx.loads(value)


def parse_obj(value: str | bytes | bytearray) -> dict[str, Any]:
    parsed = parse(value)
    if not isinstance(parsed, dict):
        raise DecodeError("JSON value is not an object", code="json.not_object")
    return parsed


def dumps(value: Any) -> str:
    return jsonx.dumps(value)


def dumps_pretty(value: Any) -> str:
    return jsonx.dumps(value, pretty=True)


def get_path(obj: Any, path: str, *, default: Any = None) -> Any:
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return default
            index = int(part)
            if index >= len(current):
                return default
            current = current[index]
            continue
        return default
    return current
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vjson.py -q
```

Expected:

```text
3 passed
```

## Task 5: Daily File Facade

**Files:**
- Create: `src/kniferpy/internal/filex.py`
- Create: `src/kniferpy/vfile.py`
- Create: `tests/test_vfile.py`

- [ ] **Step 1: Add safe file tests**

Write `tests/test_vfile.py`:

```python
from pathlib import Path

from kniferpy import vfile
from kniferpy.verr import SecurityError


def test_read_text_limit(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("hello", encoding="utf-8")

    assert vfile.read_text(path, max_bytes=10) == "hello"


def test_read_text_rejects_large_file(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("hello", encoding="utf-8")

    try:
        vfile.read_text(path, max_bytes=3)
    except SecurityError as err:
        assert err.code == "file.too_large"
    else:
        raise AssertionError("expected SecurityError")


def test_safe_join_rejects_traversal(tmp_path: Path) -> None:
    try:
        vfile.safe_join(tmp_path, "../escape.txt")
    except SecurityError as err:
        assert err.code == "file.path_traversal"
    else:
        raise AssertionError("expected SecurityError")
```

- [ ] **Step 2: Implement file safety helpers**

Write `src/kniferpy/internal/filex.py`:

```python
from __future__ import annotations

from pathlib import Path

from kniferpy.verr import SecurityError


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    root = Path(base).resolve()
    candidate = root.joinpath(*parts).resolve()
    if candidate != root and root not in candidate.parents:
        raise SecurityError("path escapes base directory", code="file.path_traversal")
    return candidate


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> str:
    candidate = Path(path)
    size = candidate.stat().st_size
    if size > max_bytes:
        raise SecurityError("file exceeds max_bytes", code="file.too_large", context={"size": size})
    return candidate.read_text(encoding=encoding)
```

Write `src/kniferpy/vfile.py`:

```python
from __future__ import annotations

from pathlib import Path

from kniferpy.internal import filex


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    return filex.safe_join(base, *parts)


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> str:
    return filex.read_text(path, encoding=encoding, max_bytes=max_bytes)


def write_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    Path(path).write_text(value, encoding=encoding)
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vfile.py -q
```

Expected:

```text
3 passed
```

## Task 6: Safe Crypto and Random Facades

**Files:**
- Create: `src/kniferpy/internal/cryptox.py`
- Create: `src/kniferpy/vcrypto.py`
- Create: `src/kniferpy/vrand.py`
- Create: `tests/test_vcrypto.py`
- Create: `tests/test_vrand.py`

- [ ] **Step 1: Add crypto tests**

Write `tests/test_vcrypto.py`:

```python
from kniferpy import vcrypto


def test_sha256_hex() -> None:
    assert vcrypto.sha256_hex("kniferpy") == "983b8790345a90a374d0cc2d52d2a2175dc335542f8207d70726dd8daed95342"


def test_hmac_sha256_hex() -> None:
    assert vcrypto.hmac_sha256_hex("secret", "payload") == "b82fcb791acec57859b989b430a826488ce2e479fdf92326bd0a2e8375a42ba4"
```

Write `tests/test_vrand.py`:

```python
from kniferpy import vrand


def test_secure_bytes_length() -> None:
    assert len(vrand.secure_bytes(32)) == 32


def test_secure_token_urlsafe_length() -> None:
    token = vrand.secure_token_urlsafe(16)
    assert isinstance(token, str)
    assert len(token) >= 16
```

- [ ] **Step 2: Implement crypto and random helpers**

Write `src/kniferpy/internal/cryptox.py`:

```python
from __future__ import annotations

import hashlib
import hmac


def to_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def sha256_hex(value: str | bytes) -> str:
    return hashlib.sha256(to_bytes(value)).hexdigest()


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return hmac.new(to_bytes(key), to_bytes(value), hashlib.sha256).hexdigest()
```

Write `src/kniferpy/vcrypto.py`:

```python
from __future__ import annotations

from kniferpy.internal import cryptox


def sha256_hex(value: str | bytes) -> str:
    return cryptox.sha256_hex(value)


def hmac_sha256_hex(key: str | bytes, value: str | bytes) -> str:
    return cryptox.hmac_sha256_hex(key, value)
```

Write `src/kniferpy/vrand.py`:

```python
from __future__ import annotations

import secrets


def secure_bytes(length: int) -> bytes:
    return secrets.token_bytes(length)


def secure_token_urlsafe(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vcrypto.py tests/test_vrand.py -q
```

Expected:

```text
4 passed
```

## Task 7: URL and Safe HTTP Facades

**Files:**
- Create: `src/kniferpy/internal/urlx.py`
- Create: `src/kniferpy/internal/httpx.py`
- Create: `src/kniferpy/vurl.py`
- Create: `src/kniferpy/vhttp.py`
- Create: `tests/test_vurl.py`
- Create: `tests/test_vhttp.py`

- [ ] **Step 1: Add URL safety tests**

Write `tests/test_vurl.py`:

```python
from kniferpy import vurl
from kniferpy.verr import SecurityError


def test_safe_url_allows_expected_host() -> None:
    assert vurl.validate_http_url("https://api.example.com/health", allowed_hosts={"api.example.com"})


def test_safe_url_rejects_private_host() -> None:
    try:
        vurl.validate_http_url("http://127.0.0.1:8000")
    except SecurityError as err:
        assert err.code == "url.private_host"
    else:
        raise AssertionError("expected SecurityError")


def test_safe_url_rejects_unlisted_host() -> None:
    try:
        vurl.validate_http_url("https://evil.example.com", allowed_hosts={"api.example.com"})
    except SecurityError as err:
        assert err.code == "url.host_not_allowed"
    else:
        raise AssertionError("expected SecurityError")
```

- [ ] **Step 2: Add HTTP tests with a fake session**

Write `tests/test_vhttp.py`:

```python
from kniferpy import vhttp


class FakeResponse:
    text = "ok"
    content = b"ok"

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.called_with: str | None = None

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.called_with = url
        return FakeResponse()


def test_get_string_safe_uses_provider_and_timeout() -> None:
    session = FakeSession()

    body = vhttp.get_string_safe(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        session=session,
        timeout=1.0,
    )

    assert body == "ok"
    assert session.called_with == "https://api.example.com/health"
```

- [ ] **Step 3: Implement URL and HTTP helpers**

Write `src/kniferpy/internal/urlx.py`:

```python
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from kniferpy.verr import SecurityError, ValidationError


def validate_http_url(raw_url: str, *, allowed_hosts: set[str] | None = None) -> bool:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("URL must be http(s) with a hostname", code="url.invalid")
    host = parsed.hostname.lower()
    if allowed_hosts is not None and host not in allowed_hosts:
        raise SecurityError("host is not allowed", code="url.host_not_allowed", context={"host": host})
    if _is_private_host(host):
        raise SecurityError("private host is not allowed", code="url.private_host", context={"host": host})
    return True


def _is_private_host(host: str) -> bool:
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, None)]
        except socket.gaierror:
            raise ValidationError("host cannot be resolved", code="url.resolve_failed", context={"host": host})
    return any(addr.is_private or addr.is_loopback or addr.is_link_local for addr in addresses)
```

Write `src/kniferpy/internal/httpx.py`:

```python
from __future__ import annotations

from typing import Protocol

import requests

from kniferpy.internal import urlx


class ResponseLike(Protocol):
    text: str
    content: bytes

    def raise_for_status(self) -> None: ...


class SessionLike(Protocol):
    def get(self, url: str, timeout: float) -> ResponseLike: ...


def get_string_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    session: SessionLike | None = None,
) -> str:
    urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts)
    client = session or requests.Session()
    response = client.get(raw_url, timeout=timeout)
    response.raise_for_status()
    return response.text
```

Write `src/kniferpy/vurl.py`:

```python
from __future__ import annotations

from kniferpy.internal import urlx


def validate_http_url(raw_url: str, *, allowed_hosts: set[str] | None = None) -> bool:
    return urlx.validate_http_url(raw_url, allowed_hosts=allowed_hosts)
```

Write `src/kniferpy/vhttp.py`:

```python
from __future__ import annotations

from kniferpy.internal import httpx


def get_string_safe(
    raw_url: str,
    *,
    allowed_hosts: set[str] | None = None,
    timeout: float = 10.0,
    session: httpx.SessionLike | None = None,
) -> str:
    return httpx.get_string_safe(
        raw_url,
        allowed_hosts=allowed_hosts,
        timeout=timeout,
        session=session,
    )
```

- [ ] **Step 4: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vurl.py tests/test_vhttp.py -q
```

Expected:

```text
4 passed
```

## Task 8: JWT Facade

**Files:**
- Create: `src/kniferpy/vjwt.py`
- Create: `tests/test_vjwt.py`

- [ ] **Step 1: Add JWT tests**

Write `tests/test_vjwt.py`:

```python
from kniferpy import vjwt


def test_sign_and_verify_hs256() -> None:
    token = vjwt.sign_hs256({"sub": "user-1"}, "secret")

    assert vjwt.verify_hs256(token, "secret")["sub"] == "user-1"
```

- [ ] **Step 2: Implement JWT helpers**

Write `src/kniferpy/vjwt.py`:

```python
from __future__ import annotations

from typing import Any

import jwt


def sign_hs256(payload: dict[str, Any], secret: str | bytes) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_hs256(token: str, secret: str | bytes) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_vjwt.py -q
```

Expected:

```text
1 passed
```

## Task 9: Collection Facades

**Files:**
- Create: `src/kniferpy/vseq.py`
- Create: `src/kniferpy/vdict.py`
- Create: `src/kniferpy/vset.py`
- Create: `tests/test_collections.py`

- [ ] **Step 1: Add collection tests**

Write `tests/test_collections.py`:

```python
from kniferpy import vdict, vseq, vset


def test_vseq_chunk_and_unique() -> None:
    assert vseq.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert vseq.unique([1, 1, 2, 3, 2]) == [1, 2, 3]


def test_vdict_pick_and_omit() -> None:
    obj = {"a": 1, "b": 2, "c": 3}
    assert vdict.pick(obj, {"a", "c"}) == {"a": 1, "c": 3}
    assert vdict.omit(obj, {"b"}) == {"a": 1, "c": 3}


def test_vset_operations() -> None:
    assert vset.intersection({1, 2}, {2, 3}) == {2}
    assert vset.difference({1, 2}, {2, 3}) == {1}
```

- [ ] **Step 2: Implement collection helpers**

Write `src/kniferpy/vseq.py`:

```python
from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def chunk(values: list[T], size: int) -> list[list[T]]:
    if size <= 0:
        raise ValueError("size must be positive")
    return [values[index : index + size] for index in range(0, len(values), size)]


def unique(values: Iterable[T]) -> list[T]:
    result: list[T] = []
    seen: set[T] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
```

Write `src/kniferpy/vdict.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


def pick(value: Mapping[K, V], keys: set[K]) -> dict[K, V]:
    return {key: item for key, item in value.items() if key in keys}


def omit(value: Mapping[K, V], keys: set[K]) -> dict[K, V]:
    return {key: item for key, item in value.items() if key not in keys}
```

Write `src/kniferpy/vset.py`:

```python
from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def intersection(left: set[T], right: set[T]) -> set[T]:
    return left & right


def difference(left: set[T], right: set[T]) -> set[T]:
    return left - right
```

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_collections.py -q
```

Expected:

```text
3 passed
```

## Task 10: Documentation and Governance

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/api-policy.md`
- Create: `docs/security.md`
- Create: `Makefile`
- Modify: `README.md`

- [ ] **Step 1: Document architecture**

Write `docs/architecture.md`:

```markdown
# kniferpy Architecture

`kniferpy` exposes focused public `v*` modules under `kniferpy`.
Application code imports facade modules such as `kniferpy.vjson` and never imports `kniferpy.internal`.

The first-release star domains are:

1. Safe HTTP and URL handling.
2. Safe crypto and token workflows.
3. Daily JSON and file workflows.
```

- [ ] **Step 2: Document API policy**

Write `docs/api-policy.md`:

```markdown
# API Policy

Public modules are `kniferpy.v*`, `kniferpy.verr`, and the root `kniferpy` package.
Modules under `kniferpy.internal` are private and may change without compatibility guarantees.

For untrusted input, prefer APIs with explicit policy parameters such as `allowed_hosts`, `max_bytes`, `timeout`, and `session`.
```

- [ ] **Step 3: Document security defaults**

Write `docs/security.md`:

```markdown
# Security

Security-sensitive helpers must expose limits and policies at the call site.

- URL and HTTP helpers reject non-http schemes, private hosts, loopback hosts, link-local hosts, and hosts outside `allowed_hosts`.
- File helpers enforce bounded reads and path traversal checks.
- Crypto helpers wrap standard primitives without inventing algorithms.
```

- [ ] **Step 4: Add Make targets**

Write `Makefile`:

```makefile
.PHONY: install test lint typecheck check

install:
	.venv/bin/poetry install

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check src tests

typecheck:
	.venv/bin/python -m mypy src tests

check: lint typecheck test
```

- [ ] **Step 5: Update README quickstart**

Write `README.md`:

````markdown
# kniferpy

A Python utility toolkit with focused `v*` domain facades.

## Install for local development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip poetry
.venv/bin/poetry config virtualenvs.in-project true
.venv/bin/poetry install
```

## Validate

```bash
.venv/bin/python -m pytest
make check
```

## Start with these modules

| Need | Module |
| --- | --- |
| Safe HTTP and URL handling | `kniferpy.vhttp`, `kniferpy.vurl` |
| Safe crypto and random tokens | `kniferpy.vcrypto`, `kniferpy.vrand`, `kniferpy.vjwt` |
| Daily JSON and file workflows | `kniferpy.vjson`, `kniferpy.vfile` |
```
````

- [ ] **Step 6: Verify all gates**

Run:

```bash
make check
```

Expected:

```text
All checks pass
```

## Implementation Order

1. Bootstrap Poetry, venv, and pytest first.
2. Add `verr` before domain modules so every facade uses the same exception contract.
3. Implement `vstr`, `vjson`, and `vfile` before network and crypto modules; these have the lowest dependency risk.
4. Implement `vcrypto`, `vrand`, and `vjwt` with standard primitives and thin wrappers.
5. Implement `vurl` before `vhttp`, because `vhttp` depends on URL policy.
6. Add collection helpers only after the star domains are passing.
7. Add docs and Make targets once package behavior is stable enough to describe.

## Release-Readiness Checks

Before tagging `0.1.0`, run:

```bash
.venv/bin/poetry lock --no-update
.venv/bin/poetry install
make check
.venv/bin/python -m pytest --cov=kniferpy --cov-report=term-missing
```

Expected:

```text
No lint errors
No mypy errors
All tests pass
Coverage report generated
```

## Deferred Scope

These `knifer-go` domains should not be part of the first Python version unless a concrete Python use case appears:

- `vpoi`: Python Excel support should be designed later around `openpyxl` or `xlsxwriter`.
- `vdb`: SQL helpers need a separate safety contract for SQLAlchemy, sqlite, or DB-API.
- `vmail`, `vssh`, `vftp`: provider-heavy APIs should remain outside the core until the facade contract is proven.
- Chinese-market P0s such as SM2/SM3/SM4, lunar calendar, credit code validation, and coordinate conversion should be planned as separate domain packages after the base toolkit is stable.

## Self-Review

- Spec coverage: The plan references `knifer-go`, preserves the `v*` facade model, uses Poetry for dependency installation, and verifies through pytest inside `.venv`.
- Placeholder scan: No task contains `TBD`, vague "add tests", or missing file paths.
- Type consistency: Public modules use `kniferpy.v*`; private helpers use `kniferpy.internal.*`; shared errors come from `kniferpy.verr`.
