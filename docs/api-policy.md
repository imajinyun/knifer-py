# 📜 API Policy

Public modules are `kniferpy.v*`, `kniferpy.verr`, and the root `kniferpy`
package. Modules under `kniferpy.internal` are private implementation details
and may change without compatibility guarantees.

## 🧭 Call-Site Policy

For untrusted input, prefer APIs with explicit policy parameters such as
`allowed_hosts`, `max_bytes`, `timeout`, `resolver`, and `session`.
