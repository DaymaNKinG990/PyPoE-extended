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
        assert len(manager.get_records()) == 0

    def test_add_record(self) -> None:
        """Test adding a record."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record = FileRecord(container=container, length=100, offset=0)
        record.name = "test.dat"
        manager.add_record(0, record)
        assert len(manager) == 1
        assert manager.get_record(0) == record

    def test_add_multiple_records(self) -> None:
        """Test adding multiple records."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record1 = FileRecord(container=container, length=50, offset=0)
        record1.name = "file1.dat"
        record2 = FileRecord(container=container, length=50, offset=50)
        record2.name = "file2.dat"
        manager.add_record(0, record1)
        manager.add_record(50, record2)
        assert len(manager) == 2

    def test_get_record(self) -> None:
        """Test getting record by offset."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record = FileRecord(container=container, length=100, offset=0)
        record.name = "test.dat"
        manager.add_record(0, record)
        found = manager.get_record(0)
        assert found == record

    def test_get_record_not_found(self) -> None:
        """Test getting non-existent record."""
        manager = GGPKRecordManager()
        found = manager.get_record(999)
        assert found is None

    def test_get_records(self) -> None:
        """Test getting all records."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record1 = FileRecord(container=container, length=100, offset=0)
        record1.name = "file1.dat"
        record2 = FileRecord(container=container, length=100, offset=100)
        record2.name = "file2.dat"
        manager.add_record(0, record1)
        manager.add_record(100, record2)

        records = manager.get_records()
        assert len(records) == 2
        assert 0 in records
        assert 100 in records

    def test_clear(self) -> None:
        """Test clearing all records."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record = FileRecord(container=container, length=100, offset=0)
        record.name = "test.dat"
        manager.add_record(0, record)
        assert len(manager) == 1

        manager.clear()
        assert len(manager) == 0
        assert len(manager.get_records()) == 0

    def test_iter(self) -> None:
        """Test iterating over records."""
        manager = GGPKRecordManager()
        container = MagicMock()
        record1 = FileRecord(container=container, length=50, offset=0)
        record1.name = "file1.dat"
        record2 = FileRecord(container=container, length=50, offset=50)
        record2.name = "file2.dat"
        manager.add_record(0, record1)
        manager.add_record(50, record2)

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
        container = MagicMock()
        for i in range(5):
            record = FileRecord(container=container, length=100, offset=i * 100)
            record.name = f"file{i}.dat"
            manager.add_record(i * 100, record)
        assert len(manager) == 5

