# 🏗️ kniferpy Architecture

`kniferpy` exposes focused public `v*` modules under `kniferpy`.
Application code imports facade modules such as `kniferpy.vjson` and does not
depend on `kniferpy.internal`.

## ⭐ First-Release Star Domains

1. 🌐 Safe HTTP and URL handling.
2. 🔐 Safe crypto and token workflows.
3. 📄 Daily JSON and file workflows.

## 🧩 knifer-go Alignment

The Python facade set mirrors low-risk `knifer-go` domains where Python's
standard library can provide stable behavior:

- 🔤 `vstr` aligns with `knifer-go/vstr`.
- 🔢 `vnum` aligns with `knifer-go/vnum` (validation, parsing, aggregation, rounding, ranges, factorial).
- 🔁 `vconv` aligns with `knifer-go/vconv` scalar coercion with default and error variants.
- ☑️ `vbool` aligns with `knifer-go/vbool` logical helpers.
- 🧪 `vregex` aligns with `knifer-go/vregex` (match/find/replace/delete/groups, safe on invalid patterns).
- 🆔 `vid` aligns with `knifer-go/vid` (UUID, NanoID, ObjectId, Snowflake with matching bit layout).
- 🕵️ `vmask` aligns with `knifer-go/vmask` field masking strategies.
- 🌐 `vnet` aligns with `knifer-go/vnet` IP/CIDR/port helpers via Python `ipaddress`.
- 🔐 `vpass` aligns with `knifer-go/vpass` deterministic password strength scoring.
- 📅 `vdate` aligns with `knifer-go/vdate` Gregorian helpers (format, parse, begin/end, offset, between) via `datetime`; lunar/GanZhi/solar-term APIs are intentionally omitted.
- 🧺 `vseq`, `vdict`, and `vset` align with `vslice`, `vmap`, and `vset`.
- 🧬 `vcodec` aligns with common `vcodec` Base64, Hex, and ROT helpers.
