import csv
import io
from dataclasses import dataclass, field

import pytest

from kniferpy import vcsv
from kniferpy.internal import csvx
from kniferpy.verr import ValidationError


def test_read_string_records() -> None:
    records = vcsv.read_string("a,b,c\n1,2,3\n4,5,6\n")
    assert records == [["a", "b", "c"], ["1", "2", "3"], ["4", "5", "6"]]


def test_read_string_custom_delimiter_and_trim() -> None:
    records = vcsv.read_string("a; b; c", delimiter=";", trim_leading_space=True)
    assert records == [["a", "b", "c"]]


def test_read_string_tab_delimiter() -> None:
    records = vcsv.read_string("a\tb\tc\n1\t2\t3\n", delimiter="\t")
    assert records == [["a", "b", "c"], ["1", "2", "3"]]


def test_read_string_empty() -> None:
    records = vcsv.read_string("")
    assert records == []


def test_read_string_only_header() -> None:
    records = vcsv.read_string("a,b,c")
    assert records == [["a", "b", "c"]]


def test_read_string_maps() -> None:
    rows = vcsv.read_string_maps("name,age\nalice,30\nbob,25\n")
    assert rows == [
        {"name": "alice", "age": "30"},
        {"name": "bob", "age": "25"},
    ]


def test_read_string_maps_empty() -> None:
    assert vcsv.read_string_maps("") == []


def test_read_string_maps_header_only() -> None:
    assert vcsv.read_string_maps("name,age") == []


def test_read_string_maps_short_and_empty_headers() -> None:
    rows = vcsv.read_string_maps("name,,age\nalice,x\n")
    assert rows == [{"name": "alice", "age": ""}]


def test_write_string_roundtrip() -> None:
    out = vcsv.write_string([["a", "b"], ["1", "2"]])
    assert out == "a,b\n1,2\n"
    assert vcsv.read_string(out) == [["a", "b"], ["1", "2"]]


def test_write_string_crlf_and_quoting() -> None:
    out = vcsv.write_string([["a", "b,c"]], use_crlf=True)
    assert out == 'a,"b,c"\r\n'


def test_write_string_crlf_disabled() -> None:
    out = vcsv.write_string([["a", "b"]], use_crlf=False)
    assert out == "a,b\n"


def test_write_string_maps() -> None:
    out = vcsv.write_string_maps(
        ["name", "age"],
        [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}],
    )
    assert out == "name,age\nalice,30\nbob,25\n"


def test_write_string_maps_empty() -> None:
    out = vcsv.write_string_maps(["name", "age"], [])
    assert out == "name,age\n"


def test_write_string_maps_missing_keys() -> None:
    out = vcsv.write_string_maps(
        ["name", "age"],
        [{"name": "alice"}],
    )
    assert out == "name,age\nalice,\n"


def test_write_string_maps_custom_delimiter() -> None:
    out = vcsv.write_string_maps(
        ["name", "age"],
        [{"name": "alice", "age": "30"}],
        delimiter=";",
    )
    assert out == "name;age\nalice;30\n"


def test_maps_records_conversions() -> None:
    records = [["name", "age"], ["alice", "30"]]
    maps = vcsv.records_to_maps(records)
    assert maps == [{"name": "alice", "age": "30"}]
    assert vcsv.maps_to_records(["name", "age"], maps) == records
    assert vcsv.records_to_maps([]) == []
    assert vcsv.maps_to_records(["a", "b"], [{"a": "1"}]) == [["a", "b"], ["1", ""]]


def test_maps_to_records_empty_rows() -> None:
    assert vcsv.maps_to_records(["a", "b"], []) == [["a", "b"]]


def test_maps_to_records_extra_headers() -> None:
    records = vcsv.maps_to_records(["a", "b", "c"], [{"a": "1", "b": "2"}])
    assert records == [["a", "b", "c"], ["1", "2", ""]]


def test_csv_error_is_validation_error() -> None:
    assert issubclass(vcsv.CSVError, ValidationError)
    assert vcsv.Error is vcsv.CSVError


def test_read_string_wraps_csv_errors(monkeypatch) -> None:
    class FailingReader:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def __iter__(self):
            raise csv.Error("bad csv")

    monkeypatch.setattr(csvx.csv, "reader", FailingReader)

    with pytest.raises(ValidationError) as exc_info:
        vcsv.read_string("bad")

    assert exc_info.value.code == "knifer.csv.invalid_input"


def test_file_read_write_and_map_variants(tmp_path) -> None:
    records_path = tmp_path / "records.csv"
    maps_path = tmp_path / "maps.csv"

    vcsv.write(str(records_path), [["name", "age"], ["alice", "30"]], delimiter=";", use_crlf=True)
    assert records_path.read_bytes() == b"name;age\r\nalice;30\r\n"
    assert vcsv.read(str(records_path), delimiter=";") == [["name", "age"], ["alice", "30"]]
    assert vcsv.read_maps(str(records_path), delimiter=";") == [{"name": "alice", "age": "30"}]

    vcsv.write_maps(
        str(maps_path),
        ["name", "age"],
        [{"name": "bob", "age": "25"}],
        delimiter=";",
        use_crlf=False,
    )
    assert maps_path.read_text(encoding="utf-8") == "name;age\nbob;25\n"
    assert vcsv.read_maps(str(maps_path), delimiter=";") == [{"name": "bob", "age": "25"}]


def test_for_each_and_for_each_map(tmp_path) -> None:
    path = tmp_path / "records.csv"
    path.write_text("name,age\nalice,30\nbob,25\n", encoding="utf-8")
    records: list[list[str]] = []
    rows: list[dict[str, str]] = []

    vcsv.for_each(str(path), records.append)
    vcsv.for_each_map(str(path), rows.append)

    assert records == [["name", "age"], ["alice", "30"], ["bob", "25"]]
    assert rows == [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}]


def test_structs_to_records_dataclass_plain_object_and_empty() -> None:
    @dataclass
    class User:
        name: str = field(metadata={"csv": "user_name"})
        age: int = 0
        secret: str = field(default="", metadata={"csv": "-"})

    class Plain:
        def __init__(self) -> None:
            self.name = "plain"
            self.age = 9
            self._private = "skip"

    users = [User("alice", 30, "x"), User("bob", 25, "y")]
    plain = [Plain()]

    assert vcsv.structs_to_records([]) == []
    assert vcsv.structs_to_records(users) == [
        ["user_name", "age"],
        ["alice", "30"],
        ["bob", "25"],
    ]
    assert vcsv.structs_to_records(plain) == [["name", "age"], ["plain", "9"]]
    assert vcsv.structs_to_records([object()]) == [[], []]


def test_write_structs_and_write_string_structs() -> None:
    @dataclass
    class User:
        name: str
        age: int

    users = [User("alice", 30), User("bob", 25)]
    writer = io.StringIO()

    vcsv.write_structs(writer, users, delimiter=";", use_crlf=True)
    assert writer.getvalue() == "name;age\r\nalice;30\r\nbob;25\r\n"
    assert vcsv.write_string_structs(users) == "name,age\nalice,30\nbob,25\n"
