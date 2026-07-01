# 🔪 knifer-py

A Python utility toolkit with focused `v*` domain facades.

`knifer-py` follows the same maintenance model as `knifer-go`: public domain
facades stay small and stable, while implementation details live under
`kniferpy.internal`.

## 🚀 Install for Local Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip poetry
.venv/bin/poetry config virtualenvs.in-project true
.venv/bin/poetry install
```

## ✅ Validate

```bash
.venv/bin/python -m pytest
make check
```

## 🧰 Development

```bash
make install
make format
make check
```

CI runs `ruff`, `mypy`, and `pytest` on Python 3.11, 3.12, and 3.13.

## 🚢 Release

```bash
make check
make build
```

Tagged releases such as `v0.1.0` run the release workflow and publish through
PyPI trusted publishing. See [`docs/release.md`](docs/release.md).

## ⭐ Start With These Modules

| Need | Module |
| --- | --- |
| 🌐 Safe HTTP and URL handling | `kniferpy.vhttp`, `kniferpy.vurl` |
| 🔐 Safe crypto and random tokens | `kniferpy.vcrypto`, `kniferpy.vrand`, `kniferpy.vjwt` |
| 📄 Daily JSON and file workflows | `kniferpy.vjson`, `kniferpy.vfile` |

## 🧩 Examples

```python
from kniferpy import vhttp, vjson, vjwt

data = vjson.read_obj("config/app.json", max_bytes=64_000)
body = vhttp.get_string_safe(
    "https://api.example.com/health",
    allowed_hosts={"api.example.com"},
    max_bytes=64_000,
)
token = vjwt.sign_hs256(data, "0123456789abcdef0123456789abcdef", expires_in=300)
```

## 🛡️ Safe Defaults

Common safe defaults are visible at the call site:

- 📦 `vjson.read_obj(..., max_bytes=...)` for bounded JSON file reads.
- 🎯 `vjson.get_str/get_int/get_float/get_bool/get_list/get_dict` for typed path lookup.
- ✍️ `vfile.write_text_atomic(...)` and `vfile.write_bytes_atomic(...)` for replace-style writes.
- 📃 `vfile.read_lines(...)` and `vfile.write_lines(...)` for small bounded text files.
- 🌐 `vhttp.get_json_safe(...)` and `vhttp.post_json_safe(...)` for bounded JSON APIs.
- 🔑 `vcrypto.pbkdf2_sha256_hex(..., iterations=...)` for password-derived keys.
- 🧾 `vcrypto.file_sha256_hex(...)` and `vcrypto.verify_file_sha256_hex(...)` for file checksums.
- 🪪 `vurl.redact_userinfo(...)` for log-safe URL rendering.
