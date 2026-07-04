from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kniferpy.verr import SecurityError

DEFAULT_MAX_BYTES = 64 << 20  # 64 MiB


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


def is_local_path(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in ("http://", "https://", "ftp://", "s3://"))


# ── exists / stat ──────────────────────────────────────────────────────────


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def is_file(path: str | Path) -> bool:
    return Path(path).is_file()


def is_dir(path: str | Path) -> bool:
    return Path(path).is_dir()


def file_size(path: str | Path) -> int:
    return Path(path).stat().st_size


# ── read ────────────────────────────────────────────────────────────────────


def read_text(path: str | Path, *, encoding: str = "utf-8", max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    candidate = Path(path)
    _ensure_size(candidate, max_bytes=max_bytes)
    return candidate.read_text(encoding=encoding)


def read_lines(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int = DEFAULT_MAX_BYTES,
    keepends: bool = False,
) -> list[str]:
    return read_text(path, encoding=encoding, max_bytes=max_bytes).splitlines(keepends=keepends)


def read_bytes(path: str | Path, *, max_bytes: int = DEFAULT_MAX_BYTES) -> bytes:
    candidate = Path(path)
    _ensure_size(candidate, max_bytes=max_bytes)
    return candidate.read_bytes()


# ── write ───────────────────────────────────────────────────────────────────


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


def append_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding=encoding) as f:
        f.write(value)


def append_bytes(path: str | Path, value: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("ab") as f:
        f.write(value)


# ── directory / file management ─────────────────────────────────────────────


def mkdir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def touch(path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()


def delete(path: str | Path) -> None:
    target = Path(path)
    if target.is_dir():
        shutil.rmtree(target)
    elif target.is_file():
        target.unlink()


def copy_file(src: str | Path, dst: str | Path, *, max_bytes: int = 10_485_760) -> Path:
    source = Path(src)
    _ensure_size(source, max_bytes=max_bytes)
    target = Path(dst)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


# ── filename utilities ──────────────────────────────────────────────────────


def main_name(path: str | Path) -> str:
    return Path(path).stem


def extension(path: str | Path) -> str:
    return Path(path).suffix


# ── file type detection ─────────────────────────────────────────────────────


_MAGIC_SIGNATURES: dict[str, tuple[str, str, str]] = {
    b"\xff\xd8\xff": ("image/jpeg", ".jpg", "image"),
    b"\x89PNG\r\n\x1a\n": ("image/png", ".png", "image"),
    b"GIF87a": ("image/gif", ".gif", "image"),
    b"GIF89a": ("image/gif", ".gif", "image"),
    b"RIFF": ("", "", ""),  # handled specially
    b"PK\x03\x04": ("application/zip", ".zip", "archive"),
    b"%PDF": ("application/pdf", ".pdf", "document"),
    b"\x25\x50\x44\x46": ("application/pdf", ".pdf", "document"),
    b"\x1f\x8b\x08": ("application/gzip", ".gz", "archive"),
    b"\x42\x5a\x68": ("application/bzip2", ".bz2", "archive"),
    b"\x1f\x9d": ("application/compress", ".z", "archive"),
    b"\x7fELF": ("application/x-elf", "", "executable"),
    b"\xca\xfe\xba\xbe": ("application/x-mach", "", "executable"),
    b"\xcf\xfa\xed\xfe": ("application/x-mach", "", "executable"),
    b"II*\x00": ("image/tiff", ".tiff", "image"),
    b"MM\x00*": ("image/tiff", ".tiff", "image"),
    b"\x00\x00\x01\x00": ("image/x-icon", ".ico", "image"),
    b"BM": ("image/bmp", ".bmp", "image"),
    b"\x1a\x45\xdf\xa3": ("video/webm", ".webm", "video"),
    b"OggS": ("audio/ogg", ".ogg", "audio"),
    b"ID3": ("audio/mpeg", ".mp3", "audio"),
    b"fLaC": ("audio/flac", ".flac", "audio"),
    b"\x00\x00\x00\x1c\x66\x74\x79\x70": ("video/mp4", ".mp4", "video"),
    b"\x00\x00\x00\x14\x66\x74\x79\x70": ("video/mp4", ".mp4", "video"),
    b"\x00\x00\x00\x20\x66\x74\x79\x70": ("video/mp4", ".mp4", "video"),
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": ("application/msword", ".doc", "document"),
    b"\x50\x4b\x03\x04": ("", "", ""),  # handled via PK
    b"\x1f\x8b": ("", "", ""),  # handled via gzip
}


@dataclass(slots=True, frozen=True)
class FileType:
    mime: str = ""
    extension: str = ""
    category: str = ""


UNKNOWN_FILE_TYPE = FileType()


def detect_file_type(data: bytes) -> FileType:
    if len(data) < 2:
        return UNKNOWN_FILE_TYPE

    for magic, (mime, ext, cat) in _MAGIC_SIGNATURES.items():
        if data.startswith(magic):
            if magic == b"RIFF":
                if len(data) >= 12:
                    sub = data[8:12]
                    if sub == b"WEBP":
                        return FileType("image/webp", ".webp", "image")
                    if sub == b"WAVE":
                        return FileType("audio/wav", ".wav", "audio")
                return UNKNOWN_FILE_TYPE
            if mime:
                return FileType(mime, ext, cat)
            return UNKNOWN_FILE_TYPE

    if data.startswith(b"\x00\x00\x00"):
        return FileType("video/mp4", ".mp4", "video")

    return UNKNOWN_FILE_TYPE


def detect_file_type_from_path(path: str | Path) -> FileType:
    try:
        head = Path(path).read_bytes()[:64]
    except OSError:
        return UNKNOWN_FILE_TYPE
    return detect_file_type(head)


def is_image(ft: FileType) -> bool:
    return ft.category == "image"


def is_video(ft: FileType) -> bool:
    return ft.category == "video"


def is_audio(ft: FileType) -> bool:
    return ft.category == "audio"


def is_archive(ft: FileType) -> bool:
    return ft.category == "archive"


def is_document(ft: FileType) -> bool:
    return ft.category == "document"


# ── internal helpers ────────────────────────────────────────────────────────


def _ensure_size(path: Path, *, max_bytes: int) -> None:
    size = path.stat().st_size
    if size > max_bytes:
        raise SecurityError(
            "file exceeds max_bytes",
            code="file.too_large",
            context={"size": size, "max_bytes": max_bytes},
        )
