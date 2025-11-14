"""
Unit tests for GGPKRecordManager class.
"""

import pytest

from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
from PyPoE.poe.file.ggpk.records import FileRecord, DirectoryRecord, GGPKRecord


class TestGGPKRecordManager:
    """Test cases for GGPKRecordManager class."""

    def test_init(self) -> None:
        """Test GGPKRecordManager initialization."""
        manager = GGPKRecordManager()
        assert len(manager) == 0
        assert manager.records == []

    def test_add_record(self) -> None:
        """Test adding a record."""
        manager = GGPKRecordManager()
        record = FileRecord(
            name="test.dat",
            data_offset=0,
            data_length=100,
        )
        manager.add_record(record)
        assert len(manager) == 1
        assert record in manager.records

    def test_add_multiple_records(self) -> None:
        """Test adding multiple records."""
        manager = GGPKRecordManager()
        record1 = FileRecord(name="file1.dat", data_offset=0, data_length=50)
        record2 = FileRecord(name="file2.dat", data_offset=50, data_length=50)
        manager.add_record(record1)
        manager.add_record(record2)
        assert len(manager) == 2

    def test_get_record_by_name(self) -> None:
        """Test getting record by name."""
        manager = GGPKRecordManager()
        record = FileRecord(name="test.dat", data_offset=0, data_length=100)
        manager.add_record(record)
        found = manager.get_record_by_name("test.dat")
        assert found == record

    def test_get_record_by_name_not_found(self) -> None:
        """Test getting non-existent record."""
        manager = GGPKRecordManager()
        found = manager.get_record_by_name("nonexistent.dat")
        assert found is None

    def test_get_records_by_type(self) -> None:
        """Test getting records by type."""
        manager = GGPKRecordManager()
        file_record = FileRecord(name="file.dat", data_offset=0, data_length=100)
        dir_record = DirectoryRecord(name="dir", entries=[])
        manager.add_record(file_record)
        manager.add_record(dir_record)

        file_records = manager.get_records_by_type(FileRecord)
        assert len(file_records) == 1
        assert file_records[0] == file_record

    def test_clear(self) -> None:
        """Test clearing all records."""
        manager = GGPKRecordManager()
        record = FileRecord(name="test.dat", data_offset=0, data_length=100)
        manager.add_record(record)
        assert len(manager) == 1

        manager.clear()
        assert len(manager) == 0
        assert manager.records == []

    def test_iter(self) -> None:
        """Test iterating over records."""
        manager = GGPKRecordManager()
        record1 = FileRecord(name="file1.dat", data_offset=0, data_length=50)
        record2 = FileRecord(name="file2.dat", data_offset=50, data_length=50)
        manager.add_record(record1)
        manager.add_record(record2)

        records = list(manager)
        assert len(records) == 2
        assert record1 in records
        assert record2 in records

    def test_len_empty(self) -> None:
        """Test length of empty manager."""
        manager = GGPKRecordManager()
        assert len(manager) == 0

    def test_len_with_records(self) -> None:
        """Test length with records."""
        manager = GGPKRecordManager()
        for i in range(5):
            record = FileRecord(name=f"file{i}.dat", data_offset=i * 100, data_length=100)
            manager.add_record(record)
        assert len(manager) == 5

