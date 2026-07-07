"""Excel read/write helpers (POI - Poor Obfuscation Implementation).

Ports knifer-go's internal/poi with Python-idiomatic mappings:

- Go excelize -> openpyxl
- Go io.Reader -> bytes/file-like objects
- Go functional options -> callable configurators

Errors use kniferpy.verr types with codes knifer.poi.<reason>.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Any, Callable

import openpyxl  # type: ignore[import-untyped]
from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]

from kniferpy.verr import KniferError

# --- constants ----------------------------------------------------------------

DEFAULT_SHEET_NAME = "Sheet1"
MAX_SHEET_NAME_RUNES = 31
_INVALID_SHEET_NAME_CHARS = frozenset(":\\/?*[]")

# --- errors -------------------------------------------------------------------


class ErrNoSheet(KniferError):
    pass


class ErrEmptySheetName(KniferError):
    pass


class ErrInvalidSheetName(KniferError):
    pass


# --- cell types ---------------------------------------------------------------

CellType = str

CellTypeUnset = ""
CellTypeBool = "b"
CellTypeNumber = "n"
CellTypeString = "s"
CellTypeFormula = "str"
CellTypeError = "e"
CellTypeDate = "d"
CellTypeInlineString = "inlineStr"
CellTypeSharedString = "s"


@dataclass
class Cell:
    Value: str = ""
    Type: CellType = CellTypeUnset
    Axis: str = ""
    Row: int = 0
    Col: int = 0


# --- sheet name validation ----------------------------------------------------


def is_valid_sheet_name(sheet: str) -> bool:
    return validate_sheet_name(sheet) is None


def validate_sheet_name(sheet: str) -> Exception | None:
    if not sheet:
        return ErrEmptySheetName("sheet name is empty")
    if len(sheet) > MAX_SHEET_NAME_RUNES:
        return ErrInvalidSheetName("sheet name is invalid")
    if any(c in _INVALID_SHEET_NAME_CHARS for c in sheet):
        return ErrInvalidSheetName("sheet name is invalid")
    return None


# --- read config --------------------------------------------------------------


@dataclass
class _ReadConfig:
    sheet: str = ""
    start_row: int = 1
    start_col: int = 1
    max_rows: int = 0
    max_cols: int = 0
    open_file: Callable[..., Any] | None = None
    open_reader: Callable[..., Any] | None = None


ReadOption = Callable[[_ReadConfig], None]


def with_read_sheet(sheet: str) -> ReadOption:
    def apply(c: _ReadConfig) -> None:
        if sheet:
            c.sheet = sheet

    return apply


def with_read_start_cell(row: int, col: int) -> ReadOption:
    def apply(c: _ReadConfig) -> None:
        if row > 0:
            c.start_row = row
        if col > 0:
            c.start_col = col

    return apply


def with_read_limit(max_rows: int, max_cols: int) -> ReadOption:
    def apply(c: _ReadConfig) -> None:
        if max_rows > 0:
            c.max_rows = max_rows
        if max_cols > 0:
            c.max_cols = max_cols

    return apply


def with_open_file_func(open_file: Callable[..., Any]) -> ReadOption:
    def apply(c: _ReadConfig) -> None:
        if open_file is not None:
            c.open_file = open_file

    return apply


def with_open_reader_func(open_reader: Callable[..., Any]) -> ReadOption:
    def apply(c: _ReadConfig) -> None:
        if open_reader is not None:
            c.open_reader = open_reader

    return apply


def _default_read_config() -> _ReadConfig:
    return _ReadConfig(start_row=1, start_col=1)


def _apply_read_options(opts: list[ReadOption]) -> _ReadConfig:
    cfg = _default_read_config()
    for opt in opts:
        if opt is not None:
            opt(cfg)
    return cfg


# --- write config -------------------------------------------------------------


@dataclass
class _WriteConfig:
    sheet: str = DEFAULT_SHEET_NAME
    start_row: int = 1
    start_col: int = 1
    dir_perm: int = 0o750
    file_perm: int = 0o644
    overwrite: bool = True
    create_parents: bool = True
    new_file: Callable[[], Any] | None = None
    save_as: Callable[..., Any] | None = None
    mkdir_all: Callable[..., Any] | None = None
    stat: Callable[..., Any] | None = None
    chmod: Callable[..., Any] | None = None


WriteOption = Callable[[_WriteConfig], None]


def with_write_sheet(sheet: str) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        if sheet:
            c.sheet = sheet

    return apply


def with_start_cell(row: int, col: int) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        if row > 0:
            c.start_row = row
        if col > 0:
            c.start_col = col

    return apply


def with_dir_perm(perm: int) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        c.dir_perm = perm

    return apply


def with_file_perm(perm: int) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        c.file_perm = perm

    return apply


def with_overwrite(overwrite: bool) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        c.overwrite = overwrite

    return apply


def with_create_parents(create: bool) -> WriteOption:
    def apply(c: _WriteConfig) -> None:
        c.create_parents = create

    return apply


def _default_write_config() -> _WriteConfig:
    return _WriteConfig(
        sheet=DEFAULT_SHEET_NAME,
        start_row=1,
        start_col=1,
        dir_perm=0o750,
        file_perm=0o644,
        overwrite=True,
        create_parents=True,
    )


def _apply_write_options(opts: list[WriteOption]) -> _WriteConfig:
    cfg = _default_write_config()
    for opt in opts:
        if opt is not None:
            opt(cfg)
    return cfg


# --- sheet names --------------------------------------------------------------


def sheet_names(path: str) -> list[str]:
    return sheet_names_with_options(path)


def sheet_names_with_options(path: str, *opts: ReadOption) -> list[str]:
    cfg = _apply_read_options(list(opts))
    wb = _open_workbook(path, cfg)
    return wb.sheetnames  # type: ignore[no-any-return]


# --- read rows ----------------------------------------------------------------


def read_rows(path: str, *opts: ReadOption) -> list[list[str]]:
    cfg = _apply_read_options(list(opts))
    wb = _open_workbook(path, cfg)
    sheet = _resolve_sheet(wb, cfg.sheet)
    return _read_rows_from_sheet(wb, sheet, cfg)


def read_sheet_rows(path: str, sheet: str) -> list[list[str]]:
    return read_sheet_rows_with_options(path, sheet)


def read_sheet_rows_with_options(path: str, sheet: str, *opts: ReadOption) -> list[list[str]]:
    cfg = _apply_read_options(list(opts))
    wb = _open_workbook(path, cfg)
    return _read_rows_from_sheet(wb, sheet, cfg)


def read_rows_from_reader(data: bytes, *opts: ReadOption) -> list[list[str]]:
    cfg = _apply_read_options(list(opts))
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    sheet = _resolve_sheet(wb, cfg.sheet)
    return _read_rows_from_sheet(wb, sheet, cfg)


# --- read cells ---------------------------------------------------------------


def read_cells(path: str, *opts: ReadOption) -> list[list[Cell]]:
    cfg = _apply_read_options(list(opts))
    wb = _open_workbook(path, cfg)
    sheet = _resolve_sheet(wb, cfg.sheet)
    return _read_cells_from_sheet(wb, sheet, cfg)


def read_sheet_cells(path: str, sheet: str) -> list[list[Cell]]:
    return read_sheet_cells_with_options(path, sheet)


def read_sheet_cells_with_options(path: str, sheet: str, *opts: ReadOption) -> list[list[Cell]]:
    cfg = _apply_read_options(list(opts))
    wb = _open_workbook(path, cfg)
    return _read_cells_from_sheet(wb, sheet, cfg)


def read_cells_from_reader(data: bytes, *opts: ReadOption) -> list[list[Cell]]:
    cfg = _apply_read_options(list(opts))
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    sheet = _resolve_sheet(wb, cfg.sheet)
    return _read_cells_from_sheet(wb, sheet, cfg)


# --- write rows ---------------------------------------------------------------


def write_rows(path: str, rows: list[list[str]], *opts: WriteOption) -> None:
    cfg = _apply_write_options(list(opts))
    _write_rows_impl(path, rows, cfg)


def write_sheet_rows(path: str, sheet: str, rows: list[list[str]], *opts: WriteOption) -> None:
    all_opts = [_with_write_sheet(sheet)] + list(opts)
    cfg = _apply_write_options(all_opts)
    _write_rows_impl(path, rows, cfg)


def write_any_rows(path: str, rows: list[list[Any]], *opts: WriteOption) -> None:
    cfg = _apply_write_options(list(opts))
    _write_any_rows_impl(path, rows, cfg)


def write_sheet_any_rows(path: str, sheet: str, rows: list[list[Any]], *opts: WriteOption) -> None:
    all_opts = [_with_write_sheet(sheet)] + list(opts)
    cfg = _apply_write_options(all_opts)
    _write_any_rows_impl(path, rows, cfg)


def write_sheets(path: str, sheets: dict[str, list[list[str]]], *opts: WriteOption) -> None:
    cfg = _apply_write_options(list(opts))
    wb = _new_workbook(cfg)
    first = True
    for sheet_name in sorted(sheets.keys()):
        rows = sheets[sheet_name]
        if first:
            ws = wb.active
            ws.title = sheet_name
            first = False
        else:
            ws = wb.create_sheet(title=sheet_name)
        _set_rows(ws, rows, cfg.start_row, cfg.start_col)
    _save_workbook(wb, path, cfg)


def write_rows_to_buffer(sheet: str, rows: list[list[str]], *opts: WriteOption) -> bytes:
    all_opts = [_with_write_sheet(sheet)] + list(opts)
    cfg = _apply_write_options(all_opts)
    wb = _new_workbook(cfg)
    ws = wb.active
    ws.title = sheet
    _set_rows(ws, rows, cfg.start_row, cfg.start_col)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def write_any_rows_to_buffer(sheet: str, rows: list[list[Any]], *opts: WriteOption) -> bytes:
    all_opts = [_with_write_sheet(sheet)] + list(opts)
    cfg = _apply_write_options(all_opts)
    wb = _new_workbook(cfg)
    ws = wb.active
    ws.title = sheet
    _set_any_rows(ws, rows, cfg.start_row, cfg.start_col)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --- internal helpers ---------------------------------------------------------


def _open_workbook(path: str, cfg: _ReadConfig) -> Any:
    if cfg.open_file is not None:
        return cfg.open_file(path)
    return openpyxl.load_workbook(path, read_only=True, data_only=True)


def _resolve_sheet(wb: Any, sheet: str) -> str:
    if sheet:
        return sheet
    if not wb.sheetnames:
        raise ErrNoSheet("workbook has no sheet")
    return wb.sheetnames[0]  # type: ignore[no-any-return]


def _read_rows_from_sheet(wb: Any, sheet: str, cfg: _ReadConfig) -> list[list[str]]:
    err = validate_sheet_name(sheet)
    if err is not None:
        raise err
    ws = wb[sheet]
    rows = [[str(cell.value) if cell.value is not None else "" for cell in row] for row in ws.rows]
    return _limit_rows(rows, cfg)


def _read_cells_from_sheet(wb: Any, sheet: str, cfg: _ReadConfig) -> list[list[Cell]]:
    err = validate_sheet_name(sheet)
    if err is not None:
        raise err
    ws = wb[sheet]
    cells: list[list[Cell]] = []
    for row_idx, row in enumerate(ws.iter_rows(), start=1):
        row_cells: list[Cell] = []
        for col_idx, cell in enumerate(row, start=1):
            column_letter = get_column_letter(col_idx)
            axis = f"{column_letter}{row_idx}"
            row_cells.append(
                Cell(
                    Value=str(cell.value) if cell.value is not None else "",
                    Type=_map_cell_type(cell.data_type),
                    Axis=axis,
                    Row=row_idx,
                    Col=col_idx,
                )
            )
        cells.append(row_cells)
    return _limit_cells(cells, cfg)


def _map_cell_type(data_type: str) -> CellType:
    if data_type == "n":
        return CellTypeNumber
    if data_type == "s":
        return CellTypeString
    if data_type == "b":
        return CellTypeBool
    if data_type == "e":
        return CellTypeError
    return CellTypeUnset


def _limit_rows(rows: list[list[str]], cfg: _ReadConfig) -> list[list[str]]:
    if cfg.start_row <= 1 and cfg.start_col <= 1 and cfg.max_rows <= 0 and cfg.max_cols <= 0:
        return rows

    start_row = max(cfg.start_row, 1)
    start_col = max(cfg.start_col, 1)

    if start_row > len(rows):
        return []

    out = rows[start_row - 1 :]
    if cfg.max_rows > 0 and cfg.max_rows < len(out):
        out = out[: cfg.max_rows]

    result: list[list[str]] = []
    for row in out:
        if start_col - 1 >= len(row):
            result.append([])
            continue
        cell_values = row[start_col - 1 :]
        if cfg.max_cols > 0 and cfg.max_cols < len(cell_values):
            cell_values = cell_values[: cfg.max_cols]
        result.append(cell_values)
    return result


def _limit_cells(cells: list[list[Cell]], cfg: _ReadConfig) -> list[list[Cell]]:
    if cfg.start_row <= 1 and cfg.start_col <= 1 and cfg.max_rows <= 0 and cfg.max_cols <= 0:
        return cells

    start_row = max(cfg.start_row, 1)
    start_col = max(cfg.start_col, 1)

    if start_row > len(cells):
        return []

    out = cells[start_row - 1 :]
    if cfg.max_rows > 0 and cfg.max_rows < len(out):
        out = out[: cfg.max_rows]

    result: list[list[Cell]] = []
    for row in out:
        if start_col - 1 >= len(row):
            result.append([])
            continue
        cell_values = row[start_col - 1 :]
        if cfg.max_cols > 0 and cfg.max_cols < len(cell_values):
            cell_values = cell_values[: cfg.max_cols]
        result.append(cell_values)
    return result


def _with_write_sheet(sheet: str) -> WriteOption:
    return with_write_sheet(sheet)


def _new_workbook(cfg: _WriteConfig) -> Any:
    if cfg.new_file is not None:
        return cfg.new_file()
    return openpyxl.Workbook()


def _write_rows_impl(path: str, rows: list[list[str]], cfg: _WriteConfig) -> None:
    err = validate_sheet_name(cfg.sheet)
    if err is not None:
        raise err
    wb = _new_workbook(cfg)
    ws = wb.active
    ws.title = cfg.sheet
    _set_rows(ws, rows, cfg.start_row, cfg.start_col)
    _save_workbook(wb, path, cfg)


def _write_any_rows_impl(path: str, rows: list[list[Any]], cfg: _WriteConfig) -> None:
    err = validate_sheet_name(cfg.sheet)
    if err is not None:
        raise err
    wb = _new_workbook(cfg)
    ws = wb.active
    ws.title = cfg.sheet
    _set_any_rows(ws, rows, cfg.start_row, cfg.start_col)
    _save_workbook(wb, path, cfg)


def _set_rows(ws: Any, rows: list[list[str]], start_row: int, start_col: int) -> None:
    if start_row <= 0:
        start_row = 1
    if start_col <= 0:
        start_col = 1
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            ws.cell(row=start_row + row_idx, column=start_col + col_idx, value=value)


def _set_any_rows(ws: Any, rows: list[list[Any]], start_row: int, start_col: int) -> None:
    if start_row <= 0:
        start_row = 1
    if start_col <= 0:
        start_col = 1
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            ws.cell(row=start_row + row_idx, column=start_col + col_idx, value=value)


def _save_workbook(wb: Any, path: str, cfg: _WriteConfig) -> None:
    if not cfg.overwrite and os.path.exists(path):
        raise ErrInvalidSheetName("file already exists")
    if cfg.create_parents:
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, cfg.dir_perm, exist_ok=True)
    wb.save(path)
    if cfg.file_perm != 0:
        os.chmod(path, cfg.file_perm)
