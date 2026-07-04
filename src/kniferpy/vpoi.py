"""Excel read/write helpers (POI facade).

Thin facade over kniferpy.internal.poix, porting knifer-go's vpoi surface.

Provides Excel read/write helpers with configurable sheet selection,
row/column limiting, and workbook factory injection.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal.poix import (
    DEFAULT_SHEET_NAME,
    Cell,
    CellType,
    CellTypeBool,
    CellTypeDate,
    CellTypeError,
    CellTypeFormula,
    CellTypeInlineString,
    CellTypeNumber,
    CellTypeSharedString,
    CellTypeString,
    CellTypeUnset,
    ErrEmptySheetName,
    ErrInvalidSheetName,
    ErrNoSheet,
    ReadOption,
    WriteOption,
    is_valid_sheet_name,
    read_cells,
    read_cells_from_reader,
    read_rows,
    read_rows_from_reader,
    read_sheet_cells,
    read_sheet_cells_with_options,
    read_sheet_rows,
    read_sheet_rows_with_options,
    sheet_names,
    sheet_names_with_options,
    validate_sheet_name,
    with_create_parents,
    with_dir_perm,
    with_file_perm,
    with_open_file_func,
    with_open_reader_func,
    with_overwrite,
    with_read_limit,
    with_read_sheet,
    with_read_start_cell,
    with_start_cell,
    with_write_sheet,
    write_any_rows,
    write_any_rows_to_buffer,
    write_rows,
    write_rows_to_buffer,
    write_sheet_any_rows,
    write_sheet_rows,
    write_sheets,
)

# ── Go-compat factory function type aliases ─────────────────────────────────────

OpenFileFunc = Callable[[str], Any]
OpenReaderFunc = Callable[[bytes], Any]
NewFileFunc = Callable[[], Any]
SaveAsFunc = Callable[[Any, str], None]

__all__ = [
    "DEFAULT_SHEET_NAME",
    "Cell",
    "CellType",
    "CellTypeBool",
    "CellTypeDate",
    "CellTypeError",
    "CellTypeFormula",
    "CellTypeInlineString",
    "CellTypeNumber",
    "CellTypeSharedString",
    "CellTypeString",
    "CellTypeUnset",
    "ErrEmptySheetName",
    "ErrInvalidSheetName",
    "ErrNoSheet",
    "ReadOption",
    "WriteOption",
    "is_valid_sheet_name",
    "read_cells",
    "read_cells_from_reader",
    "read_rows",
    "read_rows_from_reader",
    "read_sheet_cells",
    "read_sheet_cells_with_options",
    "read_sheet_rows",
    "read_sheet_rows_with_options",
    "sheet_names",
    "sheet_names_with_options",
    "validate_sheet_name",
    "with_create_parents",
    "with_dir_perm",
    "with_file_perm",
    "with_open_file_func",
    "with_open_reader_func",
    "with_overwrite",
    "with_read_limit",
    "with_read_sheet",
    "with_read_start_cell",
    "with_start_cell",
    "with_write_sheet",
    "write_any_rows",
    "write_any_rows_to_buffer",
    "write_rows",
    "write_rows_to_buffer",
    "write_sheet_any_rows",
    "write_sheet_rows",
    "write_sheets",
    # Go-compat factory function types
    "OpenFileFunc",
    "OpenReaderFunc",
    "NewFileFunc",
    "SaveAsFunc",
]