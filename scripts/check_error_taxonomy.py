from __future__ import annotations

import ast
import importlib
import pkgutil
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src" / "kniferpy"

ERROR_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$")
ALLOWED_DOMAINS = {
    "blf",
    "cache",
    "cli",
    "crypto",
    "file",
    "http",
    "json",
    "jwt",
    "knifer",
    "sem",
    "url",
    "xml",
    "zip",
}


def _iter_python_files() -> list[Path]:
    return sorted(path for path in SRC_ROOT.rglob("*.py") if path.is_file())


def _constant_string(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _extract_code(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == "code":
            return _constant_string(keyword.value)
    return None


def _format_path(path: Path, line: int) -> str:
    return f"{path.relative_to(PROJECT_ROOT)}:{line}"


def _public_module_names() -> list[str]:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    import kniferpy

    return sorted(
        name
        for _, name, is_pkg in pkgutil.iter_modules(kniferpy.__path__)
        if not is_pkg and (name.startswith("v") or name in {"verr", "vid"})
    )


def _check_public_error_sentinels() -> list[str]:
    from kniferpy.verr import KniferError

    errors: list[str] = []
    for module_name in _public_module_names():
        module = importlib.import_module(f"kniferpy.{module_name}")
        for name in getattr(module, "__all__", ()):
            if not name.startswith("Err"):
                continue
            value = getattr(module, name)
            if isinstance(value, KniferError):
                code = value.code
                if not ERROR_CODE_RE.fullmatch(code):
                    errors.append(f"{module_name}.{name} has invalid sentinel code {code!r}")
                continue
            if isinstance(value, type) and issubclass(value, BaseException):
                continue
            errors.append(f"{module_name}.{name} must be a KniferError instance or exception type")
    return errors


def main() -> int:
    errors: list[str] = []
    codes: list[tuple[Path, int, str]] = []

    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                code = _extract_code(node)
                if code is None:
                    continue
                codes.append((path, node.lineno, code))

                if not ERROR_CODE_RE.fullmatch(code):
                    errors.append(f"{_format_path(path, node.lineno)} invalid error code {code!r}")
                    continue
                domain = code.split(".", 1)[0]
                if domain not in ALLOWED_DOMAINS:
                    errors.append(
                        f"{_format_path(path, node.lineno)} unknown error domain {domain!r}"
                    )

    if not codes:
        errors.append("no structured error codes found")
    errors.extend(_check_public_error_sentinels())

    if errors:
        print("error taxonomy check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"error taxonomy check passed ({len(codes)} codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
