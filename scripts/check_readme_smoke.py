from __future__ import annotations

import ast
import re
import shlex
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"

FENCE_RE = re.compile(r"^```(?P<lang>[A-Za-z0-9_-]*)\n(?P<body>.*?)^```", re.MULTILINE | re.DOTALL)
SHELL_LANGS = {"bash", "sh", "shell", "console"}
PYTHON_LANGS = {"python", "py"}


def _check_shell_block(body: str, block_index: int) -> list[str]:
    errors: list[str] = []
    for line_no, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("$ "):
            line = line[2:].strip()
        try:
            shlex.split(line)
        except ValueError as exc:
            errors.append(f"block {block_index} shell line {line_no}: {exc}")
    return errors


def _check_python_block(body: str, block_index: int) -> list[str]:
    try:
        ast.parse(body)
    except SyntaxError as exc:
        return [f"block {block_index} python line {exc.lineno}: {exc.msg}"]
    return []


def main() -> int:
    text = README.read_text(encoding="utf-8")
    errors: list[str] = []
    checked = 0

    for index, match in enumerate(FENCE_RE.finditer(text), start=1):
        lang = match.group("lang").strip().lower()
        body = match.group("body")
        if lang in SHELL_LANGS:
            checked += 1
            errors.extend(_check_shell_block(body, index))
        elif lang in PYTHON_LANGS:
            checked += 1
            errors.extend(_check_python_block(body, index))

    if checked == 0:
        errors.append("README.md has no smoke-checkable code blocks")

    if errors:
        print("README smoke check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"README smoke check passed ({checked} code blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
