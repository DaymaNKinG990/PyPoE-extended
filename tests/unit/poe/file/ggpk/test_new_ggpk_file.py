"""Tests for new refactored GGPKFile."""

import pytest

from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
from PyPoE.poe.file.ggpk.file import GGPKFile
from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager


def test_ggpk_file_initialization():
    """Test GGPKFile initialization with default components."""
    ggpk = GGPKFile()

    assert ggpk.directory is None
    assert isinstance(ggpk._reader, GGPKReader)
    assert isinstance(ggpk._record_manager, GGPKRecordManager)
    assert isinstance(ggpk._directory_builder, GGPKDirectoryBuilder)
    assert isinstance(ggpk._diff_comparator, GGPKDiffComparator)


def test_ggpk_file_with_injected_components():
    """Test GGPKFile initialization with injected components."""
    reader = GGPKReader()
    record_manager = GGPKRecordManager()
    directory_builder = GGPKDirectoryBuilder()
    diff_comparator = GGPKDiffComparator()

    ggpk = GGPKFile(
        reader=reader,
        record_manager=record_manager,
        directory_builder=directory_builder,
        diff_comparator=diff_comparator,
    )

    assert ggpk._reader is reader
    assert ggpk._record_manager is record_manager
    assert ggpk._directory_builder is directory_builder
    assert ggpk._diff_comparator is diff_comparator


def test_ggpk_file_records_property():
    """Test records property (backward compatibility)."""
    ggpk = GGPKFile()

    # Initially empty
    assert len(ggpk.records) == 0

    # Can set records (backward compatibility)
    from PyPoE.poe.file.ggpk.records import BaseRecord

    class MockRecord(BaseRecord):
        tag = "TEST"

        def __init__(self):
            super().__init__(None, 0, 0)

    mock_record = MockRecord()
    ggpk.records = {0: mock_record}

    # Can get records
    assert len(ggpk.records) == 1
    assert ggpk.records[0] is mock_record


def test_ggpk_file_is_parsed_property():
    """Test is_parsed property."""
    ggpk = GGPKFile()

    # Initially not parsed
    assert not ggpk.is_parsed

    # After building directory, should be parsed
    # (This will fail without records, but we test the property)
    assert ggpk.directory is None
    assert not ggpk.is_parsed


def test_ggpk_file_getitem_raises_when_not_built():
    """Test __getitem__ raises when directory not built."""
    ggpk = GGPKFile()

    with pytest.raises(ValueError, match="Directory not build"):
        _ = ggpk["some/path"]


def test_ggpk_file_getitem_root():
    """Test __getitem__ with ROOT."""
    ggpk = GGPKFile()

    # Should raise if not built
    with pytest.raises(ValueError):
        _ = ggpk["ROOT"]


def test_ggpk_file_extension():
    """Test EXTENSION constant."""
    assert GGPKFile.EXTENSION == ".ggpk"


def test_ggpk_file_components_are_accessible():
    """Test that all components are accessible."""
    ggpk = GGPKFile()

    # All components should be accessible
    assert hasattr(ggpk, "_reader")
    assert hasattr(ggpk, "_record_manager")
    assert hasattr(ggpk, "_directory_builder")
    assert hasattr(ggpk, "_diff_comparator")

    # All should be initialized
    assert ggpk._reader is not None
    assert ggpk._record_manager is not None
    assert ggpk._directory_builder is not None
    assert ggpk._diff_comparator is not None

