# 🤝 Contributing

Thanks for helping improve `kniferpy`.

## 🧰 Local Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip poetry
.venv/bin/poetry install
```

## ✅ Validation

Run the full local gate before sending changes:

```bash
make check
```

For coverage:

```bash
make test-cov
```

## 🧭 API Guidelines

- Keep public APIs in `kniferpy.v*` facade modules.
- Keep implementation details in `kniferpy.internal`.
- For untrusted input, expose policy parameters at the call site, such as
  `allowed_hosts`, `max_bytes`, `timeout`, `resolver`, and `session`.
- Prefer explicit exceptions from `kniferpy.verr` for domain failures.
- Do not add broad utility modules until a repeated workflow justifies them.

## 🧪 Test Guidelines

- Add tests for every public facade behavior.
- Use injected providers, resolvers, sessions, or temporary directories instead
  of real network or host-specific filesystem state.
- Keep tests deterministic and small.
