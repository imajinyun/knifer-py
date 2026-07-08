from __future__ import annotations

import argparse
import inspect
import json
import pkgutil
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
DEFAULT_SNAPSHOT = PROJECT_ROOT / "api" / "kniferpy-public-api.json"
PUBLIC_NON_V_MODULES = {"verr", "vid"}


def _ensure_src_on_path() -> None:
    src = str(SRC_ROOT)
    if src not in sys.path:
        sys.path.insert(0, src)


def _public_module_names() -> list[str]:
    import kniferpy

    root_exports = set(getattr(kniferpy, "__all__", ()))
    names: set[str] = set()
    for info in pkgutil.iter_modules(kniferpy.__path__):
        if info.ispkg:
            continue
        if info.name.startswith("v") or info.name in PUBLIC_NON_V_MODULES:
            names.add(info.name)
    names.update(
        name for name in root_exports if name.startswith("v") or name in PUBLIC_NON_V_MODULES
    )
    return sorted(names)


def _export_names(module: ModuleType) -> list[str]:
    explicit = getattr(module, "__all__", None)
    if explicit is not None:
        return sorted(str(name) for name in explicit if hasattr(module, str(name)))
    return sorted(name for name in vars(module) if not name.startswith("_"))


def _safe_signature(obj: Any) -> str | None:
    try:
        signature = str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None
    return re.sub(r" at 0x[0-9a-fA-F]+", " at 0x...", signature)


def _entry_kind(obj: Any) -> str:
    if inspect.isclass(obj):
        return "class"
    if inspect.isfunction(obj):
        return "function"
    if inspect.ismodule(obj):
        return "module"
    return "value"


def _callable_entry(obj: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "kind": _entry_kind(obj),
        "type": f"{type(obj).__module__}.{type(obj).__qualname__}",
    }
    signature = _safe_signature(obj)
    if signature is not None:
        entry["signature"] = signature
    if inspect.isclass(obj):
        methods: dict[str, dict[str, Any]] = {}
        for name, member in inspect.getmembers(obj):
            if name.startswith("_"):
                continue
            if inspect.isfunction(member) or inspect.ismethoddescriptor(member):
                member_signature = _safe_signature(member)
                methods[name] = {"signature": member_signature} if member_signature else {}
        if methods:
            entry["methods"] = methods
    return entry


def build_snapshot() -> dict[str, Any]:
    _ensure_src_on_path()
    import importlib

    import kniferpy

    modules: dict[str, Any] = {}
    for name in _public_module_names():
        module = importlib.import_module(f"kniferpy.{name}")
        exports: dict[str, Any] = {}
        for export in _export_names(module):
            obj = getattr(module, export)
            exports[export] = _callable_entry(obj)
        modules[name] = {"exports": exports}

    return {
        "schema_version": 1,
        "package": "kniferpy",
        "root_exports": sorted(str(name) for name in getattr(kniferpy, "__all__", ())),
        "modules": modules,
    }


def _format_missing(paths: Iterable[str]) -> str:
    return "\n".join(f"  - {path}" for path in paths)


def diff_snapshot(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    diffs: list[str] = []
    expected_modules = expected.get("modules", {})
    actual_modules = actual.get("modules", {})

    for module in sorted(set(expected_modules) - set(actual_modules)):
        diffs.append(f"missing module: {module}")
    for module in sorted(set(actual_modules) - set(expected_modules)):
        diffs.append(f"new module: {module}")

    for module in sorted(set(expected_modules) & set(actual_modules)):
        expected_exports = expected_modules[module].get("exports", {})
        actual_exports = actual_modules[module].get("exports", {})
        for name in sorted(set(expected_exports) - set(actual_exports)):
            diffs.append(f"missing export: {module}.{name}")
        for name in sorted(set(actual_exports) - set(expected_exports)):
            diffs.append(f"new export: {module}.{name}")
        for name in sorted(set(expected_exports) & set(actual_exports)):
            exp_entry = expected_exports[name]
            act_entry = actual_exports[name]
            for field in ("kind", "signature"):
                if exp_entry.get(field) != act_entry.get(field):
                    diffs.append(
                        f"changed {field}: {module}.{name}: "
                        f"{exp_entry.get(field)!r} -> {act_entry.get(field)!r}"
                    )
            exp_methods = exp_entry.get("methods", {})
            act_methods = act_entry.get("methods", {})
            for method in sorted(set(exp_methods) - set(act_methods)):
                diffs.append(f"missing method: {module}.{name}.{method}")
            for method in sorted(set(act_methods) - set(exp_methods)):
                diffs.append(f"new method: {module}.{name}.{method}")
            for method in sorted(set(exp_methods) & set(act_methods)):
                if exp_methods[method].get("signature") != act_methods[method].get("signature"):
                    diffs.append(
                        f"changed method signature: {module}.{name}.{method}: "
                        f"{exp_methods[method].get('signature')!r} -> "
                        f"{act_methods[method].get('signature')!r}"
                    )

    if expected.get("root_exports") != actual.get("root_exports"):
        missing = sorted(
            set(expected.get("root_exports", ())) - set(actual.get("root_exports", ()))
        )
        added = sorted(set(actual.get("root_exports", ())) - set(expected.get("root_exports", ())))
        if missing:
            diffs.append("missing root exports:\n" + _format_missing(missing))
        if added:
            diffs.append("new root exports:\n" + _format_missing(added))

    return diffs


def _write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _format_api_entry(kind: str, name: str, signature: str | None) -> str:
    if signature is None:
        return f"- {kind} `{name}`"
    return f"- {kind} `{name}{signature}`"


def render_api_index(snapshot: dict[str, Any]) -> str:
    package = str(snapshot.get("package", "kniferpy"))
    lines = [f"# {package} Public API Index", "", "## Root Exports", ""]

    root_exports = sorted(str(name) for name in snapshot.get("root_exports", ()))
    if root_exports:
        lines.extend(f"- {name}" for name in root_exports)
    else:
        lines.append("- None")

    lines.extend(["", "## Modules", ""])
    modules = snapshot.get("modules", {})
    if not isinstance(modules, dict) or not modules:
        lines.append("- None")
        return "\n".join(lines).rstrip() + "\n"

    for module_name in sorted(str(name) for name in modules):
        module = modules[module_name]
        lines.append(f"### {package}.{module_name}")
        lines.append("")
        exports = module.get("exports", {}) if isinstance(module, dict) else {}
        if not isinstance(exports, dict) or not exports:
            lines.append("- None")
            lines.append("")
            continue
        for export_name in sorted(str(name) for name in exports):
            entry = exports[export_name]
            if not isinstance(entry, dict):
                lines.append(f"- value `{export_name}`")
                continue
            kind = str(entry.get("kind", "value"))
            signature = entry.get("signature")
            signature_text = signature if isinstance(signature, str) else None
            lines.append(_format_api_entry(kind, export_name, signature_text))
            methods = entry.get("methods", {})
            if isinstance(methods, dict) and methods:
                for method_name in sorted(str(name) for name in methods):
                    method = methods[method_name]
                    method_signature = (
                        method.get("signature") if isinstance(method, dict) else None
                    )
                    signature_text = (
                        method_signature if isinstance(method_signature, str) else None
                    )
                    if signature_text is None:
                        lines.append(f"  - method `{method_name}`")
                    else:
                        lines.append(f"  - method `{method_name}{signature_text}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check kniferpy public API snapshot.")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--update", action="store_true", help="rewrite the public API snapshot")
    parser.add_argument("--print-index", action="store_true", help="print a public API index")
    args = parser.parse_args()

    actual = build_snapshot()
    if args.print_index:
        print(render_api_index(actual), end="")
        return 0

    if args.update:
        _write_snapshot(args.snapshot, actual)
        print(f"updated API snapshot: {args.snapshot}")
        return 0

    if not args.snapshot.exists():
        print(f"API snapshot is missing: {args.snapshot}", file=sys.stderr)
        print("Run `UPDATE_API=1 make api-check` to create the baseline.", file=sys.stderr)
        return 1

    expected = json.loads(args.snapshot.read_text(encoding="utf-8"))
    diffs = diff_snapshot(expected, actual)
    if diffs:
        print("Public API snapshot changed:", file=sys.stderr)
        for diff in diffs:
            print(f"- {diff}", file=sys.stderr)
        print(
            "Run `UPDATE_API=1 make api-check` after intentional public API changes.",
            file=sys.stderr,
        )
        return 1

    print("public API snapshot is up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
