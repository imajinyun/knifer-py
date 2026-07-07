from __future__ import annotations

import ast
import importlib
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
PACKAGE_ROOT = SRC_ROOT / "kniferpy"
PUBLIC_NON_V_MODULES = {"verr", "vid"}


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


def _literal_all(path: Path) -> list[str] | None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        has_all_target = any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        )
        if not has_all_target:
            continue
        if not isinstance(node.value, ast.List | ast.Tuple):
            return None
        values: list[str] = []
        for elt in node.value.elts:
            if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                return None
            values.append(elt.value)
        return values
    return None


def _module_exports(module: ModuleType, module_path: Path) -> tuple[list[str], list[str]]:
    explicit = getattr(module, "__all__", None)
    if explicit is None:
        public_names = [
            name
            for name, value in vars(module).items()
            if not name.startswith("_") and not isinstance(value, ModuleType)
        ]
        return sorted(public_names), []
    if not isinstance(explicit, list):
        return [], ["__all__ must be a list"]
    if not all(isinstance(name, str) for name in explicit):
        return [], ["__all__ must contain only strings"]

    literal = _literal_all(module_path)
    if literal is not None and literal != explicit:
        return [], ["literal __all__ differs from runtime __all__"]
    return list(explicit), []


def _format_module_error(module_name: str, message: str) -> str:
    return f"kniferpy.{module_name}: {message}"


def _object_origin(obj: Any) -> str:
    module = getattr(obj, "__module__", "")
    if module:
        return str(module)
    return type(obj).__module__


def _check_root_exports() -> list[str]:
    import kniferpy

    errors: list[str] = []
    root_exports = list(getattr(kniferpy, "__all__", ()))
    public_modules = _public_module_names()

    if len(root_exports) != len(set(root_exports)):
        errors.append("kniferpy.__all__ contains duplicate module names")
    if sorted(root_exports) != public_modules:
        missing = sorted(set(public_modules) - set(root_exports))
        extra = sorted(set(root_exports) - set(public_modules))
        if missing:
            errors.append(f"kniferpy.__all__ missing public modules: {', '.join(missing)}")
        if extra:
            errors.append(f"kniferpy.__all__ contains unknown modules: {', '.join(extra)}")
    return errors


def _check_module(module_name: str) -> list[str]:
    module = importlib.import_module(f"kniferpy.{module_name}")
    module_path = PACKAGE_ROOT / f"{module_name}.py"
    errors: list[str] = []

    exports, export_errors = _module_exports(module, module_path)
    if export_errors:
        return [_format_module_error(module_name, error) for error in export_errors]

    if len(exports) != len(set(exports)):
        errors.append(_format_module_error(module_name, "__all__ contains duplicate exports"))

    for name in exports:
        if name.startswith("_"):
            errors.append(
                _format_module_error(module_name, f"private export {name!r} is not allowed")
            )
            continue
        if not hasattr(module, name):
            errors.append(_format_module_error(module_name, f"export {name!r} does not exist"))
            continue

        value = getattr(module, name)
        if isinstance(value, ModuleType):
            errors.append(
                _format_module_error(module_name, f"export {name!r} must not be a module")
            )
            continue

        origin = _object_origin(value)
        if origin.startswith("kniferpy.") and not (
            origin == f"kniferpy.{module_name}" or origin.startswith("kniferpy.internal.")
        ):
            errors.append(
                _format_module_error(
                    module_name,
                    f"export {name!r} unexpectedly originates from {origin!r}",
                )
            )

    return errors


def main() -> int:
    _ensure_src_on_path()
    errors: list[str] = []
    errors.extend(_check_root_exports())

    for module_name in _public_module_names():
        errors.extend(_check_module(module_name))

    if errors:
        print("facade consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"facade consistency check passed ({len(_public_module_names())} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
