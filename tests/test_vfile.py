from pathlib import Path

from kniferpy import vfile
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
