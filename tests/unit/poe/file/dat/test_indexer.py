"""
Unit tests for DatIndexer class.
"""

from collections import OrderedDict
from unittest.mock import MagicMock

import pytest

from PyPoE.poe.file.dat.indexer import DatIndexer
from PyPoE.poe.file.dat.record import DatRecord


class TestDatIndexer:
    """Test cases for DatIndexer class."""

    def test_init(self) -> None:
        """Test DatIndexer initialization."""
        spec = MagicMock()
        columns_unique = OrderedDict([("id", None), ("name", None)])
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)
        assert indexer.specification == spec
        assert indexer.columns_unique == columns_unique
        assert indexer.index == {}

    def test_build_index_single_unique_column(self) -> None:
        """Test building index for a single unique column."""
        spec = MagicMock()
        spec.fields = {
            "id": MagicMock(type="int"),
        }
        columns_unique = OrderedDict([("id", None)])
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        # Create mock parent for DatRecord
        parent = MagicMock()
        parent.table_columns = OrderedDict([("id", {"index": 0})])
        records = [
            DatRecord(parent, 0),
            DatRecord(parent, 1),
            DatRecord(parent, 2),
        ]
        records[0].append(1)  # id = 1
        records[1].append(2)  # id = 2
        records[2].append(3)  # id = 3

        indexer.build_index(records, column="id")
        assert "id" in indexer.index
        assert indexer.index["id"][1] == records[0]
        assert indexer.index["id"][2] == records[1]
        assert indexer.index["id"][3] == records[2]

    def test_build_index_multiple_unique_columns(self) -> None:
        """Test building index for multiple unique columns."""
        spec = MagicMock()
        spec.fields = {
            "id": MagicMock(type="int"),
            "name": MagicMock(type="string"),
        }
        columns_unique = OrderedDict([("id", None), ("name", None)])
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        parent = MagicMock()
        parent.table_columns = OrderedDict([("id", {"index": 0}), ("name", {"index": 1})])
        records = [
            DatRecord(parent, 0),
            DatRecord(parent, 1),
        ]
        records[0].extend([1, "Item1"])
        records[1].extend([2, "Item2"])

        indexer.build_index(records, column=["id", "name"])
        assert "id" in indexer.index
        assert "name" in indexer.index
        assert indexer.index["id"][1] == records[0]
        assert indexer.index["name"]["Item1"] == records[0]

    def test_build_index_all_unique_columns(self) -> None:
        """Test building index for all unique columns (default)."""
        spec = MagicMock()
        spec.fields = {
            "id": MagicMock(type="int"),
        }
        columns_unique = OrderedDict([("id", None)])
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        parent = MagicMock()
        parent.table_columns = OrderedDict([("id", {"index": 0})])
        records = [
            DatRecord(parent, 0),
            DatRecord(parent, 1),
        ]
        records[0].append(1)
        records[1].append(2)

        indexer.build_index(records)  # No column specified
        assert "id" in indexer.index
        assert indexer.index["id"][1] == records[0]

    def test_build_index_non_unique_column(self) -> None:
        """Test building index for non-unique column."""
        spec = MagicMock()
        spec.fields = {
            "category": MagicMock(type="string"),
        }
        columns_unique = OrderedDict()
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        parent = MagicMock()
        parent.table_columns = OrderedDict([("category", {"index": 0})])
        records = [
            DatRecord(parent, 0),
            DatRecord(parent, 1),
            DatRecord(parent, 2),
        ]
        records[0].append("A")
        records[1].append("A")
        records[2].append("B")

        indexer.build_index(records, column="category")
        assert "category" in indexer.index
        # Non-unique columns return lists
        assert len(indexer.index["category"]["A"]) == 2
        assert len(indexer.index["category"]["B"]) == 1

    def test_build_index_ref_list_column(self) -> None:
        """Test building index for ref|list column."""
        spec = MagicMock()
        spec.fields = {
            "tags": MagicMock(type="ref|list|int"),
        }
        columns_unique = OrderedDict()
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        parent = MagicMock()
        parent.table_columns = OrderedDict([("tags", {"index": 0})])
        records = [
            DatRecord(parent, 0),
            DatRecord(parent, 1),
        ]
        records[0].append([1, 2])
        records[1].append([2, 3])

        indexer.build_index(records, column="tags")
        assert "tags" in indexer.index
        # Each value in the list is indexed
        assert len(indexer.index["tags"][1]) == 1
        assert len(indexer.index["tags"][2]) == 2
        assert len(indexer.index["tags"][3]) == 1

    def test_build_index_empty_records(self) -> None:
        """Test building index with empty records."""
        spec = MagicMock()
        spec.fields = {}
        columns_unique = OrderedDict([("id", None)])
        indexer = DatIndexer(specification=spec, columns_unique=columns_unique)

        indexer.build_index([], column="id")
        assert "id" in indexer.index
        assert len(indexer.index["id"]) == 0

