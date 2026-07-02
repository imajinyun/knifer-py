# 🔪 kniferpy

A Python utility toolkit with focused `v*` domain facades.

`kniferpy` follows the same maintenance model as `knifer-go`: public domain
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
| 🔤 String helpers | `kniferpy.vstr` |
| 🔢 Number and conversion helpers | `kniferpy.vnum`, `kniferpy.vconv`, `kniferpy.vbool` |
| 🧰 Object nil/empty and default helpers | `kniferpy.vobj` |
| 🧪 Regex helpers | `kniferpy.vregex` |
| 🆔 ID generation | `kniferpy.vid` |
| 🪪 China ID card and credit code validation | `kniferpy.vident` |
| 📝 Form field validators | `kniferpy.vform` |
| 🕵️ Data masking helpers | `kniferpy.vmask` |
| 🌐 IP, CIDR, and port helpers | `kniferpy.vnet` |
| 🔐 Password strength scoring | `kniferpy.vpass` |
| 📅 Date and time helpers | `kniferpy.vdate` |
| 🧾 CSV read/write helpers | `kniferpy.vcsv` |
| 🏷️ Version comparison helpers | `kniferpy.vver` |
| 🧺 Sequence, dict, and set helpers | `kniferpy.vseq`, `kniferpy.vdict`, `kniferpy.vset` |
| 🧬 Encoding helpers | `kniferpy.vcodec` |

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
- 🔤 `vstr.to_snake_case(...)`, `vstr.split_trim(...)`, and `vstr.default_if_blank(...)` for text cleanup.
- 🔢 `vnum.round_half_up(...)`, `vconv.to_int(..., default=...)`, and `vbool.to_int(...)` for numeric coercion.
- 🧪 `vregex.find_all(...)`, `vregex.replace(...)`, and `vregex.get_first_number(...)` with invalid patterns failing safe.
- 🆔 `vid.random_uuid(...)`, `vid.nano_id(...)`, and `vid.object_id(...)` for identifiers backed by `secrets`.
- 🪪 `vident.is_valid_id_card(...)`, `vident.parse_id_card(...)`, and `vident.is_valid_credit_code(...)` for China ID validation.
- 📝 `vform.is_email(...)`, `vform.is_mobile(...)`, and `vform.is_url(...)` for form field validation.
- 🕵️ `vmask.mobile_phone(...)`, `vmask.email(...)`, and `vmask.bank_card(...)` for log-safe redaction.
- 🌐 `vnet.is_inner_ip(...)`, `vnet.is_in_range(...)`, and `vnet.hide_ip_part(...)` for IP checks and redaction.
- 🔐 `vpass.analyze(...)`, `vpass.is_strong(...)`, and `vpass.is_weak(...)` for password strength gating.
- 📅 `vdate.parse(...)`, `vdate.end_of_month(...)`, and `vdate.between_days(...)` for date-only workflows.
- 🧾 `vcsv.read_string_maps(...)`, `vcsv.write_string_maps(...)`, and `vcsv.records_to_maps(...)` for tabular data.
- 🏷️ `vver.compare_version(...)`, `vver.is_greater_than(...)`, and `vver.match_el(...)` for version gating.
- 🗺️ `vgeo.wgs84_to_gcj02(...)`, `vgeo.convert(...)`, and `vgeo.distance(...)` for coordinate transforms.
- 🧺 `vseq.group_by(...)`, `vdict.pick(...)`, and `vset.union(...)` for collection workflows.
- 🧬 `vcodec.base64_encode_str(...)`, `vcodec.hex_decode_str(...)`, and `vcodec.rot13(...)` for encoding workflows.
