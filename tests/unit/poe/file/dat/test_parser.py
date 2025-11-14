"""
Unit tests for DatParser class.
"""

import struct
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from PyPoE.poe.file.dat.caster import CastTypes, DatCaster
from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER, DatParser
from PyPoE.poe.file.specification.errors import SpecificationError


class TestDatParser:
    """Test cases for DatParser class."""

    def test_init(self) -> None:
        """Test DatParser initialization."""
        spec = MagicMock()
        spec.columns_data = ["id", "name"]
        spec.fields = {
            "id": MagicMock(type="int"),
            "name": MagicMock(type="string"),
        }
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)
        assert parser.file_name == "test.dat"
        assert parser.specification == spec
        assert parser.caster == caster
        assert parser.x64 is False
        assert len(parser.table_columns) == 2

    def test_init_x64(self) -> None:
        """Test DatParser initialization with x64 mode."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster(x64=True)
        parser = DatParser("test.dat", spec, caster, x64=True)
        assert parser.x64 is True

    def test_parse_file_valid(self) -> None:
        """Test parsing valid DAT file."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        # Create minimal valid DAT file
        table_rows = 2
        table_data = struct.pack("<I", table_rows)  # 4 bytes for row count
        table_data += struct.pack("<i", 1)  # First row: id=1
        table_data += struct.pack("<i", 2)  # Second row: id=2
        magic = DAT_FILE_MAGIC_NUMBER
        data_section = b"data section content"

        file_raw = table_data + magic + data_section

        file_raw_result, file_length, data_offset, table_rows_result, table_record_length = (
            parser.parse_file(file_raw)
        )

        assert file_raw_result == file_raw
        assert file_length == len(file_raw)
        assert data_offset == len(table_data)
        assert table_rows_result == table_rows
        assert table_record_length == 4  # int size

    def test_parse_file_bytesio(self) -> None:
        """Test parsing DAT file from BytesIO."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        table_rows = 1
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<i", 1)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        file_io = BytesIO(file_raw)
        result = parser.parse_file(file_io)

        assert result[0] == file_raw
        assert result[2] == len(table_data)

    def test_parse_file_invalid_type(self) -> None:
        """Test parsing with invalid input type."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        with pytest.raises(TypeError, match="Raw must be bytes or BytesIO"):
            parser.parse_file("invalid")  # type: ignore[arg-type]

    def test_parse_file_no_magic(self) -> None:
        """Test parsing file without magic number."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        file_raw = b"invalid file content"

        with pytest.raises(ValueError, match="Did not find data magic number"):
            parser.parse_file(file_raw)

    def test_parse_file_empty(self) -> None:
        """Test parsing empty DAT file."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        table_rows = 0
        table_data = struct.pack("<I", table_rows)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic

        result = parser.parse_file(file_raw)
        assert result[3] == 0  # table_rows
        assert result[4] == 0  # table_record_length

    def test_parse_file_size_mismatch(self) -> None:
        """Test parsing file with size mismatch."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        # Create file with wrong row size (8 bytes instead of 4)
        table_rows = 1
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<ii", 1, 2)  # 8 bytes instead of 4
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic

        with pytest.raises(SpecificationError, match="row size"):
            parser.parse_file(file_raw)

    def test_parse_row_empty(self) -> None:
        """Test parsing empty row."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        file_raw = b""
        parent = MagicMock()
        row = parser.parse_row(file_raw, 0, 0, 0, parent)

        assert row.parent == parent
        assert row.rowid == 0
        assert len(row) == 0

    def test_parse_row_single_int(self) -> None:
        """Test parsing row with single int column."""
        spec = MagicMock()
        spec.columns_data = ["id"]
        spec.fields = {"id": MagicMock(type="int")}
        caster = DatCaster()
        parser = DatParser("test.dat", spec, caster)

        table_data = struct.pack("<I", 1)  # row count
        table_data += struct.pack("<i", 42)  # id = 42
        magic = DAT_FILE_MAGIC_NUMBER
        data_section = b"data"
        file_raw = table_data + magic + data_section

        parent = MagicMock()
        row = parser.parse_row(file_raw, len(table_data), 0, 4, parent)

        assert row.parent == parent
        assert row.rowid == 0
        assert len(row) == 1

