"""
Unit tests for GGPKFileBuilder.
"""

import pytest

from PyPoE.poe.file.ggpk.builder import GGPKFileBuilder
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager


class TestGGPKFileBuilder:
    """Test cases for GGPKFileBuilder."""

    def test_builder_with_file_path(self):
        """Test builder with file path."""
        builder = GGPKFileBuilder("test.ggpk")
        ggpk = builder.build()

        assert ggpk is not None
        assert ggpk.file_path == "test.ggpk"

    def test_builder_without_file_path(self):
        """Test builder without file path (can be set later)."""
        builder = GGPKFileBuilder()
        ggpk = builder.build()

        assert ggpk is not None

    def test_builder_with_reader(self):
        """Test builder with custom reader."""
        reader = GGPKReader()
        builder = GGPKFileBuilder("test.ggpk").with_reader(reader)
        ggpk = builder.build()

        assert ggpk._reader is reader

    def test_builder_with_record_manager(self):
        """Test builder with custom record manager."""
        manager = GGPKRecordManager()
        builder = GGPKFileBuilder("test.ggpk").with_record_manager(manager)
        ggpk = builder.build()

        assert ggpk._record_manager is manager

    def test_builder_with_directory_builder(self):
        """Test builder with custom directory builder."""
        directory_builder = GGPKDirectoryBuilder()
        builder = GGPKFileBuilder("test.ggpk").with_directory_builder(directory_builder)
        ggpk = builder.build()

        assert ggpk._directory_builder is directory_builder

    def test_builder_method_chaining(self):
        """Test builder method chaining."""
        reader = GGPKReader()
        manager = GGPKRecordManager()
        directory_builder = GGPKDirectoryBuilder()

        builder = (
            GGPKFileBuilder("test.ggpk")
            .with_reader(reader)
            .with_record_manager(manager)
            .with_directory_builder(directory_builder)
        )
        ggpk = builder.build()

        assert ggpk._reader is reader
        assert ggpk._record_manager is manager
        assert ggpk._directory_builder is directory_builder

    def test_builder_with_file_path_setter(self):
        """Test builder with_file_path setter."""
        builder = GGPKFileBuilder().with_file_path("test.ggpk")
        ggpk = builder.build()

        assert ggpk.file_path == "test.ggpk"

