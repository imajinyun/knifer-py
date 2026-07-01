from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from kniferpy.verr import SecurityError


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    root = Path(base).resolve()
    candidate = root.joinpath(*parts).resolve()
    if candidate != root and root not in candidate.parents:
        raise SecurityError(
            "path escapes base directory",
            code="file.path_traversal",
            context={"base": str(root), "candidate": str(candidate)},
        )
    return candidate


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> str:
    candidate = Path(path)
    _ensure_size(candidate, max_bytes=max_bytes)
    return candidate.read_text(encoding=encoding)


def read_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = 1_048_576,
    keepends: bool = False,
) -> list[str]:
    return read_text(path, encoding=encoding, max_bytes=max_bytes).splitlines(keepends=keepends)


def read_bytes(path: str | Path, *, max_bytes: int = 1_048_576) -> bytes:
    candidate = Path(path)
    _ensure_size(candidate, max_bytes=max_bytes)
    return candidate.read_bytes()


def write_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding=encoding)


def write_lines(
    path: str | Path,
    lines: list[str],
    *,
    encoding: str = "utf-8",
    newline: str = "\n",
) -> None:
    write_text(path, newline.join(lines), encoding=encoding)


def write_text_atomic(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding=encoding,
        dir=target.parent,
        delete=False,
    ) as tmp:
        tmp.write(value)
        tmp_path = Path(tmp.name)
    tmp_path.replace(target)


def write_bytes(path: str | Path, value: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(value)


def write_bytes_atomic(path: str | Path, value: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as tmp:
        tmp.write(value)
        tmp_path = Path(tmp.name)
    tmp_path.replace(target)


def copy_file(src: str | Path, dst: str | Path, *, max_bytes: int = 10_485_760) -> Path:
    source = Path(src)
    _ensure_size(source, max_bytes=max_bytes)
    target = Path(dst)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def _ensure_size(path: Path, *, max_bytes: int) -> None:
    size = path.stat().st_size
    if size > max_bytes:
        raise SecurityError(
            "file exceeds max_bytes",
            code="file.too_large",
            context={"size": size, "max_bytes": max_bytes},
        )
