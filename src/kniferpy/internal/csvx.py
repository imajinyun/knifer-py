from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from kniferpy.verr import ValidationError

Record = list[str]
Row = dict[str, str]


def read_string(
    text: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
) -> list[Record]:
    reader = csv.reader(
        io.StringIO(text),
        delimiter=delimiter,
        skipinitialspace=trim_leading_space,
    )
    try:
        return [list(record) for record in reader]
    except csv.Error as exc:
        raise ValidationError(
            message=f"invalid CSV input: {exc}",
            code="knifer.csv.invalid_input",
        ) from exc


def read_string_maps(
    text: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
) -> list[Row]:
    return records_to_maps(read_string(text, delimiter, trim_leading_space))


def write_string(
    records: Sequence[Sequence[str]],
    delimiter: str = ",",
    use_crlf: bool = False,
) -> str:
    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter=delimiter,
        lineterminator="\r\n" if use_crlf else "\n",
    )
    writer.writerows([list(record) for record in records])
    return buffer.getvalue()


def write_string_maps(
    headers: Sequence[str],
    rows: Sequence[Row],
    delimiter: str = ",",
    use_crlf: bool = False,
) -> str:
    return write_string(maps_to_records(headers, rows), delimiter, use_crlf)


def records_to_maps(records: Sequence[Sequence[str]]) -> list[Row]:
    if not records:
        return []
    headers = list(records[0])
    rows: list[Row] = []
    for record in records[1:]:
        row: Row = {}
        for index, header in enumerate(headers):
            if header == "":
                continue
            row[header] = record[index] if index < len(record) else ""
        rows.append(row)
    return rows


def maps_to_records(headers: Sequence[str], rows: Sequence[Row]) -> list[Record]:
    header_list = list(headers)
    records: list[Record] = [list(header_list)]
    for row in rows:
        records.append([row.get(header, "") for header in header_list])
    return records
