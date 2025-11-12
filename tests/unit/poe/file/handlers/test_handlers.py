"""
Unit tests for File Handlers (Chain of Responsibility pattern).
"""

from unittest.mock import MagicMock

import pytest

from PyPoE.poe.file.handlers.base import FileHandler
from PyPoE.poe.file.handlers.bundle_handler import BundleHandler
from PyPoE.poe.file.handlers.dat_handler import DatFileHandler
from PyPoE.poe.file.handlers.ggpk_handler import GGPKFileHandler
from PyPoE.poe.file.handlers.processor import FileProcessor


class TestFileHandler:
    """Test cases for base FileHandler."""

    def test_file_handler_is_abstract(self):
        """Test that FileHandler is an abstract base class."""
        with pytest.raises(TypeError):
            FileHandler()  # type: ignore[abstract]

    def test_set_next_handler(self):
        """Test setting next handler in chain."""
        handler1 = MagicMock(spec=FileHandler)
        handler2 = MagicMock(spec=FileHandler)
        handler1.set_next = MagicMock(return_value=handler2)

        result = handler1.set_next(handler2)

        assert result is handler2
        handler1.set_next.assert_called_once_with(handler2)


class TestGGPKFileHandler:
    """Test cases for GGPKFileHandler."""

    def test_can_handle_ggpk_file(self):
        """Test that handler can identify GGPK files."""
        handler = GGPKFileHandler()
        ggpk_file = MagicMock()
        ggpk_file.__class__.__name__ = "GGPKFile"

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=True):
            assert handler.can_handle(ggpk_file) is True

    def test_can_handle_non_ggpk_file(self):
        """Test that handler rejects non-GGPK files."""
        handler = GGPKFileHandler()
        dat_file = MagicMock()
        dat_file.__class__.__name__ = "DatFile"

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=False):
            assert handler.can_handle(dat_file) is False

    def test_handle_ggpk_file(self):
        """Test handling GGPK file."""
        handler = GGPKFileHandler()
        ggpk_file = MagicMock()
        ggpk_file.directory = None
        ggpk_file.directory_build = MagicMock()

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=True):
            handler.handle(ggpk_file)
            ggpk_file.directory_build.assert_called_once()

    def test_handle_passes_to_next(self):
        """Test that handler passes non-GGPK files to next handler."""
        handler = GGPKFileHandler()
        next_handler = MagicMock(spec=FileHandler)
        handler.set_next(next_handler)

        dat_file = MagicMock()

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=False):
            handler.handle(dat_file)
            next_handler.handle.assert_called_once_with(dat_file)


class TestDatFileHandler:
    """Test cases for DatFileHandler."""

    def test_can_handle_dat_file(self):
        """Test that handler can identify DAT files."""
        handler = DatFileHandler()
        dat_file = MagicMock()
        dat_file.__class__.__name__ = "DatFile"

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=True):
            assert handler.can_handle(dat_file) is True


class TestBundleHandler:
    """Test cases for BundleHandler."""

    def test_can_handle_bundle(self):
        """Test that handler can identify Bundle files."""
        handler = BundleHandler()
        bundle_file = MagicMock()
        bundle_file.__class__.__name__ = "Bundle"

        # Mock isinstance check
        with pytest.mock.patch("builtins.isinstance", return_value=True):
            assert handler.can_handle(bundle_file) is True


class TestFileProcessor:
    """Test cases for FileProcessor."""

    def test_add_handler(self):
        """Test adding handlers to processor."""
        processor = FileProcessor()
        handler1 = MagicMock(spec=FileHandler)
        handler2 = MagicMock(spec=FileHandler)

        processor.add_handler(handler1)
        assert processor._chain is handler1

        processor.add_handler(handler2)
        # Second handler should be chained to first
        handler1.set_next.assert_called_once_with(handler2)

    def test_process_file(self):
        """Test processing file through chain."""
        processor = FileProcessor()
        handler = MagicMock(spec=FileHandler)
        processor.add_handler(handler)

        file = MagicMock()
        processor.process(file)

        handler.handle.assert_called_once_with(file)

    def test_clear_chain(self):
        """Test clearing handler chain."""
        processor = FileProcessor()
        handler = MagicMock(spec=FileHandler)
        processor.add_handler(handler)

        processor.clear_chain()
        assert processor._chain is None

