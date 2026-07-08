from __future__ import annotations

import json
import pkgutil
import sys
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
CAPABILITY_FILE = PROJECT_ROOT / "api" / "capability-domains.json"
PUBLIC_NON_V_MODULES = {"verr", "vid"}
STAR_ALLOWED_DOMAINS = {"trust_boundary", "crypto_security", "data_format", "filesystem_io"}


def _ensure_src_on_path() -> None:
    src = str(SRC_ROOT)
    if src not in sys.path:
        sys.path.insert(0, src)


def _public_module_names() -> list[str]:
    import kniferpy

    return sorted(
        info.name
        for info in pkgutil.iter_modules(kniferpy.__path__)
        if not info.ispkg and (info.name.startswith("v") or info.name in PUBLIC_NON_V_MODULES)
    )


def load_registry(path: Path = CAPABILITY_FILE) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def validate_registry(payload: dict[str, Any], public_modules: set[str]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("capability-domains schema_version must be 1")

    domains = payload.get("domains")
    if not isinstance(domains, dict) or not domains:
        errors.append("capability-domains domains must be a non-empty object")
        domains = {}

    modules = payload.get("modules")
    if not isinstance(modules, dict):
        errors.append("capability-domains modules must be an object")
        modules = {}

    registry_modules = set(str(name) for name in modules)
    missing = sorted(public_modules - registry_modules)
    extra = sorted(registry_modules - public_modules)
    if missing:
        errors.append(f"capability-domains missing modules: {', '.join(missing)}")
    if extra:
        errors.append(f"capability-domains contains unknown modules: {', '.join(extra)}")

    domain_names = set(str(name) for name in domains)
    for module_name in sorted(public_modules & registry_modules):
        entry = modules[module_name]
        if not isinstance(entry, dict):
            errors.append(f"{module_name}: capability entry must be an object")
            continue

        domain = entry.get("domain")
        if not isinstance(domain, str) or not domain:
            errors.append(f"{module_name}: domain must be a non-empty string")
            continue
        if domain not in domain_names:
            errors.append(f"{module_name}: unknown domain {domain!r}")

        star = entry.get("star")
        if not isinstance(star, bool):
            errors.append(f"{module_name}: star must be a boolean")
        elif star and domain not in STAR_ALLOWED_DOMAINS:
            errors.append(f"{module_name}: star facade cannot use domain {domain!r}")

        security_sensitive = entry.get("security_sensitive")
        if not isinstance(security_sensitive, bool):
            errors.append(f"{module_name}: security_sensitive must be a boolean")

    return errors


def main() -> int:
    _ensure_src_on_path()
    public_modules = set(_public_module_names())
    errors = validate_registry(load_registry(), public_modules)
    if errors:
        print("capability domain check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"capability domain check passed ({len(public_modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
