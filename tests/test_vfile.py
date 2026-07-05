import io
from pathlib import Path

import pytest

from kniferpy import vfile
from kniferpy.internal import filex
from kniferpy.verr import SecurityError


def test_read_text_limit(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("hello", encoding="utf-8")

    assert vfile.read_text(path, max_bytes=10) == "hello"


def test_read_text_rejects_large_file(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("hello", encoding="utf-8")

    try:
        vfile.read_text(path, max_bytes=3)
    except SecurityError as err:
        assert err.code == "file.too_large"
    else:
        raise AssertionError("expected SecurityError")


def test_safe_join_rejects_traversal(tmp_path: Path) -> None:
    try:
        vfile.safe_join(tmp_path, "../escape.txt")
    except SecurityError as err:
        assert err.code == "file.path_traversal"
    else:
        raise AssertionError("expected SecurityError")


def test_read_write_bytes_create_parent(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data.bin"

    vfile.write_bytes(path, b"abc")

    assert vfile.read_bytes(path, max_bytes=3) == b"abc"


def test_copy_file_enforces_size_limit(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("hello", encoding="utf-8")

    try:
        vfile.copy_file(source, target, max_bytes=3)
    except SecurityError as err:
        assert err.code == "file.too_large"
    else:
        raise AssertionError("expected SecurityError")


def test_copy_file_returns_target(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "nested" / "target.txt"
    source.write_text("hello", encoding="utf-8")

    copied = vfile.copy_file(source, target)

    assert copied == target
    assert target.read_text(encoding="utf-8") == "hello"


def test_atomic_writes_replace_existing_content(tmp_path: Path) -> None:
    text_path = tmp_path / "data.txt"
    bytes_path = tmp_path / "data.bin"
    text_path.write_text("old", encoding="utf-8")
    bytes_path.write_bytes(b"old")

    vfile.write_text_atomic(text_path, "new")
    vfile.write_bytes_atomic(bytes_path, b"new")

    assert text_path.read_text(encoding="utf-8") == "new"
    assert bytes_path.read_bytes() == b"new"


def test_read_write_lines(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data.txt"

    vfile.write_lines(path, ["a", "b", "c"])

    assert vfile.read_lines(path) == ["a", "b", "c"]


def test_safe_join_allows_base_and_nested_paths(tmp_path: Path) -> None:
    nested = vfile.safe_join(tmp_path, "a", "b.txt")

    assert vfile.safe_join(tmp_path) == tmp_path.resolve()
    assert nested == (tmp_path / "a" / "b.txt").resolve()


def test_local_path_and_stat_helpers(tmp_path: Path) -> None:
    file_path = tmp_path / "data.txt"
    dir_path = tmp_path / "dir"
    file_path.write_text("hello", encoding="utf-8")
    dir_path.mkdir()

    assert vfile.is_local_path(str(file_path))
    assert not vfile.is_local_path("https://example.com/a.txt")
    assert not vfile.is_local_path("s3://bucket/key")
    assert vfile.exists(file_path)
    assert vfile.is_file(file_path)
    assert vfile.is_dir(dir_path)
    assert vfile.file_size(file_path) == 5
    assert vfile.size(file_path) == 5
    assert vfile.main_name("archive.tar.gz") == "archive.tar"
    assert vfile.extension("archive.tar.gz") == ".gz"


def test_append_touch_mkdir_and_delete(tmp_path: Path) -> None:
    dir_path = tmp_path / "nested"
    text_path = dir_path / "data.txt"
    bytes_path = dir_path / "data.bin"

    vfile.mkdir(dir_path)
    vfile.touch(text_path)
    vfile.append_text(text_path, "a")
    vfile.append_text(text_path, "b")
    vfile.append_bytes(bytes_path, b"a")
    vfile.append_bytes(bytes_path, b"b")

    assert text_path.read_text(encoding="utf-8") == "ab"
    assert bytes_path.read_bytes() == b"ab"
    vfile.delete(text_path)
    assert not text_path.exists()
    vfile.delete(dir_path)
    assert not dir_path.exists()
    vfile.delete(dir_path)


def test_reader_helpers_and_limits() -> None:
    chunks: list[bytes] = []

    assert vfile.read_all(io.BytesIO(b"hello"), max_bytes=10) == b"hello"
    assert vfile.reader_read_string(io.BytesIO("hé".encode()), max_bytes=10) == "hé"
    assert vfile.reader_read_lines(io.BytesIO(b"a\nb\n"), keepends=True) == ["a\n", "b\n"]
    vfile.read_chunks(io.BytesIO(b"abcdef"), chunks.append, buffer_size=2, max_bytes=10)
    assert chunks == [b"ab", b"cd", b"ef"]

    with pytest.raises(SecurityError) as read_exc:
        vfile.read_all(io.BytesIO(b"abcdef"), max_bytes=3)
    with pytest.raises(SecurityError) as chunks_exc:
        vfile.read_chunks(io.BytesIO(b"abcdef"), lambda chunk: None, buffer_size=2, max_bytes=3)
    assert read_exc.value.code == "file.too_large"
    assert chunks_exc.value.code == "file.too_large"


def test_reader_factories_copy_stream_and_close_quietly() -> None:
    string_reader = vfile.reader_from_string("hello")
    bytes_reader = vfile.reader_from_bytes(b"hello")
    dst = io.BytesIO()

    assert string_reader.read() == "hello"
    assert bytes_reader.read() == b"hello"
    assert vfile.copy_stream(dst, io.BytesIO(b"abcdef"), buffer_size=2) == 6
    assert dst.getvalue() == b"abcdef"
    vfile.close_quietly(io.BytesIO(b"x"))
    vfile.close_quietly(None)

    class BadClose(io.BytesIO):
        def close(self) -> None:
            if not getattr(self, "_already_failed", False):
                self._already_failed = True
                raise RuntimeError("close failed")
            super().close()

    vfile.close_quietly(BadClose(b"x"))


def test_file_aliases_and_chunks(tmp_path: Path) -> None:
    text_path = tmp_path / "data.txt"
    bytes_path = tmp_path / "data.bin"
    chunks: list[bytes] = []

    vfile.write_file_string(text_path, "a\nb\n")
    vfile.write_file_bytes(bytes_path, b"abcdef")
    vfile.append_file_string(text_path, "c")
    vfile.read_file_chunks(bytes_path, chunks.append, buffer_size=3)

    assert vfile.read_file_string(text_path) == "a\nb\nc"
    assert vfile.read_file_bytes(bytes_path) == b"abcdef"
    assert vfile.read_file_lines(text_path, keepends=False) == ["a", "b", "c"]
    assert chunks == [b"abc", b"def"]


@pytest.mark.parametrize(
    ("data", "mime", "extension", "category"),
    [
        (b"\xff\xd8\xff\x00", "image/jpeg", ".jpg", "image"),
        (b"\x89PNG\r\n\x1a\nrest", "image/png", ".png", "image"),
        (b"GIF87a", "image/gif", ".gif", "image"),
        (b"GIF89a", "image/gif", ".gif", "image"),
        (b"RIFFxxxxWEBP", "image/webp", ".webp", "image"),
        (b"RIFFxxxxWAVE", "audio/wav", ".wav", "audio"),
        (b"%PDF-1.7", "application/pdf", ".pdf", "document"),
        (b"\x1f\x8b\x08rest", "application/gzip", ".gz", "archive"),
        (b"\x42\x5a\x68rest", "application/bzip2", ".bz2", "archive"),
        (b"\x7fELFrest", "application/x-elf", "", "executable"),
        (b"II*\x00rest", "image/tiff", ".tiff", "image"),
        (b"MM\x00*rest", "image/tiff", ".tiff", "image"),
        (b"\x00\x00\x01\x00rest", "image/x-icon", ".ico", "image"),
        (b"BMrest", "image/bmp", ".bmp", "image"),
        (b"\x1a\x45\xdf\xa3rest", "video/webm", ".webm", "video"),
        (b"OggSrest", "audio/ogg", ".ogg", "audio"),
        (b"ID3rest", "audio/mpeg", ".mp3", "audio"),
        (b"fLaCrest", "audio/flac", ".flac", "audio"),
        (b"\x00\x00\x00\x1c\x66\x74\x79\x70rest", "video/mp4", ".mp4", "video"),
        (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest", "application/msword", ".doc", "document"),
    ],
)
def test_detect_file_type_known_signatures(
    data: bytes,
    mime: str,
    extension: str,
    category: str,
) -> None:
    ft = vfile.detect_file_type(data)

    assert ft.mime == mime
    assert ft.extension == extension
    assert ft.category == category


def test_detect_file_type_unknown_special_cases_and_categories(tmp_path: Path) -> None:
    webp_unknown = vfile.detect_file_type(b"RIFFxxxx????")
    pk_unknown = vfile.detect_file_type(b"PK\x03\x04rest")
    short = vfile.detect_file_type(b"x")
    generic_mp4 = vfile.detect_file_type(b"\x00\x00\x00rest")
    unknown_path = tmp_path / "missing.bin"
    png_path = tmp_path / "image.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\nrest")

    assert webp_unknown == vfile.UNKNOWN_FILE_TYPE
    assert pk_unknown == vfile.UNKNOWN_FILE_TYPE
    assert short == vfile.UNKNOWN_FILE_TYPE
    assert generic_mp4 == vfile.FileType("video/mp4", ".mp4", "video")
    assert vfile.detect_file_type_from_path(unknown_path) == vfile.UNKNOWN_FILE_TYPE
    assert vfile.detect_file_type_from_path(png_path).mime == "image/png"
    assert vfile.is_image(vfile.FileType(category=vfile.FileCategoryImage))
    assert vfile.is_video(vfile.FileType(category=vfile.FileCategoryVideo))
    assert vfile.is_audio(vfile.FileType(category=vfile.FileCategoryAudio))
    assert vfile.is_archive(vfile.FileType(category=vfile.FileCategoryArchive))
    assert vfile.is_document(vfile.FileType(category=vfile.FileCategoryDocument))
    assert vfile.FileCategoryUnknown == "unknown"
    assert vfile.FileCategoryFont == "font"
    assert vfile.FileCategoryExecutable == "executable"


def test_detect_file_type_from_reader_resets_reader_and_handles_errors() -> None:
    reader = io.BytesIO(b"%PDF-1.7")
    ft = vfile.detect_file_type_from_reader(reader)

    assert ft.mime == "application/pdf"
    assert reader.tell() == 0
    assert vfile.detect_file_type_from_reader(object()) == vfile.UNKNOWN_FILE_TYPE

    class BadReader(io.BytesIO):
        def read(self, size=-1):  # type: ignore[no-untyped-def]
            raise OSError("read failed")

    assert vfile.detect_file_type_from_reader(BadReader()) == vfile.UNKNOWN_FILE_TYPE


def test_internal_ensure_size_and_default_constants(tmp_path: Path) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"abcd")

    filex._ensure_size(path, max_bytes=4)
    with pytest.raises(SecurityError) as exc_info:
        filex._ensure_size(path, max_bytes=3)
    assert exc_info.value.context == {"size": 4, "max_bytes": 3}
    assert vfile.DEFAULT_MAX_BYTES == 64 << 20
