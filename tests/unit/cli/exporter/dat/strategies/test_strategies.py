"""
Unit tests for export strategies.
"""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from PyPoE.cli.exporter.dat.strategies.base import ExportStrategy
from PyPoE.cli.exporter.dat.strategies.csv_strategy import CsvExportStrategy
from PyPoE.cli.exporter.dat.strategies.json_strategy import JsonExportStrategy
from PyPoE.cli.exporter.dat.strategy_exporter import DatStrategyExporter
from PyPoE.poe.file.dat import DatFile


class TestExportStrategy:
    """Test cases for base ExportStrategy."""

    def test_export_strategy_is_abstract(self):
        """Test that ExportStrategy is an abstract base class."""
        with pytest.raises(TypeError):
            ExportStrategy()  # type: ignore[abstract]


class TestJsonExportStrategy:
    """Test cases for JsonExportStrategy."""

    @pytest.fixture
    def mock_dat_file(self):
        """Create a mock DatFile for testing."""
        dat_file = MagicMock(spec=DatFile)
        dat_file._file_name = "Test.dat"
        dat_file.reader = MagicMock()
        dat_file.reader.columns_data = ["Id", "Name", "Value"]
        dat_file.reader.table_data = [
            ["item1", "Item 1", 100],
            ["item2", "Item 2", 200],
        ]
        dat_file.reader.table_record_length = 32
        return dat_file

    def test_get_format_name(self):
        """Test format name."""
        strategy = JsonExportStrategy()
        assert strategy.get_format_name() == "JSON"

    def test_get_file_extension(self):
        """Test file extension."""
        strategy = JsonExportStrategy()
        assert strategy.get_file_extension() == "json"

    def test_export_basic(self, mock_dat_file):
        """Test basic JSON export."""
        strategy = JsonExportStrategy()

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"

            with patch("PyPoE.cli.core.console"):
                strategy.export(
                    mock_dat_file,
                    str(output_path),
                    spec={"Test.dat": {"fields": {}, "virtual_fields": {}}},
                )

            assert output_path.exists()
            content = output_path.read_text()
            assert "filename" in content
            assert "Test.dat" in content
            assert "header" in content
            assert "data" in content

    def test_export_with_options(self, mock_dat_file):
        """Test JSON export with options."""
        strategy = JsonExportStrategy()

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"

            with patch("PyPoE.cli.core.console"):
                strategy.export(
                    mock_dat_file,
                    str(output_path),
                    use_object_format=True,
                    include_virtual_fields=True,
                    include_record_length=True,
                    spec={"Test.dat": {"fields": {}, "virtual_fields": {}}},
                )

            assert output_path.exists()
            content = output_path.read_text()
            assert "record_length" in content

    def test_export_raises_on_unread_file(self):
        """Test that export raises on unread file."""
        strategy = JsonExportStrategy()
        dat_file = MagicMock(spec=DatFile)
        dat_file.reader = None

        with pytest.raises(ValueError, match="must be read"):
            strategy.export(dat_file, "test.json")


class TestCsvExportStrategy:
    """Test cases for CsvExportStrategy."""

    @pytest.fixture
    def mock_dat_file(self):
        """Create a mock DatFile for testing."""
        dat_file = MagicMock(spec=DatFile)
        dat_file._file_name = "Test.dat"
        dat_file.reader = MagicMock()
        dat_file.reader.columns_data = ["Id", "Name", "Value"]
        dat_file.reader.table_data = [
            ["item1", "Item 1", 100],
            ["item2", "Item 2", 200],
        ]
        return dat_file

    def test_get_format_name(self):
        """Test format name."""
        strategy = CsvExportStrategy()
        assert strategy.get_format_name() == "CSV"

    def test_get_file_extension(self):
        """Test file extension."""
        strategy = CsvExportStrategy()
        assert strategy.get_file_extension() == "csv"

    def test_export_basic(self, mock_dat_file):
        """Test basic CSV export."""
        strategy = CsvExportStrategy()

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            with patch("PyPoE.cli.core.console"):
                strategy.export(mock_dat_file, str(output_path))

            assert output_path.exists()
            content = output_path.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 3  # Header + 2 data rows
            assert "Id,Name,Value" in content

    def test_export_without_header(self, mock_dat_file):
        """Test CSV export without header."""
        strategy = CsvExportStrategy()

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"

            with patch("PyPoE.cli.core.console"):
                strategy.export(mock_dat_file, str(output_path), include_header=False)

            assert output_path.exists()
            content = output_path.read_text()
            assert "Id,Name,Value" not in content

    def test_export_raises_on_unread_file(self):
        """Test that export raises on unread file."""
        strategy = CsvExportStrategy()
        dat_file = MagicMock(spec=DatFile)
        dat_file.reader = None

        with pytest.raises(ValueError, match="must be read"):
            strategy.export(dat_file, "test.csv")


class TestDatStrategyExporter:
    """Test cases for DatStrategyExporter."""

    def test_set_and_get_strategy(self):
        """Test setting and getting strategy."""
        exporter = DatStrategyExporter()
        strategy = JsonExportStrategy()

        exporter.set_strategy(strategy)
        assert exporter.get_strategy() is strategy

    def test_export_without_strategy_raises(self):
        """Test that export raises without strategy."""
        exporter = DatStrategyExporter()
        dat_file = MagicMock(spec=DatFile)

        with pytest.raises(ValueError, match="strategy must be set"):
            exporter.export(dat_file, "test.json")

    def test_export_with_strategy(self):
        """Test export with strategy."""
        exporter = DatStrategyExporter()
        strategy = MagicMock(spec=ExportStrategy)
        strategy.get_format_name.return_value = "JSON"
        exporter.set_strategy(strategy)

        dat_file = MagicMock(spec=DatFile)
        dat_file._file_name = "Test.dat"

        with patch("PyPoE.cli.core.console"):
            exporter.export(dat_file, "test.json")

        strategy.export.assert_called_once()

    def test_export_multiple(self):
        """Test exporting multiple files."""
        exporter = DatStrategyExporter()
        strategy = MagicMock(spec=ExportStrategy)
        strategy.get_format_name.return_value = "JSON"
        strategy.get_file_extension.return_value = "json"
        exporter.set_strategy(strategy)

        dat_files = {
            "File1.dat": MagicMock(spec=DatFile),
            "File2.dat": MagicMock(spec=DatFile),
        }

        with TemporaryDirectory() as tmpdir:
            with patch("PyPoE.cli.core.console"):
                exporter.export_multiple(dat_files, tmpdir)

        assert strategy.export.call_count == 2

