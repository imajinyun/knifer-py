from __future__ import annotations

from pathlib import Path

from kniferpy.internal import filex


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    return filex.safe_join(base, *parts)


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = 1_048_576) -> str:
    return filex.read_text(path, encoding=encoding, max_bytes=max_bytes)


def read_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = 1_048_576,
    keepends: bool = False,
) -> list[str]:
    return filex.read_lines(path, encoding=encoding, max_bytes=max_bytes, keepends=keepends)


def read_bytes(path: str | Path, *, max_bytes: int = 1_048_576) -> bytes:
    return filex.read_bytes(path, max_bytes=max_bytes)


def write_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    filex.write_text(path, value, encoding=encoding)


def write_lines(
    path: str | Path,
    lines: list[str],
    *,
    encoding: str = "utf-8",
    newline: str = "\n",
) -> None:
    filex.write_lines(path, lines, encoding=encoding, newline=newline)


def write_text_atomic(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    filex.write_text_atomic(path, value, encoding=encoding)


def write_bytes(path: str | Path, value: bytes) -> None:
    filex.write_bytes(path, value)


def write_bytes_atomic(path: str | Path, value: bytes) -> None:
    filex.write_bytes_atomic(path, value)


def copy_file(src: str | Path, dst: str | Path, *, max_bytes: int = 10_485_760) -> Path:
    return filex.copy_file(src, dst, max_bytes=max_bytes)
