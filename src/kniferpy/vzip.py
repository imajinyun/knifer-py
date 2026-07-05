"""ZIP archive and gzip/zlib compression utilities.

Create and extract ZIP archives, read archive entries, and compress or
decompress data with gzip and zlib. Extraction is safe by default: entry names
are checked for path traversal (zip-slip) and the total uncompressed size is
bounded to guard against zip bombs.
"""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any, Callable

from kniferpy.internal import zipx
from kniferpy.internal.zipx import (
    DEFAULT_UNZIP_MAX_BYTES,
    EntryData,
    CreateTempFunc,
    EvalSymlinksFunc,
    LstatFunc,
    MkdirAllFunc,
    OpenFileFunc,
    OpenFunc,
    OpenZipReaderFunc,
    ReadDirFunc,
    ReadFileFunc,
    ReadlinkFunc,
    RemoveFunc,
    RenameFunc,
    StatFunc,
    gunzip,
)

# ── Go-compat type aliases ─────────────────────────────────────────────────────

Entry = EntryData  # Go: zipimpl.Entry
StreamEntry = Any  # Go: zipimpl.StreamEntry
ArchiveOption = Callable[[Any], None]  # Go: functional option pattern
Writer = Any  # Go: zipimpl.Writer
Reader = Any  # Go: zipimpl.Reader
FileFilter = Callable[[str], bool]  # Go: zipimpl.FileFilter
ZipError = type("ZipError", (Exception,), {})  # Go: zipimpl.ZipError

__all__ = [
    "DEFAULT_UNZIP_MAX_BYTES",
    "EntryData",
    "append_to_zip",
    "get",
    "get_bytes",
    "get_bytes_with_options",
    "get_stream",
    "gunzip",
    "gunzip_reader",
    "gzip_bytes",
    "gzip_file",
    "gzip_reader",
    "gzip_reader_from_stream",
    "gzip_string",
    "list_file_names",
    "new_zip_writer",
    "open_zip",
    "read_entries",
    "read_file",
    "read_zip",
    "ungzip",
    "ungzip_reader_from_stream",
    "ungzip_string",
    "unzip",
    "unzip_reader",
    "unzip_to",
    "unzip_to_limit",
    "unzlib",
    "unzlib_reader",
    "unzlib_reader_from_stream",
    "unzlib_string",
    "zip_archive",
    "zip_bytes",
    "zip_data",
    "zip_entries",
    "zip_entries_to_writer",
    "zip_files",
    "zip_files_filter",
    "zip_streams",
    "zip_streams_to_writer",
    "zip_to",
    "zip_to_writer",
    "zlib_bytes",
    "zlib_file",
    "zlib_reader",
    "zlib_reader_from_stream",
    "zlib_string",
    # Go-compat type aliases
    "Entry",
    "StreamEntry",
    "ArchiveOption",
    "Writer",
    "Reader",
    "FileFilter",
    "ZipError",
    # Go-compat file operation func types
    "OpenFunc",
    "ReadFileFunc",
    "OpenFileFunc",
    "EvalSymlinksFunc",
    "StatFunc",
    "LstatFunc",
    "ReadDirFunc",
    "ReadlinkFunc",
    "MkdirAllFunc",
    "RemoveFunc",
    "RenameFunc",
    "OpenZipReaderFunc",
    "CreateTempFunc",
]

# ── ZIP creation ──────────────────────────────────────────────────────────────

zip_entries = zipx.zip_entries
zip_bytes = zipx.zip_bytes
zip_data = zipx.zip_data
zip_files = zipx.zip_files
zip_to = zipx.zip_to
zip_archive = zipx.zip_archive
zip_files_filter = zipx.zip_files_filter
zip_to_writer = zipx.zip_to_writer
zip_entries_to_writer = zipx.zip_entries_to_writer
zip_streams = zipx.zip_streams
append_to_zip = zipx.append_to_zip
new_zip_writer = zipx.new_zip_writer

# ── ZIP reading / extraction ──────────────────────────────────────────────────

open_zip = zipx.open_zip
get_stream = zipx.get_stream
get = zipx.get
get_bytes = zipx.get_bytes
get_bytes_with_options = zipx.get_bytes_with_options
read_zip = zipx.read_zip
read_file = zipx.read_file
read_entries = zipx.read_entries
list_file_names = zipx.list_file_names
unzip_to = zipx.unzip_to
unzip_to_limit = zipx.unzip_to_limit
unzip = zipx.unzip
unzip_reader = zipx.unzip_reader

# ── gzip ──────────────────────────────────────────────────────────────────────

gzip_bytes = zipx.gzip_bytes
gzip_string = zipx.gzip_string
gzip_file = zipx.gzip_file
ungzip = zipx.ungzip
gunzip = zipx.gunzip
ungzip_string = zipx.ungzip_string
gzip_reader = zipx.gzip_reader
gunzip_reader = zipx.gunzip_reader
gzip_reader_from_stream = zipx.gzip_reader_from_stream
ungzip_reader_from_stream = zipx.ungzip_reader_from_stream

# ── zlib ──────────────────────────────────────────────────────────────────────

zlib_bytes = zipx.zlib_bytes
zlib_string = zipx.zlib_string
zlib_file = zipx.zlib_file
unzlib = zipx.unzlib
unzlib_string = zipx.unzlib_string
zlib_reader = zipx.zlib_reader
unzlib_reader = zipx.unzlib_reader
zlib_reader_from_stream = zipx.zlib_reader_from_stream
unzlib_reader_from_stream = zipx.unzlib_reader_from_stream
zip_streams_to_writer = zipx.zip_streams_to_writer