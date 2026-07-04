from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from kniferpy.internal import filex
from kniferpy.internal.filex import FileType, UNKNOWN_FILE_TYPE

__all__ = [
    "DEFAULT_MAX_BYTES",
    "UNKNOWN_FILE_TYPE",
    "FileType",
    "WriteOption",
    "DirOption",
    "ReadOption",
    "StatOption",
    "DeleteOption",
    "safe_join",
    "is_local_path",
    "exists",
    "is_file",
    "is_dir",
    "file_size",
    "size",
    "read_text",
    "read_lines",
    "read_bytes",
    "read_file_string",
    "read_file_bytes",
    "read_file_lines",
    "read_file_chunks",
    "read_all",
    "reader_read_string",
    "reader_read_lines",
    "read_chunks",
    "write_text",
    "write_lines",
    "write_text_atomic",
    "write_bytes",
    "write_bytes_atomic",
    "write_file_string",
    "write_file_bytes",
    "append_text",
    "append_bytes",
    "append_file_string",
    "mkdir",
    "touch",
    "delete",
    "copy_file",
    "copy_stream",
    "close_quietly",
    "reader_from_string",
    "reader_from_bytes",
    "main_name",
    "extension",
    "detect_file_type",
    "detect_file_type_from_path",
    "is_image",
    "is_video",
    "is_audio",
    "is_archive",
    "is_document",
]

DEFAULT_MAX_BYTES = filex.DEFAULT_MAX_BYTES

# Go-compat type aliases: functional option types
WriteOption = Callable[[Any], None]
DirOption = Callable[[Any], None]
ReadOption = Callable[[Any], None]
StatOption = Callable[[Any], None]
DeleteOption = Callable[[Any], None]


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    return filex.safe_join(base, *parts)


def is_local_path(path: str) -> bool:
    return filex.is_local_path(path)


def exists(path: str | Path) -> bool:
    return filex.exists(path)


def is_file(path: str | Path) -> bool:
    return filex.is_file(path)


def is_dir(path: str | Path) -> bool:
    return filex.is_dir(path)


def file_size(path: str | Path) -> int:
    return filex.file_size(path)


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    return filex.read_text(path, encoding=encoding, max_bytes=max_bytes)


def read_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = DEFAULT_MAX_BYTES,
    keepends: bool = False,
) -> list[str]:
    return filex.read_lines(path, encoding=encoding, max_bytes=max_bytes, keepends=keepends)


def read_bytes(path: str | Path, *, max_bytes: int = DEFAULT_MAX_BYTES) -> bytes:
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


def append_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    filex.append_text(path, value, encoding=encoding)


def append_bytes(path: str | Path, value: bytes) -> None:
    filex.append_bytes(path, value)


def mkdir(path: str | Path) -> None:
    filex.mkdir(path)


def touch(path: str | Path) -> None:
    filex.touch(path)


def delete(path: str | Path) -> None:
    filex.delete(path)


def copy_file(src: str | Path, dst: str | Path, *, max_bytes: int = 10_485_760) -> Path:
    return filex.copy_file(src, dst, max_bytes=max_bytes)


def main_name(path: str | Path) -> str:
    return filex.main_name(path)


def extension(path: str | Path) -> str:
    return filex.extension(path)


def detect_file_type(data: bytes) -> FileType:
    return filex.detect_file_type(data)


def detect_file_type_from_path(path: str | Path) -> FileType:
    return filex.detect_file_type_from_path(path)


def is_image(ft: FileType) -> bool:
    return filex.is_image(ft)


def is_video(ft: FileType) -> bool:
    return filex.is_video(ft)


def is_audio(ft: FileType) -> bool:
    return filex.is_audio(ft)


def is_archive(ft: FileType) -> bool:
    return filex.is_archive(ft)


def is_document(ft: FileType) -> bool:
    return filex.is_document(ft)


# ── Reader/Writer helpers ──────────────────────────────────────────────────


def read_all(r, *, max_bytes: int = DEFAULT_MAX_BYTES) -> bytes:
    return filex.read_all(r, max_bytes=max_bytes)


def reader_read_string(r, *, encoding: str = "utf-8", max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    return filex.reader_read_string(r, encoding=encoding, max_bytes=max_bytes)


def reader_read_lines(
    r,
    *,
    encoding: str = "utf-8",
    max_bytes: int = DEFAULT_MAX_BYTES,
    keepends: bool = False,
) -> list[str]:
    return filex.reader_read_lines(r, encoding=encoding, max_bytes=max_bytes, keepends=keepends)


def read_chunks(
    r,
    handler,
    *,
    buffer_size: int = 8192,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> None:
    return filex.read_chunks(r, handler, buffer_size=buffer_size, max_bytes=max_bytes)


def copy_stream(dst, src, *, buffer_size: int = 32768) -> int:
    return filex.copy_stream(dst, src, buffer_size=buffer_size)


def close_quietly(c) -> None:
    return filex.close_quietly(c)


def reader_from_string(s: str):
    return filex.reader_from_string(s)


def reader_from_bytes(data: bytes):
    return filex.reader_from_bytes(data)


def read_file_string(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    return filex.read_file_string(path, encoding=encoding, max_bytes=max_bytes)


def read_file_bytes(path: str | Path, *, max_bytes: int = DEFAULT_MAX_BYTES) -> bytes:
    return filex.read_file_bytes(path, max_bytes=max_bytes)


def read_file_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = DEFAULT_MAX_BYTES,
    keepends: bool = False,
) -> list[str]:
    return filex.read_file_lines(path, encoding=encoding, max_bytes=max_bytes, keepends=keepends)


def read_file_chunks(
    path: str | Path,
    handler,
    *,
    buffer_size: int = 8192,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> None:
    return filex.read_file_chunks(path, handler, buffer_size=buffer_size, max_bytes=max_bytes)


def write_file_string(path: str | Path, content: str, *, encoding: str = "utf-8") -> None:
    return filex.write_file_string(path, content, encoding=encoding)


def write_file_bytes(path: str | Path, data: bytes) -> None:
    return filex.write_file_bytes(path, data)


def append_file_string(path: str | Path, content: str, *, encoding: str = "utf-8") -> None:
    return filex.append_file_string(path, content, encoding=encoding)


def size(path: str | Path) -> int:
    return filex.size(path)