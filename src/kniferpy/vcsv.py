from __future__ import annotations

from collections.abc import Sequence

from kniferpy.internal import csvx
from kniferpy.internal.csvx import Record, Row

__all__ = [
    "Record",
    "Row",
    "read_string",
    "read_string_maps",
    "write_string",
    "write_string_maps",
    "records_to_maps",
    "maps_to_records",
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
