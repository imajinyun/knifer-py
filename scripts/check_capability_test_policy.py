from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_FILE = PROJECT_ROOT / "api" / "capability-domains.json"
FACADE_STATUS_FILE = PROJECT_ROOT / "api" / "facade-status.json"
TEST_ROOT = PROJECT_ROOT / "tests"
SECURITY_TOKENS = (
    "SecurityError",
    "ValidationError",
    "safe",
    "reject",
    "invalid",
    "forbid",
    "path",
    "allowed",
    "deny",
)


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _test_candidates(module_name: str, *, deprecated: bool, test_root: Path) -> list[Path]:
    candidates = [test_root / f"test_{module_name}.py"]
    if deprecated:
        suffix = module_name[1:] if module_name.startswith("v") else module_name
        candidates.extend(sorted(test_root.glob(f"test_*{suffix}*.py")))
        candidates.append(test_root / "test_deprecation_policy.py")
    return candidates


def _existing_test_file(module_name: str, *, deprecated: bool, test_root: Path) -> Path | None:
    for path in _test_candidates(module_name, deprecated=deprecated, test_root=test_root):
        if path.exists():
            return path
    return None


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def validate_policy(
    capability_registry: dict[str, Any],
    facade_status: dict[str, Any],
    *,
    test_root: Path = TEST_ROOT,
) -> list[str]:
    errors: list[str] = []
    modules = capability_registry.get("modules", {})
    if not isinstance(modules, dict):
        return ["capability-domains modules must be an object"]

    status_modules = facade_status.get("modules", {})
    if not isinstance(status_modules, dict):
        status_modules = {}

    for module_name in sorted(str(name) for name in modules):
        entry = modules[module_name]
        if not isinstance(entry, dict):
            errors.append(f"{module_name}: capability entry must be an object")
            continue

        status_entry = status_modules.get(module_name, {})
        deprecated = isinstance(status_entry, dict) and status_entry.get("status") == "deprecated"
        test_file = _existing_test_file(module_name, deprecated=deprecated, test_root=test_root)
        if test_file is None:
            errors.append(f"{module_name}: missing test file")
            continue

        if not test_file.is_relative_to(test_root):
            errors.append(f"{module_name}: test file must live under tests/")
            continue

        text = test_file.read_text(encoding="utf-8")
        star = entry.get("star")
        if star is True and "def test_" not in text:
            errors.append(f"{module_name}: star facade test file must define tests")

        security_sensitive = entry.get("security_sensitive")
        if security_sensitive is True and not _contains_any(text, SECURITY_TOKENS):
            errors.append(f"{module_name}: security-sensitive facade lacks safety test token")

    return errors


def main() -> int:
    errors = validate_policy(_load_json(CAPABILITY_FILE), _load_json(FACADE_STATUS_FILE))
    if errors:
        print("capability test policy check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    module_count = len(_load_json(CAPABILITY_FILE).get("modules", {}))
    print(f"capability test policy check passed ({module_count} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
