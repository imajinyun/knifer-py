from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from kniferpy import vzip
from kniferpy.verr import SecurityError, ValidationError


def test_zip_bytes_and_get_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_bytes(archive, "hello.txt", b"world")
    assert vzip.get_bytes(archive, "hello.txt") == b"world"


def test_zip_data_roundtrip(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_data(archive, "note.txt", "café")
    assert vzip.get_bytes(archive, "note.txt").decode("utf-8") == "café"


def test_zip_entries(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_entries(
        archive,
        [vzip.EntryData("a.txt", b"A"), vzip.EntryData("dir/b.txt", b"B")],
    )
    assert sorted(vzip.read_entries(archive)) == ["a.txt", "dir/b.txt"]
    assert vzip.get_bytes(archive, "dir/b.txt") == b"B"


def test_zip_entries_no_overwrite(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    archive.write_bytes(b"existing")
    with pytest.raises(ValidationError):
        vzip.zip_entries(archive, [vzip.EntryData("x", b"y")], overwrite=False)


def test_zip_files_flat(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("1")
    (tmp_path / "two.txt").write_text("2")
    archive = tmp_path / "out.zip"
    vzip.zip_files(archive, [tmp_path / "one.txt", tmp_path / "two.txt"])
    assert sorted(vzip.read_entries(archive)) == ["one.txt", "two.txt"]


def test_zip_files_directory_without_src_dir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "nested").mkdir(parents=True)
    (src / "a.txt").write_text("A")
    (src / "nested" / "b.txt").write_text("B")
    archive = tmp_path / "out.zip"
    vzip.zip_files(archive, [src], with_src_dir=False)
    assert sorted(vzip.read_entries(archive)) == ["a.txt", "nested/b.txt"]


def test_zip_files_directory_with_src_dir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("A")
    archive = tmp_path / "out.zip"
    vzip.zip_files(archive, [src], with_src_dir=True)
    assert vzip.read_entries(archive) == ["src/a.txt"]


def test_zip_files_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        vzip.zip_files(tmp_path / "out.zip", [tmp_path / "nope.txt"])


def test_zip_to_and_zip_archive(tmp_path: Path) -> None:
    src = tmp_path / "data.txt"
    src.write_text("payload")
    dest = vzip.zip_archive(src)
    assert dest == str(tmp_path / "data.zip")
    assert vzip.get_bytes(dest, "data.txt") == b"payload"


def test_unzip_to(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_entries(
        archive,
        [vzip.EntryData("a.txt", b"A"), vzip.EntryData("dir/b.txt", b"B")],
    )
    out = tmp_path / "out"
    vzip.unzip_to(archive, out)
    assert (out / "a.txt").read_bytes() == b"A"
    assert (out / "dir" / "b.txt").read_bytes() == b"B"


def test_unzip_creates_sibling_dir(tmp_path: Path) -> None:
    archive = tmp_path / "bundle.zip"
    vzip.zip_bytes(archive, "x.txt", b"X")
    dest = vzip.unzip(archive)
    assert dest == str(tmp_path / "bundle")
    assert (Path(dest) / "x.txt").read_bytes() == b"X"


def test_unzip_rejects_path_traversal(tmp_path: Path) -> None:
    # Hand-craft a malicious archive with a zip-slip entry name.
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", b"pwned")
    with pytest.raises(SecurityError):
        vzip.unzip_to(archive, tmp_path / "out")


def test_unzip_size_limit(tmp_path: Path) -> None:
    archive = tmp_path / "big.zip"
    vzip.zip_bytes(archive, "a.txt", b"0123456789")
    with pytest.raises(SecurityError):
        vzip.unzip_to(archive, tmp_path / "out", limit=5)


def test_get_bytes_missing_entry(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_bytes(archive, "a.txt", b"A")
    with pytest.raises(ValidationError):
        vzip.get_bytes(archive, "missing.txt")


def test_get_bytes_size_limit(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_bytes(archive, "a.txt", b"0123456789")
    with pytest.raises(SecurityError):
        vzip.get_bytes(archive, "a.txt", max_bytes=5)


def test_list_file_names_root(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_entries(
        archive,
        [
            vzip.EntryData("a.txt", b"A"),
            vzip.EntryData("b.txt", b"B"),
            vzip.EntryData("dir/c.txt", b"C"),
        ],
    )
    # Only direct children of the root, no descent into "dir/".
    assert sorted(vzip.list_file_names(archive)) == ["a.txt", "b.txt"]


def test_list_file_names_subdir(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_entries(
        archive,
        [vzip.EntryData("dir/c.txt", b"C"), vzip.EntryData("dir/sub/d.txt", b"D")],
    )
    assert vzip.list_file_names(archive, "dir") == ["c.txt"]


def test_gzip_roundtrip() -> None:
    blob = b"the quick brown fox" * 10
    compressed = vzip.gzip_bytes(blob)
    assert vzip.ungzip(compressed) == blob


def test_gzip_string_roundtrip() -> None:
    compressed = vzip.gzip_string("héllo")
    assert vzip.ungzip_string(compressed) == "héllo"


def test_gzip_file(tmp_path: Path) -> None:
    src = tmp_path / "data.bin"
    src.write_bytes(b"payload-bytes")
    assert vzip.ungzip(vzip.gzip_file(src)) == b"payload-bytes"


def test_ungzip_size_limit() -> None:
    compressed = vzip.gzip_bytes(b"0123456789")
    with pytest.raises(SecurityError):
        vzip.ungzip(compressed, max_bytes=5)


def test_zlib_roundtrip() -> None:
    blob = b"lorem ipsum dolor" * 8
    compressed = vzip.zlib_bytes(blob, level=9)
    assert vzip.unzlib(compressed) == blob


def test_zlib_string_roundtrip() -> None:
    compressed = vzip.zlib_string("wörld")
    assert vzip.unzlib_string(compressed) == "wörld"


def test_zlib_file(tmp_path: Path) -> None:
    src = tmp_path / "data.bin"
    src.write_bytes(b"zlib-payload")
    assert vzip.unzlib(vzip.zlib_file(src)) == b"zlib-payload"


def test_unzlib_size_limit() -> None:
    compressed = vzip.zlib_bytes(b"0123456789")
    with pytest.raises(SecurityError):
        vzip.unzlib(compressed, max_bytes=5)


def test_zip_entry_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        vzip.zip_entries(tmp_path / "a.zip", [vzip.EntryData("/abs.txt", b"x")])


def test_clean_entry_name_rejects_traversal_and_windows_absolute() -> None:
    from kniferpy.internal import zipx

    assert zipx._clean_entry_name("a/./b.txt") == "a/b.txt"
    assert zipx._clean_entry_name(r"a\b.txt") == "a/b.txt"
    for name in ("", "../x.txt", "/abs.txt", "C:/abs.txt", "a/../b.txt"):
        with pytest.raises(ValidationError):
            zipx._clean_entry_name(name)


def test_safe_target_rejects_absolute_and_traversal(tmp_path: Path) -> None:
    from kniferpy.internal import zipx

    assert zipx._safe_target(tmp_path, "dir/a.txt") == (tmp_path / "dir" / "a.txt").resolve()
    for name in ("../x.txt", "/x.txt"):
        with pytest.raises(SecurityError):
            zipx._safe_target(tmp_path, name)


def test_zip_bytes_no_overwrite_and_zip_data_invalid_name(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    vzip.zip_bytes(archive, "a.txt", b"A")

    with pytest.raises(ValidationError) as exists_exc:
        vzip.zip_bytes(archive, "b.txt", b"B", overwrite=False)
    with pytest.raises(ValidationError) as name_exc:
        vzip.zip_data(tmp_path / "bad.zip", "../bad.txt", "bad")

    assert exists_exc.value.code == "zip.exists"
    assert name_exc.value.code == "zip.invalid_name"


def test_zip_files_no_overwrite_and_filter(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "keep.txt").write_text("keep")
    (src / "skip.log").write_text("skip")
    archive = tmp_path / "filtered.zip"

    vzip.zip_files_filter(
        archive,
        [src],
        file_filter=lambda path: path.suffix == ".txt",
        with_src_dir=True,
    )

    assert vzip.read_entries(archive) == ["src/keep.txt"]
    with pytest.raises(ValidationError):
        vzip.zip_files_filter(archive, [src], overwrite=False)
    with pytest.raises(ValidationError):
        vzip.zip_files_filter(tmp_path / "missing.zip", [tmp_path / "missing"])


def test_zip_to_writer_entries_streams_and_append(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("A")
    archive = tmp_path / "append.zip"
    writer = io.BytesIO()
    entries_writer = io.BytesIO()
    streams_writer = io.BytesIO()

    vzip.zip_to_writer(writer, [src], with_src_dir=False)
    with zipfile.ZipFile(io.BytesIO(writer.getvalue()), "r") as zf:
        assert zf.namelist() == ["a.txt"]
        assert zf.read("a.txt") == b"A"

    vzip.zip_entries_to_writer(entries_writer, [vzip.EntryData("b.txt", b"B")])
    with zipfile.ZipFile(io.BytesIO(entries_writer.getvalue()), "r") as zf:
        assert zf.read("b.txt") == b"B"

    vzip.zip_streams_to_writer(streams_writer, {"c.txt": io.BytesIO(b"C")})
    with zipfile.ZipFile(io.BytesIO(streams_writer.getvalue()), "r") as zf:
        assert zf.read("c.txt") == b"C"

    vzip.zip_bytes(archive, "old.txt", b"OLD")
    vzip.append_to_zip(archive, src / "a.txt")
    vzip.append_to_zip(archive, src)
    assert sorted(vzip.read_entries(archive)) == ["a.txt", "old.txt", "src/a.txt"]
    with pytest.raises(ValidationError):
        vzip.append_to_zip(archive, tmp_path / "missing.txt")
    with pytest.raises(ValidationError):
        vzip.zip_to_writer(io.BytesIO(), [tmp_path / "missing.txt"])


def test_zip_streams_file_and_overwrite(tmp_path: Path) -> None:
    archive = tmp_path / "streams.zip"
    vzip.zip_streams(archive, {"a.txt": io.BytesIO(b"A")})

    assert vzip.get_bytes(archive, "a.txt") == b"A"
    with pytest.raises(ValidationError):
        vzip.zip_streams(archive, {"b.txt": io.BytesIO(b"B")}, overwrite=False)


def test_open_zip_get_stream_read_zip_and_read_file(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    src = tmp_path / "src.txt"
    seen: list[tuple[str, bytes]] = []
    src.write_bytes(b"source")
    vzip.zip_entries(archive, [vzip.EntryData("a.txt", b"A"), vzip.EntryData("dir/b.txt", b"B")])

    with vzip.open_zip(archive) as zf:
        with vzip.get_stream(zf, "a.txt") as stream:
            assert stream.read() == b"A"
        with pytest.raises(ValidationError):
            vzip.get_stream(zf, "missing.txt")

    with vzip.get(archive, "a.txt") as stream:
        assert stream.read() == b"A"
    assert vzip.get_bytes_with_options(archive, "dir/b.txt", max_bytes=10) == b"B"
    vzip.read_zip(archive, lambda info, stream: seen.append((info.filename, stream.read())))
    assert seen == [("a.txt", b"A"), ("dir/b.txt", b"B")]
    assert vzip.read_file(src) == b"source"
    with pytest.raises(ValidationError):
        vzip.open_zip(tmp_path / "missing.zip")


def test_unzip_reader_directory_and_limit(tmp_path: Path) -> None:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as zf:
        zf.writestr("dir/", b"")
        zf.writestr("dir/a.txt", b"A")
    payload.seek(0)
    out = tmp_path / "out"
    vzip.unzip_reader(payload, out)
    assert (out / "dir").is_dir()
    assert (out / "dir" / "a.txt").read_bytes() == b"A"

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as zf:
        zf.writestr("big.txt", b"0123456789")
    payload.seek(0)
    with pytest.raises(SecurityError):
        vzip.unzip_reader(payload, tmp_path / "limited", limit=5)

    archive = tmp_path / "limited.zip"
    vzip.zip_bytes(archive, "a.txt", b"A")
    vzip.unzip_to_limit(archive, tmp_path / "limit-ok", limit=10)
    assert (tmp_path / "limit-ok" / "a.txt").read_bytes() == b"A"


def test_gzip_zlib_reader_variants() -> None:
    gzip_data = vzip.gzip_bytes(b"hello")
    zlib_data = vzip.zlib_bytes(b"world")

    assert vzip.gzip_reader(gzip_data).read() == b"hello"
    assert vzip.gunzip_reader(gzip_data).read() == b"hello"
    assert vzip.zlib_reader(zlib_data).read() == b"world"
    assert vzip.unzlib_reader(zlib_data).read() == b"world"
    assert vzip.gunzip(gzip_data) == b"hello"
    assert vzip.ungzip_reader_from_stream(io.BytesIO(gzip_data)) == b"hello"
    assert vzip.unzlib_reader_from_stream(io.BytesIO(zlib_data)) == b"world"
    assert vzip.ungzip(vzip.gzip_reader_from_stream(io.BytesIO(b"stream"))) == b"stream"
    assert vzip.unzlib(vzip.zlib_reader_from_stream(io.BytesIO(b"stream"))) == b"stream"
