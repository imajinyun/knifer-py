# 🛡️ Security

Security-sensitive helpers must expose limits and policies at the call site.

- 🌐 URL and HTTP helpers reject non-http schemes, private hosts, loopback hosts,
  link-local hosts, and hosts outside `allowed_hosts`.
- 📁 File helpers enforce bounded reads and path traversal checks.
- ✍️ File atomic write helpers replace files through a same-directory temporary file.
- 📥 HTTP helpers support response size limits before returning bytes or writing downloads.
- 🧩 HTTP JSON helpers wrap invalid response JSON as explicit decode errors.
- 📦 HTTP JSON helpers require object responses for object-returning APIs.
- 🪪 URL helpers include `redact_userinfo` for log-safe rendering of credential-bearing URLs.
- 🔐 JWT HS256 helpers reject secrets shorter than 32 bytes.
- 🔑 PBKDF2-SHA256 helpers reject iteration counts below 100000.
- 🧾 Crypto helpers wrap standard primitives and do not invent algorithms. MD5 is exposed only
  as `md5_checksum_hex` to avoid presenting it as a secure hash.
