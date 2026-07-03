import os

import pytest

import zipfile
from kniferpy.internal.poix import ErrNoSheet
from kniferpy.vpoi import (
    DEFAULT_SHEET_NAME,
    ErrEmptySheetName,
    ErrInvalidSheetName,
    is_valid_sheet_name,
    read_cells,
    read_rows,
    read_rows_from_reader,
    read_sheet_cells,
    read_sheet_rows,
    sheet_names,
    validate_sheet_name,
    with_read_limit,
    with_read_start_cell,
    write_rows,
    write_rows_to_buffer,
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