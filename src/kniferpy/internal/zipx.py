from __future__ import annotations

import gzip
import io
import zipfile
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO

from kniferpy.verr import SecurityError, ValidationError

# Cap uncompressed extraction size to guard against zip bombs, mirroring
# knifer-go's DefaultUnzipMaxBytes (1 GiB).
DEFAULT_UNZIP_MAX_BYTES = 1 << 30


@dataclass(frozen=True, slots=True)
class EntryData:
    """In-memory content to add into a ZIP archive."""

    name: str
    data: bytes


def _clean_entry_name(name: str) -> str:
    """Return a normalized, safe archive entry name or raise on traversal.

    Rejects absolute paths and any name that would escape the archive root
    (``..`` components), matching knifer-go's ``cleanEntryName``.
    """
    if name == "" or name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        raise ValidationError(f"vzip: invalid zip entry name: {name!r}", code="zip.invalid_name")
    cleaned = PurePosixPath(name.replace("\\", "/"))
    parts = [p for p in cleaned.parts if p not in ("", ".")]
    if not parts or ".." in parts:
        raise ValidationError(f"vzip: invalid zip entry name: {name!r}", code="zip.invalid_name")
    return "/".join(parts)


def _safe_target(dest_dir: Path, name: str) -> Path:
    """Resolve ``name`` under ``dest_dir``, refusing paths that escape it.

    Any rejected or traversing entry name raises :class:`SecurityError` because
    the archive is untrusted input during extraction.
    """
    try:
        cleaned = _clean_entry_name(name)
    except ValidationError as exc:
        raise SecurityError(
            f"vzip: zip entry escapes destination: {name!r}", code="zip.path_escape"
        ) from exc
    dest_abs = dest_dir.resolve()
    target = (dest_dir / cleaned).resolve()
    if target != dest_abs and dest_abs not in target.parents:
        raise SecurityError(
            f"vzip: zip entry escapes destination: {name!r}", code="zip.path_escape"
        )
    return target


# --- ZIP archive creation ---------------------------------------------------


def zip_entries(zip_file: str | Path, entries: list[EntryData], *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add ``entries`` as deflated files."""
    dest = Path(zip_file)
    if dest.exists() and not overwrite:
        raise ValidationError(f"vzip: destination exists: {dest}", code="zip.exists")
    if dest.parent and not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            zf.writestr(_clean_entry_name(entry.name), entry.data)


def zip_bytes(zip_file: str | Path, name: str, data: bytes, *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add a single byte entry."""
    zip_entries(zip_file, [EntryData(name=name, data=data)], overwrite=overwrite)


def zip_data(zip_file: str | Path, name: str, data: str, *, overwrite: bool = True) -> None:
    """Create (or overwrite) ``zip_file`` and add a single UTF-8 text entry."""
    zip_bytes(zip_file, name, data.encode("utf-8"), overwrite=overwrite)


def zip_files(
    dest: str | Path,
    src_files: list[str | Path],
    *,
    with_src_dir: bool = False,
    overwrite: bool = True,
) -> None:
    """Create ``dest`` from source files or directories.

    When a source is a directory, its tree is walked recursively. If
    ``with_src_dir`` is true the directory's own name is kept as a prefix;
    otherwise entries are relative to the directory itself.
    """
    dest_path = Path(dest)
    if dest_path.exists() and not overwrite:
        raise ValidationError(f"vzip: destination exists: {dest_path}", code="zip.exists")
    if dest_path.parent and not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in src_files:
            src_path = Path(src)
            if not src_path.exists():
                raise ValidationError(f"vzip: source not found: {src_path}", code="zip.no_source")
            if src_path.is_dir():
                base = src_path.parent if with_src_dir else src_path
                for child in sorted(src_path.rglob("*")):
                    if child.is_file():
                        arcname = child.relative_to(base).as_posix()
                        zf.write(child, _clean_entry_name(arcname))
            else:
                zf.write(src_path, _clean_entry_name(src_path.name))


def zip_to(src_path: str | Path, zip_path: str | Path, *, with_src_dir: bool = False) -> None:
    """Create an archive at ``zip_path`` from ``src_path``."""
    zip_files(zip_path, [src_path], with_src_dir=with_src_dir)


def zip_archive(src_path: str | Path) -> str:
    """Create an archive next to ``src_path`` and return the archive path."""
    src = Path(src_path)
    dest = src.with_suffix(".zip")
    zip_to(src, dest, with_src_dir=False)
    return str(dest)


# --- ZIP archive extraction and reading -------------------------------------


def unzip_to(
    zip_file: str | Path,
    dest_dir: str | Path,
    *,
    limit: int = DEFAULT_UNZIP_MAX_BYTES,
) -> None:
    """Extract ``zip_file`` into ``dest_dir`` with a total-size ``limit``.

    Every entry is checked for path traversal before extraction, and the
    cumulative uncompressed size is capped to guard against zip bombs.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(zip_file, "r") as zf:
        for info in zf.infolist():
            target = _safe_target(dest, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if limit > 0:
                total += info.file_size
                if total > limit:
                    raise SecurityError(
                        f"vzip: archive exceeds max bytes: {limit}", code="zip.too_large"
                    )
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as out:
                out.write(src.read())


def unzip(zip_file: str | Path, *, limit: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Extract ``zip_file`` into a sibling directory named after the archive."""
    src = Path(zip_file)
    dest = src.with_suffix("")
    unzip_to(src, dest, limit=limit)
    return str(dest)


def get_bytes(
    zip_file: str | Path,
    name: str,
    *,
    max_bytes: int = DEFAULT_UNZIP_MAX_BYTES,
) -> bytes:
    """Return the uncompressed content of entry ``name`` in ``zip_file``."""
    with zipfile.ZipFile(zip_file, "r") as zf:
        try:
            info = zf.getinfo(name)
        except KeyError as exc:
            raise ValidationError(
                f"vzip: entry not found: {name!r}", code="zip.no_entry"
            ) from exc
        if max_bytes > 0 and info.file_size > max_bytes:
            raise SecurityError(
                f"vzip: entry exceeds max bytes: {max_bytes}", code="zip.too_large"
            )
        with zf.open(info, "r") as src:
            return src.read()


def list_file_names(zip_file: str | Path, dir: str = "") -> list[str]:
    """Return direct (non-recursive) file names under ``dir`` inside ``zip_file``."""
    prefix = dir.strip()
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    names: list[str] = []
    with zipfile.ZipFile(zip_file, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if prefix:
                if not name.startswith(prefix):
                    continue
                name = name[len(prefix):]
            if name and "/" not in name and not info.is_dir():
                names.append(name)
    return names


def read_entries(zip_file: str | Path) -> list[str]:
    """Return every entry name in ``zip_file`` in archive order."""
    with zipfile.ZipFile(zip_file, "r") as zf:
        return zf.namelist()


# --- gzip -------------------------------------------------------------------


def gzip_bytes(data: bytes, *, level: int = 6) -> bytes:
    """Compress ``data`` using gzip."""
    return gzip.compress(data, compresslevel=level)


def gzip_string(content: str, *, level: int = 6) -> bytes:
    """Compress UTF-8 ``content`` using gzip."""
    return gzip_bytes(content.encode("utf-8"), level=level)


def gzip_file(path: str | Path, *, level: int = 6) -> bytes:
    """Compress the contents of ``path`` using gzip and return the bytes."""
    return gzip_bytes(Path(path).read_bytes(), level=level)


def ungzip(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> bytes:
    """Decompress gzip ``data`` with a decompressed-size ``limit``."""
    out = gzip.decompress(data)
    if max_bytes > 0 and len(out) > max_bytes:
        raise SecurityError(f"vzip: gzip data exceeds max bytes: {max_bytes}", code="zip.too_large")
    return out


def ungzip_string(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Decompress gzip ``data`` and decode it as UTF-8 text."""
    return ungzip(data, max_bytes=max_bytes).decode("utf-8")


# --- zlib -------------------------------------------------------------------


def zlib_bytes(data: bytes, *, level: int = 6) -> bytes:
    """Compress ``data`` using zlib at ``level``."""
    return zlib.compress(data, level)


def zlib_string(content: str, *, level: int = 6) -> bytes:
    """Compress UTF-8 ``content`` using zlib at ``level``."""
    return zlib_bytes(content.encode("utf-8"), level=level)


def zlib_file(path: str | Path, *, level: int = 6) -> bytes:
    """Compress the contents of ``path`` using zlib and return the bytes."""
    return zlib_bytes(Path(path).read_bytes(), level=level)


def unzlib(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> bytes:
    """Decompress zlib ``data`` with a decompressed-size ``limit``."""
    out = zlib.decompress(data)
    if max_bytes > 0 and len(out) > max_bytes:
        raise SecurityError(f"vzip: zlib data exceeds max bytes: {max_bytes}", code="zip.too_large")
    return out


def unzlib_string(data: bytes, *, max_bytes: int = DEFAULT_UNZIP_MAX_BYTES) -> str:
    """Decompress zlib ``data`` and decode it as UTF-8 text."""
    return unzlib(data, max_bytes=max_bytes).decode("utf-8")


# ── ZIP reader helpers ────────────────────────────────────────────────────────


def open_zip(path: str | Path) -> zipfile.ZipFile:
    """Open a ZIP file for reading."""
    p = Path(path)
    if not p.exists():
        raise ValidationError(f"vzip: file not found: {path}", code="zip.not_found")
    return zipfile.ZipFile(p, "r")


def get_stream(zf: zipfile.ZipFile, name: str) -> IO[bytes]:
    """Get a reader for a ZIP file entry."""
    try:
        return zf.open(name, "r")
    except KeyError as exc:
        raise ValidationError(f"vzip: entry not found: {name!r}", code="zip.no_entry") from exc


def get(zip_file: str | Path, name: str) -> IO[bytes]:
    """Open a named entry in a ZIP file for reading."""
    with open_zip(zip_file) as zf:
        return get_stream(zf, name)


def get_bytes_with_options(
    zip_file: str | Path,
    name: str,
    *,
    max_bytes: int = DEFAULT_UNZIP_MAX_BYTES,
) -> bytes:
    """Return the uncompressed content of entry ``name`` in ``zip_file``."""
    return get_bytes(zip_file, name, max_bytes=max_bytes)


def read_zip(zip_file: str | Path, consumer: Callable[[zipfile.ZipInfo, IO[bytes]], None]) -> None:
    """Walk every entry in a ZIP file and pass each to ``consumer``."""
    with open_zip(zip_file) as zf:
        for info in zf.infolist():
            with zf.open(info, "r") as src:
                consumer(info, src)


def read_file(path: str | Path) -> bytes:
    """Read a file from disk into bytes (for composing in-memory ZIP entries)."""
    return Path(path).read_bytes()


# ── ZIP writer helpers ────────────────────────────────────────────────────────


def new_zip_writer(out: IO[bytes]) -> zipfile.ZipFile:
    """Create a ZIP writer writing to ``out``."""
    zf = zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED)
    return zf


def zip_to_writer(
    out: IO[bytes],
    src_files: list[str | Path],
    *,
    with_src_dir: bool = False,
) -> None:
    """Write source files into a writer as a ZIP."""
    with new_zip_writer(out) as zf:
        for src in src_files:
            src_path = Path(src)
            if not src_path.exists():
                raise ValidationError(f"vzip: source not found: {src_path}", code="zip.no_source")
            if src_path.is_dir():
                base = src_path.parent if with_src_dir else src_path
                for child in sorted(src_path.rglob("*")):
                    if child.is_file():
                        arcname = child.relative_to(base).as_posix()
                        zf.write(child, _clean_entry_name(arcname))
            else:
                zf.write(src_path, _clean_entry_name(src_path.name))


def zip_files_filter(
    dest: str | Path,
    src_files: list[str | Path],
    *,
    with_src_dir: bool = False,
    file_filter: Callable[[Path], bool] | None = None,
    overwrite: bool = True,
) -> None:
    """Create a ZIP with source path filtering."""
    dest_path = Path(dest)
    if dest_path.exists() and not overwrite:
        raise ValidationError(f"vzip: destination exists: {dest_path}", code="zip.exists")
    if dest_path.parent and not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in src_files:
            src_path = Path(src)
            if not src_path.exists():
                raise ValidationError(f"vzip: source not found: {src_path}", code="zip.no_source")
            if src_path.is_dir():
                base = src_path.parent if with_src_dir else src_path
                for child in sorted(src_path.rglob("*")):
                    if child.is_file() and (file_filter is None or file_filter(child)):
                        arcname = child.relative_to(base).as_posix()
                        zf.write(child, _clean_entry_name(arcname))
            else:
                if file_filter is None or file_filter(src_path):
                    zf.write(src_path, _clean_entry_name(src_path.name))


def zip_entries_to_writer(
    out: IO[bytes],
    entries: list[EntryData],
) -> None:
    """Write in-memory entries into a writer as ZIP."""
    with new_zip_writer(out) as zf:
        for entry in entries:
            zf.writestr(_clean_entry_name(entry.name), entry.data)


def zip_streams(
    dest: str | Path,
    streams: dict[str, IO[bytes]],
    *,
    overwrite: bool = True,
) -> None:
    """Create a ZIP from stream readers."""
    dest_path = Path(dest)
    if dest_path.exists() and not overwrite:
        raise ValidationError(f"vzip: destination exists: {dest_path}", code="zip.exists")
    if dest_path.parent and not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, stream in streams.items():
            zf.writestr(_clean_entry_name(name), stream.read())


def append_to_zip(zip_path: str | Path, src_path: str | Path) -> None:
    """Append a source path into a ZIP by rewriting."""
    src = Path(src_path)
    if not src.exists():
        raise ValidationError(f"vzip: source not found: {src}", code="zip.no_source")
    dest = Path(zip_path)
    entries: list[tuple[str, bytes]] = []

    if dest.exists():
        with zipfile.ZipFile(dest, "r") as zf:
            for info in zf.infolist():
                entries.append((info.filename, zf.read(info.filename)))

    if src.is_dir():
        for child in sorted(src.rglob("*")):
            if child.is_file():
                entries.append((child.relative_to(src.parent).as_posix(), child.read_bytes()))
    else:
        entries.append((src.name, src.read_bytes()))

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            zf.writestr(_clean_entry_name(name), data)


# ── Extraction variants ───────────────────────────────────────────────────────


def unzip_to_limit(
    zip_file: str | Path,
    dest_dir: str | Path,
    *,
    limit: int = DEFAULT_UNZIP_MAX_BYTES,
) -> None:
    """Extract with uncompressed size limit (alias for unzip_to)."""
    unzip_to(zip_file, dest_dir, limit=limit)


def unzip_reader(
    reader: IO[bytes],
    dest_dir: str | Path,
    *,
    limit: int = DEFAULT_UNZIP_MAX_BYTES,
) -> None:
    """Extract from a ZIP reader into ``dest_dir``."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(reader, "r") as zf:
        for info in zf.infolist():
            target = _safe_target(dest, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if limit > 0:
                total += info.file_size
                if total > limit:
                    raise SecurityError(
                        f"vzip: archive exceeds max bytes: {limit}", code="zip.too_large"
                    )
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as out_f:
                out_f.write(src.read())


# ── gzip/zlib reader variants ─────────────────────────────────────────────────


def gzip_reader(data: bytes) -> IO[bytes]:
    """Decompress gzip data and return a reader."""
    return io.BytesIO(gzip.decompress(data))


def gunzip_reader(data: bytes) -> IO[bytes]:
    """Decompress gzip data and return a reader (alias for gzip_reader)."""
    return gzip_reader(data)


def zlib_reader(data: bytes) -> IO[bytes]:
    """Decompress zlib data and return a reader."""
    return io.BytesIO(zlib.decompress(data))


def unzlib_reader(data: bytes) -> IO[bytes]:
    """Decompress zlib data and return a reader (alias for zlib_reader)."""
    return zlib_reader(data)
