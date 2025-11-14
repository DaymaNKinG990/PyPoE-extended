"""
Unit tests for DirectoryNode class.
"""

from unittest.mock import MagicMock

import pytest

from PyPoE.poe.file.ggpk.nodes import DirectoryNode
from PyPoE.poe.file.ggpk.records import FileRecord, DirectoryRecord


class TestDirectoryNode:
    """Test cases for DirectoryNode class."""

    def test_init(self) -> None:
        """Test DirectoryNode initialization."""
        container = MagicMock()
        record = DirectoryRecord(container=container, length=100, offset=0)
        record.name = "test"
        node = DirectoryNode(record)
        assert node.record == record
        assert node.children == []
        assert node.parent is None

    def test_add_child(self) -> None:
        """Test adding a child node."""
        container = MagicMock()
        parent_record = DirectoryRecord(container=container, length=100, offset=0)
        parent_record.name = "parent"
        child_record = DirectoryRecord(container=container, length=100, offset=100)
        child_record.name = "child"
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        assert child in parent.children
        assert child.parent == parent

    def test_add_child_file(self) -> None:
        """Test adding a file child."""
        container = MagicMock()
        dir_record = DirectoryRecord(container=container, length=100, offset=0)
        dir_record.name = "dir"
        file_record = FileRecord(container=container, length=100, offset=200)
        file_record.name = "file.dat"
        parent = DirectoryNode(dir_record)
        child = DirectoryNode(file_record)

        parent.add_child(child)
        assert child in parent.children

    def test_remove_child(self) -> None:
        """Test removing a child node."""
        container = MagicMock()
        parent_record = DirectoryRecord(container=container, length=100, offset=0)
        parent_record.name = "parent"
        child_record = DirectoryRecord(container=container, length=100, offset=100)
        child_record.name = "child"
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        assert len(parent.children) == 1

        parent.remove_child(child)
        assert len(parent.children) == 0
        assert child.parent is None

    def test_get_child_by_name(self) -> None:
        """Test getting child by name."""
        container = MagicMock()
        parent_record = DirectoryRecord(container=container, length=100, offset=0)
        parent_record.name = "parent"
        child_record = DirectoryRecord(container=container, length=100, offset=100)
        child_record.name = "child"
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        found = parent.get_child_by_name("child")
        assert found == child

    def test_get_child_by_name_not_found(self) -> None:
        """Test getting non-existent child."""
        container = MagicMock()
        parent_record = DirectoryRecord(container=container, length=100, offset=0)
        parent_record.name = "parent"
        parent = DirectoryNode(parent_record)
        found = parent.get_child_by_name("nonexistent")
        assert found is None

    def test_get_path(self) -> None:
        """Test getting node path."""
        container = MagicMock()
        root_record = DirectoryRecord(container=container, length=100, offset=0)
        root_record.name = ""
        dir_record = DirectoryRecord(container=container, length=100, offset=100)
        dir_record.name = "dir"
        file_record = FileRecord(container=container, length=100, offset=200)
        file_record.name = "file.dat"

        root = DirectoryNode(root_record)
        dir_node = DirectoryNode(dir_record)
        file_node = DirectoryNode(file_record)

        root.add_child(dir_node)
        dir_node.add_child(file_node)

        assert file_node.get_path() == "dir/file.dat"

    def test_get_path_root(self) -> None:
        """Test getting path for root node."""
        container = MagicMock()
        root_record = DirectoryRecord(container=container, length=100, offset=0)
        root_record.name = ""
        root = DirectoryNode(root_record)
        assert root.get_path() == ""

    def test_is_directory(self) -> None:
        """Test checking if node is directory."""
        container = MagicMock()
        dir_record = DirectoryRecord(container=container, length=100, offset=0)
        dir_record.name = "dir"
        node = DirectoryNode(dir_record)
        assert node.is_directory() is True

    def test_is_file(self) -> None:
        """Test checking if node is file."""
        container = MagicMock()
        file_record = FileRecord(container=container, length=100, offset=0)
        file_record.name = "file.dat"
        node = DirectoryNode(file_record)
        assert node.is_file() is True

    def test_iter_children(self) -> None:
        """Test iterating over children."""
        container = MagicMock()
        parent_record = DirectoryRecord(container=container, length=100, offset=0)
        parent_record.name = "parent"
        parent = DirectoryNode(parent_record)

        for i in range(3):
            child_record = DirectoryRecord(container=container, length=100, offset=(i + 1) * 100)
            child_record.name = f"child{i}"
            child = DirectoryNode(child_record)
            parent.add_child(child)

        children = list(parent.iter_children())
        assert len(children) == 3

