"""ZIP archive and gzip/zlib compression utilities.

Create and extract ZIP archives, read archive entries, and compress or
decompress data with gzip and zlib. Extraction is safe by default: entry names
are checked for path traversal (zip-slip) and the total uncompressed size is
bounded to guard against zip bombs.
"""

from __future__ import annotations

from pathlib import Path

from kniferpy.internal import zipx
from kniferpy.internal.zipx import DEFAULT_UNZIP_MAX_BYTES, EntryData

__all__ = [
    "DEFAULT_UNZIP_MAX_BYTES",
    "EntryData",
    "get_bytes",
    "gzip_bytes",
    "gzip_file",
    "gzip_string",
    "list_file_names",
    "read_entries",
    "ungzip",
    "ungzip_string",
    "unzip",
    "unzip_to",
    "unzlib",
    "unzlib_string",
    "zip_archive",
    "zip_bytes",
    "zip_data",
    "zip_entries",
    "zip_files",
    "zip_to",
    "zlib_bytes",
    "zlib_file",
    "zlib_string",
]


# --- ZIP archive creation ---------------------------------------------------


def zip_entries(zip_file: str | Path, entries: list[EntryData], *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add ``entries`` as deflated files."""
    zipx.zip_entries(zip_file, entries, overwrite=overwrite)


def zip_bytes(zip_file: str | Path, name: str, data: bytes, *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add a single byte entry."""
    zipx.zip_bytes(zip_file, name, data, overwrite=overwrite)


def zip_data(zip_file: str | Path, name: str, data: str, *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add a single UTF-8 text entry."""
    zipx.zip_data(zip_file, name, data, overwrite=overwrite)


def zip_files(
    dest: str | Path,
    src_files: list[str | Path],
    *,
    with_src_dir: bool = False,
    overwrite: bool = True,
) -> None:
    """Create ``dest`` from source files or directories (directories walked)."""
    zipx.zip_files(dest, src_files, with_src_dir=with_src_dir, overwrite=overwrite)


def zip_to(src_path: str | Path, zip_path: str | Path, *, with_src_dir: bool = False) -> None:
    """Create an archive at ``zip_path`` from ``src_path``."""
    zipx.zip_to(src_path, zip_path, with_src_dir=with_src_dir)


def zip_archive(src_path: str | Path) -> str:
    """Create an archive next to ``src_path`` and return the archive path."""
    return zipx.zip_archive(src_path)


# --- ZIP archive extraction and reading -------------------------------------


def unzip_to(
    zip_file: str | Path,
    dest_dir: str | Path,
    *,
    limit: int = DEFAULT_UNZIP_MAX_BYTES,
) -> None:
    """Extract ``zip_file`` into ``dest_dir`` (zip-slip safe, size bounded)."""
    zipx.unzip_to(zip_file, dest_dir, limit=limit)


def unzip(zip_file: str | Path, *, limit: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Extract ``zip_file`` into a sibling directory named after the archive."""
    return zipx.unzip(zip_file, limit=limit)


def get_bytes(
    zip_file: str | Path,
    name: str,
    *,
    max_bytes: int = DEFAULT_UNZIP_MAX_BYTES,
) -> bytes:
    """Return the uncompressed content of entry ``name`` in ``zip_file``."""
    return zipx.get_bytes(zip_file, name, max_bytes=max_bytes)


def list_file_names(zip_file: str | Path, dir: str = "") -> list[str]:
    """Return direct (non-recursive) file names under ``dir`` inside ``zip_file``."""
    return zipx.list_file_names(zip_file, dir)


def read_entries(zip_file: str | Path) -> list[str]:
    """Return every entry name in ``zip_file`` in archive order."""
    return zipx.read_entries(zip_file)


# --- gzip -------------------------------------------------------------------


def gzip_bytes(data: bytes, *, level: int = 6) -> bytes:
    """Compress ``data`` using gzip."""
    return zipx.gzip_bytes(data, level=level)


def gzip_string(content: str, *, level: int = 6) -> bytes:
    """Compress UTF-8 ``content`` using gzip."""
    return zipx.gzip_string(content, level=level)


def gzip_file(path: str | Path, *, level: int = 6) -> bytes:
    """Compress the contents of ``path`` using gzip and return the bytes."""
    return zipx.gzip_file(path, level=level)


def ungzip(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> bytes:
    """Decompress gzip ``data`` with a decompressed-size ``limit``."""
    return zipx.ungzip(data, max_bytes=max_bytes)


def ungzip_string(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Decompress gzip ``data`` and decode it as UTF-8 text."""
    return zipx.ungzip_string(data, max_bytes=max_bytes)


# --- zlib -------------------------------------------------------------------


def zlib_bytes(data: bytes, *, level: int = 6) -> bytes:
    """Compress ``data`` using zlib at ``level``."""
    return zipx.zlib_bytes(data, level=level)


def zlib_string(content: str, *, level: int = 6) -> bytes:
    """Compress UTF-8 ``content`` using zlib at ``level``."""
    return zipx.zlib_string(content, level=level)


def zlib_file(path: str | Path, *, level: int = 6) -> bytes:
    """Compress the contents of ``path`` using zlib and return the bytes."""
    return zipx.zlib_file(path, level=level)


def unzlib(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> bytes:
    """Decompress zlib ``data`` with a decompressed-size ``limit``."""
    return zipx.unzlib(data, max_bytes=max_bytes)


def unzlib_string(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Decompress zlib ``data`` and decode it as UTF-8 text."""
    return zipx.unzlib_string(data, max_bytes=max_bytes)
