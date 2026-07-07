from __future__ import annotations

from collections.abc import Sequence

from kniferpy.internal import csvx
from kniferpy.internal.csvx import (
    CSVError,
    Option,
    ReadOption,
    Record,
    Row,
    WriteOption,
    structs_to_records,
    write_string_structs,
    write_structs,
)

# ── Go-compat type alias ────────────────────────────────────────────────────

Error = CSVError  # type: ignore[assignment]

__all__ = [
    "CSVError",
    "Option",
    "ReadOption",
    "Record",
    "Row",
    "WriteOption",
    "read_string",
    "read_string_maps",
    "write_string",
    "write_string_maps",
    "records_to_maps",
    "maps_to_records",
    "read",
    "read_maps",
    "write",
    "write_maps",
    "for_each",
    "for_each_map",
    "structs_to_records",
    "write_structs",
    "write_string_structs",
    # Go-compat type alias
    "Error",
]


def read_string(
    text: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
) -> list[Record]:
    return csvx.read_string(text, delimiter, trim_leading_space)


def read_string_maps(
    text: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
) -> list[Row]:
    return csvx.read_string_maps(text, delimiter, trim_leading_space)


def write_string(
    records: Sequence[Sequence[str]],
    delimiter: str = ",",
    use_crlf: bool = False,
) -> str:
    return csvx.write_string(records, delimiter, use_crlf)


def write_string_maps(
    headers: Sequence[str],
    rows: Sequence[Row],
    delimiter: str = ",",
    use_crlf: bool = False,
) -> str:
    return csvx.write_string_maps(headers, rows, delimiter, use_crlf)


def records_to_maps(records: Sequence[Sequence[str]]) -> list[Row]:
    return csvx.records_to_maps(records)


def maps_to_records(headers: Sequence[str], rows: Sequence[Row]) -> list[Record]:
    return csvx.maps_to_records(headers, rows)


def read(
    path: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> list[Record]:
    return csvx.read(path, delimiter, trim_leading_space, encoding)


def read_maps(
    path: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> list[Row]:
    return csvx.read_maps(path, delimiter, trim_leading_space, encoding)


def write(
    path: str,
    records: Sequence[Sequence[str]],
    delimiter: str = ",",
    use_crlf: bool = False,
    encoding: str = "utf-8",
) -> None:
    csvx.write(path, records, delimiter, use_crlf, encoding)


def write_maps(
    path: str,
    headers: Sequence[str],
    rows: Sequence[Row],
    delimiter: str = ",",
    use_crlf: bool = False,
    encoding: str = "utf-8",
) -> None:
    csvx.write_maps(path, headers, rows, delimiter, use_crlf, encoding)


def for_each(
    path: str,
    callback,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> None:
    csvx.for_each(path, callback, delimiter, trim_leading_space, encoding)


def for_each_map(
    path: str,
    callback,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> None:
    csvx.for_each_map(path, callback, delimiter, trim_leading_space, encoding)
