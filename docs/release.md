# 🚢 Release Workflow

`kniferpy` uses GitHub Actions for package builds and PyPI publishing.

## ✅ Local Release Check

Run the same local gates used by CI:

```bash
make check
make build
```

The build command writes source and wheel distributions under `dist/`.

## 🏷️ Tag-Based Release

Create a semantic version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The `Release` workflow will:

1. Run `ruff`, `mypy`, and `pytest`.
2. Build package distributions with Poetry.
3. Upload the `dist/` artifacts.
4. Publish to PyPI through trusted publishing.

## 🔐 PyPI Trusted Publishing

Configure PyPI trusted publishing for this repository and the `pypi` GitHub
environment. No long-lived PyPI token is required in GitHub secrets.

## 🧪 Manual Dry Run

Use `workflow_dispatch` with `publish=false` to build and upload artifacts
without publishing.
