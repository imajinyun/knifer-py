from __future__ import annotations

import csv
import dataclasses
import io
from collections.abc import Callable, Sequence
from typing import Any

from kniferpy.verr import ValidationError

Record = list[str]
Row = dict[str, str]

# ── Go-compat type aliases ──────────────────────────────────────────────────

Option = Callable[[Any], None]
ReadOption = Option
WriteOption = Option

# ── Go-compat CSVError ──────────────────────────────────────────────────────


class CSVError(ValidationError):
    """CSV-specific error with optional code and cause (Go compat)."""

    pass


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


# ---------------------------------------------------------------------------
# File-based I/O
# ---------------------------------------------------------------------------


def read(
    path: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> list[Record]:
    """Read CSV records from a file path."""
    with open(path, encoding=encoding) as f:
        return read_string(f.read(), delimiter, trim_leading_space)


def read_maps(
    path: str,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> list[Row]:
    """Read CSV records from a file path and return as dict rows."""
    return records_to_maps(read(path, delimiter, trim_leading_space, encoding))


def write(
    path: str,
    records: Sequence[Sequence[str]],
    delimiter: str = ",",
    use_crlf: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Write CSV records to a file path."""
    content = write_string(records, delimiter, use_crlf)
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(content)


def write_maps(
    path: str,
    headers: Sequence[str],
    rows: Sequence[Row],
    delimiter: str = ",",
    use_crlf: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Write CSV records (as dict rows) to a file path."""
    content = write_string_maps(headers, rows, delimiter, use_crlf)
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(content)


def for_each(
    path: str,
    callback,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Iterate over CSV records from a file, calling callback for each record."""
    records = read(path, delimiter, trim_leading_space, encoding)
    for record in records:
        callback(record)


def for_each_map(
    path: str,
    callback,
    delimiter: str = ",",
    trim_leading_space: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Iterate over CSV records (as dict) from a file, calling callback for each."""
    rows = read_maps(path, delimiter, trim_leading_space, encoding)
    for row in rows:
        callback(row)


# ── Go-compat struct-based CSV functions ────────────────────────────────────


def _struct_fields(obj: Any) -> list[tuple[str, Any]]:
    """Extract fields from a dataclass or plain object, respecting csv tags."""
    fields: list[tuple[str, Any]] = []
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        for f in dataclasses.fields(obj):
            tag = f.metadata.get("csv", f.name) if hasattr(f, "metadata") else f.name
            if tag == "-":
                continue
            fields.append((tag, getattr(obj, f.name)))
    elif hasattr(obj, "__dict__"):
        for k, v in obj.__dict__.items():
            if not k.startswith("_"):
                fields.append((k, v))
    return fields


def structs_to_records(values: Any) -> list[Record]:
    """Convert a list of dataclass/struct objects to CSV records (Go compat)."""
    if not values:
        return []
    fields = _struct_fields(values[0])
    headers = [f[0] for f in fields]
    records: list[Record] = [headers]
    for item in values:
        item_fields = _struct_fields(item)
        record = [
            str(item_fields[i][1]) if i < len(item_fields) else "" for i in range(len(headers))
        ]
        records.append(record)
    return records


def write_structs(writer: Any, values: Any, **opts: Any) -> None:
    """Write struct values as CSV to a writer (Go compat)."""
    records = structs_to_records(values)
    text = write_string(records, **opts)
    writer.write(text)


def write_string_structs(values: Any, **opts: Any) -> str:
    """Write struct values as CSV string (Go compat)."""
    records = structs_to_records(values)
    return write_string(records, **opts)
