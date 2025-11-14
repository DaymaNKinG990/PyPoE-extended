"""
Unit tests for DirectoryNode class.
"""

import pytest

from PyPoE.poe.file.ggpk.nodes import DirectoryNode
from PyPoE.poe.file.ggpk.records import FileRecord, DirectoryRecord


class TestDirectoryNode:
    """Test cases for DirectoryNode class."""

    def test_init(self) -> None:
        """Test DirectoryNode initialization."""
        record = DirectoryRecord(name="test", entries=[])
        node = DirectoryNode(record)
        assert node.record == record
        assert node.children == []
        assert node.parent is None

    def test_add_child(self) -> None:
        """Test adding a child node."""
        parent_record = DirectoryRecord(name="parent", entries=[])
        child_record = DirectoryRecord(name="child", entries=[])
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        assert child in parent.children
        assert child.parent == parent

    def test_add_child_file(self) -> None:
        """Test adding a file child."""
        dir_record = DirectoryRecord(name="dir", entries=[])
        file_record = FileRecord(name="file.dat", data_offset=0, data_length=100)
        parent = DirectoryNode(dir_record)
        child = DirectoryNode(file_record)

        parent.add_child(child)
        assert child in parent.children

    def test_remove_child(self) -> None:
        """Test removing a child node."""
        parent_record = DirectoryRecord(name="parent", entries=[])
        child_record = DirectoryRecord(name="child", entries=[])
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        assert len(parent.children) == 1

        parent.remove_child(child)
        assert len(parent.children) == 0
        assert child.parent is None

    def test_get_child_by_name(self) -> None:
        """Test getting child by name."""
        parent_record = DirectoryRecord(name="parent", entries=[])
        child_record = DirectoryRecord(name="child", entries=[])
        parent = DirectoryNode(parent_record)
        child = DirectoryNode(child_record)

        parent.add_child(child)
        found = parent.get_child_by_name("child")
        assert found == child

    def test_get_child_by_name_not_found(self) -> None:
        """Test getting non-existent child."""
        parent_record = DirectoryRecord(name="parent", entries=[])
        parent = DirectoryNode(parent_record)
        found = parent.get_child_by_name("nonexistent")
        assert found is None

    def test_get_path(self) -> None:
        """Test getting node path."""
        root_record = DirectoryRecord(name="", entries=[])
        dir_record = DirectoryRecord(name="dir", entries=[])
        file_record = FileRecord(name="file.dat", data_offset=0, data_length=100)

        root = DirectoryNode(root_record)
        dir_node = DirectoryNode(dir_record)
        file_node = DirectoryNode(file_record)

        root.add_child(dir_node)
        dir_node.add_child(file_node)

        assert file_node.get_path() == "dir/file.dat"

    def test_get_path_root(self) -> None:
        """Test getting path for root node."""
        root_record = DirectoryRecord(name="", entries=[])
        root = DirectoryNode(root_record)
        assert root.get_path() == ""

    def test_is_directory(self) -> None:
        """Test checking if node is directory."""
        dir_record = DirectoryRecord(name="dir", entries=[])
        node = DirectoryNode(dir_record)
        assert node.is_directory() is True

    def test_is_file(self) -> None:
        """Test checking if node is file."""
        file_record = FileRecord(name="file.dat", data_offset=0, data_length=100)
        node = DirectoryNode(file_record)
        assert node.is_file() is True

    def test_iter_children(self) -> None:
        """Test iterating over children."""
        parent_record = DirectoryRecord(name="parent", entries=[])
        parent = DirectoryNode(parent_record)

        for i in range(3):
            child_record = DirectoryRecord(name=f"child{i}", entries=[])
            child = DirectoryNode(child_record)
            parent.add_child(child)

        children = list(parent.iter_children())
        assert len(children) == 3

