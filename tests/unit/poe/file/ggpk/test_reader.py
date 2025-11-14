"""
Unit tests for GGPKReader class.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.records import GGPKError, InvalidTagError


class TestGGPKReader:
    """Test cases for GGPKReader class."""

    def test_init(self) -> None:
        """Test GGPKReader initialization."""
        reader = GGPKReader()
        assert reader is not None

    def test_read_valid_ggpk(self) -> None:
        """Test reading valid GGPK file structure."""
        reader = GGPKReader()
        # Minimal valid GGPK structure
        # GGPK header: magic (4 bytes) + version (4 bytes) + root_offset (8 bytes)
        magic = b"GGPK"
        version = b"\x01\x00\x00\x00"  # Version 1
        root_offset = b"\x00\x00\x00\x00\x00\x00\x00\x00"  # Offset 0
        header = magic + version + root_offset

        # Root directory record
        # Record header: length (4) + name_length (4) + name + entries_count (4)
        record_length = 20  # Minimal record
        name_length = 0
        entries_count = 0
        record = (
            record_length.to_bytes(4, "little")
            + name_length.to_bytes(4, "little")
            + entries_count.to_bytes(4, "little")
            + b"\x00" * 8  # Padding
        )

        file_data = header + record

        with patch.object(reader, "_read_record", return_value=None):
            result = reader.read(file_data)
            assert result is not None

    def test_read_invalid_magic(self) -> None:
        """Test reading file with invalid magic number."""
        reader = GGPKReader()
        invalid_data = b"INVALID" + b"\x00" * 100

        with pytest.raises(GGPKError, match="Invalid magic"):
            reader.read(invalid_data)

    def test_read_empty_file(self) -> None:
        """Test reading empty file."""
        reader = GGPKReader()
        empty_data = b""

        with pytest.raises(GGPKError):
            reader.read(empty_data)

    def test_read_bytesio(self) -> None:
        """Test reading from BytesIO."""
        reader = GGPKReader()
        magic = b"GGPK"
        version = b"\x01\x00\x00\x00"
        root_offset = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        file_data = magic + version + root_offset

        file_io = BytesIO(file_data)

        with patch.object(reader, "_read_record", return_value=None):
            result = reader.read(file_io)
            assert result is not None

    def test_read_record_file(self) -> None:
        """Test reading file record."""
        reader = GGPKReader()
        # File record structure
        record_length = 20
        name_length = 4
        name = b"test"
        data_offset = 100
        data_length = 50

        record_data = (
            record_length.to_bytes(4, "little")
            + name_length.to_bytes(4, "little")
            + name
            + data_offset.to_bytes(8, "little")
            + data_length.to_bytes(4, "little")
        )

        file_raw = b"GGPK" + b"\x01\x00\x00\x00" + b"\x00" * 8 + record_data

        with patch.object(reader, "_read_data", return_value=b"test data"):
            result = reader.read(file_raw)
            # Should not raise error
            assert result is not None

    def test_read_record_directory(self) -> None:
        """Test reading directory record."""
        reader = GGPKReader()
        # Directory record structure
        record_length = 20
        name_length = 4
        name = b"dir"
        entries_count = 0

        record_data = (
            record_length.to_bytes(4, "little")
            + name_length.to_bytes(4, "little")
            + name
            + entries_count.to_bytes(4, "little")
            + b"\x00" * 8
        )

        file_raw = b"GGPK" + b"\x01\x00\x00\x00" + b"\x00" * 8 + record_data

        result = reader.read(file_raw)
        # Should not raise error
        assert result is not None

    def test_read_invalid_tag(self) -> None:
        """Test reading record with invalid tag."""
        reader = GGPKReader()
        # Invalid tag (not FILE, DIRECTORY, GGPK, FREE)
        invalid_tag = b"XXXX"
        record_data = (
            b"\x10\x00\x00\x00"  # length
            + invalid_tag  # invalid tag
            + b"\x00" * 8
        )

        file_raw = b"GGPK" + b"\x01\x00\x00\x00" + b"\x00" * 8 + record_data

        with pytest.raises(InvalidTagError):
            reader.read(file_raw)

