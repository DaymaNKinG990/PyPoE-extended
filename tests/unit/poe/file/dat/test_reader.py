"""
Unit tests for DatReader class.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from PyPoE.poe.file.dat.caster import DatCaster
from PyPoE.poe.file.dat.reader import DatReader
from PyPoE.poe.file.dat.record import DatRecord


class TestDatReader:
    """Test cases for DatReader class."""

    def test_init(self) -> None:
        """Test DatReader initialization."""
        # DatReader expects specification to be a dict with file_name as key
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        # DatReader doesn't take caster as parameter, it creates it internally
        reader = DatReader("test.dat", specification=spec)
        assert reader.file_name == "test.dat"
        assert reader.specification == spec_obj
        assert reader.x64 is False

    def test_init_x64(self) -> None:
        """Test DatReader initialization with x64 mode."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec, x64=True)
        assert reader.x64 is True

    def test_table_columns_property(self) -> None:
        """Test table_columns property."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id", "name"]
        spec_obj.fields = {
            "id": MagicMock(type="int"),
            "name": MagicMock(type="int"),  # Use int instead of string/ref|string
        }
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)
        assert "id" in reader.table_columns
        assert "name" in reader.table_columns

    def test_read_empty_file(self) -> None:
        """Test reading empty DAT file."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        # Empty file with cast_size > 0 will fail validation
        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        file_raw = struct.pack("<I", 0) + DAT_FILE_MAGIC_NUMBER
        # Empty files with non-zero cast_size will raise SpecificationError
        with pytest.raises(Exception):  # SpecificationError or similar
            reader.read(file_raw)

    def test_read_single_row(self) -> None:
        """Test reading DAT file with single row."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 1
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<i", 42)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        reader.read(file_raw)

        assert len(reader.table_data) == 1
        assert isinstance(reader.table_data[0], DatRecord)

    def test_read_bytesio(self) -> None:
        """Test reading DAT file from BytesIO."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 1
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<i", 42)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        file_io = BytesIO(file_raw)
        reader.read(file_io)

        assert len(reader.table_data) == 1

    def test_get_row_by_index(self) -> None:
        """Test getting row by index."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 2
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<i", 1)
        table_data += struct.pack("<i", 2)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        reader.read(file_raw)

        row0 = reader[0]
        row1 = reader[1]

        assert isinstance(row0, DatRecord)
        assert isinstance(row1, DatRecord)
        assert row0.rowid == 0
        assert row1.rowid == 1

    def test_get_row_by_index_out_of_range(self) -> None:
        """Test getting row with out of range index."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 1
        table_data = struct.pack("<I", table_rows)
        table_data += struct.pack("<i", 1)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        reader.read(file_raw)

        with pytest.raises(IndexError):
            _ = reader[10]

    def test_iter_rows(self) -> None:
        """Test iterating over rows."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 3
        table_data = struct.pack("<I", table_rows)
        for i in range(3):
            table_data += struct.pack("<i", i + 1)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        reader.read(file_raw)

        rows = list(reader)
        assert len(rows) == 3
        assert all(isinstance(row, DatRecord) for row in rows)

    def test_len(self) -> None:
        """Test len() of DatReader."""
        spec_obj = MagicMock()
        spec_obj.columns_data = ["id"]
        spec_obj.fields = {"id": MagicMock(type="int")}
        spec_obj.columns_unique = {}
        spec_obj.columns = []
        spec_obj.columns_all = []
        spec_obj.columns_zip = []
        spec = {"test.dat": spec_obj}
        reader = DatReader("test.dat", specification=spec)

        import struct

        from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER

        table_rows = 5
        table_data = struct.pack("<I", table_rows)
        for i in range(5):
            table_data += struct.pack("<i", i + 1)
        magic = DAT_FILE_MAGIC_NUMBER
        file_raw = table_data + magic + b"data"

        reader.read(file_raw)

        # DatReader doesn't have __len__, use len(table_data) instead
        assert len(reader.table_data) == 5

