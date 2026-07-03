import pytest

from kniferpy import vcsv
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