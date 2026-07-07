from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
STATUS_FILE = PROJECT_ROOT / "api" / "facade-status.json"
PUBLIC_NON_V_MODULES = {"verr", "vid"}
VALID_STATUSES = {"stable", "experimental", "deprecated"}


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


def _load_status() -> dict[str, object]:
    return cast(dict[str, object], json.loads(STATUS_FILE.read_text(encoding="utf-8")))


def main() -> int:
    _ensure_src_on_path()
    errors: list[str] = []
    payload = _load_status()
    if payload.get("schema_version") != 1:
        errors.append("facade-status schema_version must be 1")

    modules = payload.get("modules")
    if not isinstance(modules, dict):
        errors.append("facade-status modules must be an object")
        modules = {}

    public_modules = set(_public_module_names())
    status_modules = set(str(name) for name in modules)

    missing = sorted(public_modules - status_modules)
    extra = sorted(status_modules - public_modules)
    if missing:
        errors.append(f"facade-status missing modules: {', '.join(missing)}")
    if extra:
        errors.append(f"facade-status contains unknown modules: {', '.join(extra)}")

    for module_name in sorted(public_modules & status_modules):
        entry = modules[module_name]
        if not isinstance(entry, dict):
            errors.append(f"{module_name}: status entry must be an object")
            continue
        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{module_name}: invalid status {status!r}")
            continue
        replacement = entry.get("replacement")
        if status == "deprecated":
            if not isinstance(replacement, str) or not replacement:
                errors.append(f"{module_name}: deprecated facade must declare replacement")
            else:
                importlib.import_module(f"kniferpy.{replacement}")
        elif replacement is not None:
            errors.append(f"{module_name}: replacement is only allowed for deprecated facades")

    if errors:
        print("facade status check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"facade status check passed ({len(public_modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
