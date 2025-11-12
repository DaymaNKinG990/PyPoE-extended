"""
Strategy-based exporter for DAT files.

This module provides a unified exporter that uses Strategy Pattern to support
multiple export formats.
"""

from pathlib import Path
from typing import Any

from PyPoE.cli.core import console
from PyPoE.cli.exporter.dat.strategies.base import ExportStrategy
from PyPoE.poe.file.dat import DatFile


class DatStrategyExporter:
    """
    Exporter for DAT files using Strategy Pattern.

    This class allows exporting DAT files to different formats by using
    different ExportStrategy implementations.

    Example::

        exporter = DatStrategyExporter()
        exporter.set_strategy(JsonExportStrategy())
        exporter.export(dat_file, "output.json", use_object_format=True)
    """

    def __init__(self, strategy: ExportStrategy | None = None) -> None:
        """
        Initialize exporter.

        Args:
            strategy: Initial export strategy (optional)
        """
        self._strategy: ExportStrategy | None = strategy

    def set_strategy(self, strategy: ExportStrategy) -> None:
        """
        Set the export strategy.

        Args:
            strategy: ExportStrategy implementation to use
        """
        self._strategy = strategy

    def get_strategy(self) -> ExportStrategy | None:
        """
        Get current export strategy.

        Returns:
            Current ExportStrategy or None if not set
        """
        return self._strategy

    def export(
        self,
        dat_file: DatFile,
        output_path: str | Path,
        **options: Any,
    ) -> None:
        """
        Export DAT file using current strategy.

        Args:
            dat_file: DatFile instance to export
            output_path: Path to write exported file
            **options: Format-specific export options

        Raises:
            ValueError: If no strategy is set
            IOError: If export fails
        """
        if self._strategy is None:
            raise ValueError("Export strategy must be set before export")

        output_path_str = str(output_path)
        console(
            f"Exporting {dat_file._file_name or 'DAT file'} to {self._strategy.get_format_name()} format..."
        )

        self._strategy.export(dat_file, output_path_str, **options)

    def export_multiple(
        self,
        dat_files: dict[str, DatFile],
        output_dir: str | Path,
        **options: Any,
    ) -> None:
        """
        Export multiple DAT files using current strategy.

        Args:
            dat_files: Dictionary mapping file names to DatFile instances
            output_dir: Directory to write exported files
            **options: Format-specific export options
        """
        if self._strategy is None:
            raise ValueError("Export strategy must be set before export")

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        extension = self._strategy.get_file_extension()

        for file_name, dat_file in dat_files.items():
            # Remove .dat extension if present
            base_name = file_name.replace(".dat", "")
            output_path = output_dir_path / f"{base_name}.{extension}"

            self.export(dat_file, output_path, **options)

