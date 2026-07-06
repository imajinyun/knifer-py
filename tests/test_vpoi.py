import os
import stat
import zipfile

import pytest

from kniferpy.internal import poix
from kniferpy.internal.poix import ErrNoSheet
from kniferpy.vpoi import (
    DEFAULT_SHEET_NAME,
    ErrEmptySheetName,
    ErrInvalidSheetName,
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

# --- sheet name validation ----------------------------------------------------


def test_is_valid_sheet_name_valid():
    assert is_valid_sheet_name("Sheet1")
    assert is_valid_sheet_name("My Sheet")
    assert is_valid_sheet_name("A" * 31)  # exactly 31 chars is OK
    assert is_valid_sheet_name("A" * 32) is False  # too long


def test_is_valid_sheet_name_invalid_chars():
    assert not is_valid_sheet_name("Sheet:1")
    assert not is_valid_sheet_name("Sheet\\1")
    assert not is_valid_sheet_name("Sheet/1")
    assert not is_valid_sheet_name("Sheet?1")
    assert not is_valid_sheet_name("Sheet*1")
    assert not is_valid_sheet_name("Sheet[1")
    assert not is_valid_sheet_name("Sheet]1")


def test_validate_sheet_name_empty():
    err = validate_sheet_name("")
    assert isinstance(err, ErrEmptySheetName)


def test_validate_sheet_name_invalid_length():
    err = validate_sheet_name("A" * 32)
    assert isinstance(err, ErrInvalidSheetName)


# --- sheet names -------------------------------------------------------------


def test_sheet_names(tmp_path):
    wb_path = str(tmp_path / "test.xlsx")
    with open(wb_path, "wb") as f:
        f.write(b"")
    # openpyxl can read empty files? no, will error
    with pytest.raises(zipfile.BadZipFile):
        sheet_names(wb_path)


# --- read rows --------------------------------------------------------------


def test_read_rows(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_rows(str(wb_path), [["a", "b", "c"], ["1", "2", "3"]])
    rows = read_rows(str(wb_path))
    assert rows == [["a", "b", "c"], ["1", "2", "3"]]


def test_read_sheet_rows(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_sheet_rows(str(wb_path), "Custom", [["a", "b"], ["1", "2"]])
    rows = read_sheet_rows(str(wb_path), "Custom")
    assert rows == [["a", "b"], ["1", "2"]]


def test_read_rows_with_limit(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_rows(str(wb_path), [[str(i)] for i in range(10)])
    rows = read_rows(str(wb_path), with_read_limit(5, 1))
    assert len(rows) == 5
    assert all(len(row) == 1 for row in rows)


def test_read_rows_with_start_cell(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_rows(str(wb_path), [
        ["", "", "", "", "", ""],
        ["", "", "A", "B", "C"],
        ["", "", "1", "2", "3"],
    ])
    rows = read_rows(str(wb_path), with_read_start_cell(2, 3))
    # The first row should contain A, B, C and the second 1, 2, 3
    # openpyxl may include trailing empty cells
    assert rows[0][0:3] == ["A", "B", "C"]
    assert rows[1][0:3] == ["1", "2", "3"]


# --- read cells -------------------------------------------------------------


def test_read_cells(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_rows(str(wb_path), [["a", "1"], ["b", "2"]])
    cells = read_cells(str(wb_path))
    assert len(cells) == 2
    assert len(cells[0]) == 2
    assert cells[0][0].Value == "a"
    assert cells[0][1].Value == "1"


def test_read_sheet_cells(tmp_path):
    wb_path = tmp_path / "test.xlsx"
    write_sheet_rows(str(wb_path), "Custom", [["hello", "world"]])
    cells = read_sheet_cells(str(wb_path), "Custom")
    assert len(cells) == 1
    assert cells[0][0].Value == "hello"
    assert cells[0][0].Row == 1
    assert cells[0][0].Col == 1


def test_read_cells_from_bytes():
    buf = write_rows_to_buffer("Sheet", [["a", "b"], ["1", "2"]])
    rows = read_rows_from_reader(buf)
    assert rows == [["a", "b"], ["1", "2"]]


# --- write rows -------------------------------------------------------------


def test_write_rows(tmp_path):
    wb_path = str(tmp_path / "output.xlsx")
    data = [["Name", "Value"], ["a", "1"]]
    write_rows(wb_path, data)
    assert os.path.exists(wb_path)
    read_back = read_rows(wb_path)
    assert read_back == data


def test_write_sheet_rows(tmp_path):
    wb_path = str(tmp_path / "output.xlsx")
    data = [["a", "b"], ["1", "2"]]
    write_sheet_rows(wb_path, "Custom", data)
    read_back = read_sheet_rows(wb_path, "Custom")
    assert read_back == data


def test_write_multiple_sheets(tmp_path):
    wb_path = str(tmp_path / "multi.xlsx")
    data = {
        "Sheet1": [["a", "b"], ["1", "2"]],
        "Sheet2": [["x", "y"], ["3", "4"]],
    }
    write_sheets(wb_path, data)
    assert os.path.exists(wb_path)
    names = sheet_names(wb_path)
    assert sorted(names) == sorted(["Sheet1", "Sheet2"])


def test_write_rows_to_buffer():
    buf = write_rows_to_buffer("Sheet1", [["hello", "world"]])
    assert len(buf) > 0
    assert isinstance(buf, bytes)


def test_default_sheet_name():
    buf = write_rows_to_buffer(DEFAULT_SHEET_NAME, [["a"]])
    rows = read_rows_from_reader(buf)
    assert rows == [["a"]]


# --- errors ----------------------------------------------------------------


def test_read_empty_sheet_name(tmp_path):
    wb_path = str(tmp_path / "test.xlsx")
    write_rows(wb_path, [["a"]])
    with pytest.raises(ErrEmptySheetName):
        read_sheet_rows(wb_path, "")


def test_read_invalid_sheet_name(tmp_path):
    wb_path = str(tmp_path / "test.xlsx")
    write_rows(wb_path, [["a"]])
    with pytest.raises(ErrInvalidSheetName):
        read_sheet_rows(wb_path, "bad:name")


# --- integration tests -------------------------------------------------------


def test_integration_read_write_roundtrip(tmp_path):
    original = [
        ["Name", "Age", "Active"],
        ["Alice", "30", "True"],
        ["Bob", "25", "False"],
    ]
    wb_path = str(tmp_path / "roundtrip.xlsx")
    write_rows(wb_path, original)
    result = read_rows(wb_path)
    assert result == original


def test_integration_read_write_multiple_sheets(tmp_path):
    data = {
        "Users": [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]],
        "Products": [["SKU", "Price"], ["ABC", "10.0"], ["XYZ", "20.0"]],
    }
    wb_path = str(tmp_path / "multi.xlsx")
    write_sheets(wb_path, data)
    assert sorted(sheet_names(wb_path)) == sorted(data.keys())
    for sheet_name in data:
        rows = read_sheet_rows(wb_path, sheet_name)
        assert rows == data[sheet_name]


def test_read_options_sheet_limit_and_custom_open_file(tmp_path):
    wb_path = str(tmp_path / "custom.xlsx")
    write_sheets(wb_path, {"A": [["skip"]], "B": [["h1", "h2"], ["v1", "v2"]]})

    opened: list[str] = []

    def open_file(path: str):
        opened.append(path)
        return poix.openpyxl.load_workbook(path, read_only=True, data_only=True)

    assert sheet_names_with_options(wb_path, with_open_file_func(open_file)) == ["A", "B"]
    rows = read_rows(
        wb_path,
        with_read_sheet("B"),
        with_read_start_cell(2, 2),
        with_read_limit(10, 1),
        with_open_file_func(open_file),
    )

    assert opened == [wb_path, wb_path]
    assert rows == [["v2"]]


def test_read_cells_from_reader_and_cell_type_mapping() -> None:
    buf = write_any_rows_to_buffer("Sheet", [[True, 3.14, "text"]])
    cells = read_cells_from_reader(buf)

    assert [cell.Type for cell in cells[0]] == [
        poix.CellTypeBool,
        poix.CellTypeNumber,
        poix.CellTypeString,
    ]
    assert cells[0][0].Axis == "A1"
    assert cells[0][1].Value == "3.14"
    assert poix._map_cell_type("e") == poix.CellTypeError
    assert poix._map_cell_type("unknown") == poix.CellTypeUnset


def test_read_cells_limits_and_empty_rows(tmp_path):
    wb_path = str(tmp_path / "cells.xlsx")
    write_rows(
        wb_path,
        [
            ["a", "b"],
            ["c", "d"],
        ],
    )

    assert read_sheet_cells_with_options(wb_path, "Sheet1", with_read_start_cell(9, 9)) == []
    assert read_sheet_rows_with_options(wb_path, "Sheet1", with_read_start_cell(1, 9)) == [
        [],
        [],
    ]


def test_write_any_rows_sheet_and_buffer(tmp_path):
    wb_path = str(tmp_path / "any.xlsx")
    write_any_rows(wb_path, [["name", "active", "score"], ["alice", True, 3.5]])
    assert read_rows(wb_path) == [["name", "active", "score"], ["alice", "True", "3.5"]]

    sheet_path = str(tmp_path / "sheet-any.xlsx")
    write_sheet_any_rows(sheet_path, "Typed", [[1, False]])
    assert read_sheet_rows(sheet_path, "Typed") == [["1", "False"]]

    buf = write_any_rows_to_buffer("Any", [[1, True]])
    assert read_rows_from_reader(buf) == [["1", "True"]]


def test_write_options_permissions_overwrite_and_create_parent(tmp_path):
    wb_path = tmp_path / "perms" / "out.xlsx"
    write_rows(
        str(wb_path),
        [["a"]],
        with_dir_perm(0o755),
        with_file_perm(0o600),
        with_create_parents(True),
    )
    assert wb_path.exists()
    assert stat.S_IMODE(wb_path.stat().st_mode) == 0o600

    with pytest.raises(ErrInvalidSheetName):
        write_rows(str(wb_path), [["b"]], with_overwrite(False))

    missing_parent = tmp_path / "missing" / "out.xlsx"
    with pytest.raises(FileNotFoundError):
        write_rows(str(missing_parent), [["a"]], with_create_parents(False))


def test_invalid_write_sheet_and_start_cell_defaults(tmp_path):
    with pytest.raises(ErrInvalidSheetName):
        write_rows(str(tmp_path / "bad.xlsx"), [["a"]], with_write_sheet("bad:name"))

    wb_path = str(tmp_path / "start-default.xlsx")
    write_rows(wb_path, [["a"]], with_start_cell(0, 0))
    assert read_rows(wb_path) == [["a"]]


def test_internal_config_helpers_and_custom_workbook(tmp_path):
    read_cfg = poix._apply_read_options(
        [
            with_read_sheet("A"),
            with_read_start_cell(-1, -1),
            with_read_limit(-1, -1),
            with_open_file_func(None),  # type: ignore[arg-type]
            with_open_reader_func(None),  # type: ignore[arg-type]
            None,  # type: ignore[list-item]
        ]
    )
    assert read_cfg.sheet == "A"
    assert read_cfg.start_row == 1
    assert read_cfg.start_col == 1
    assert read_cfg.max_rows == 0
    assert read_cfg.max_cols == 0

    calls: list[str] = []
    wb = poix.openpyxl.Workbook()

    def new_file():
        calls.append("new")
        return wb

    cfg = poix._apply_write_options([None])  # type: ignore[list-item]
    cfg.new_file = new_file
    assert poix._new_workbook(cfg) is wb
    assert calls == ["new"]


def test_resolve_sheet_no_sheet_error() -> None:
    class EmptyWorkbook:
        sheetnames: list[str] = []

    with pytest.raises(ErrNoSheet):
        poix._resolve_sheet(EmptyWorkbook(), "")
