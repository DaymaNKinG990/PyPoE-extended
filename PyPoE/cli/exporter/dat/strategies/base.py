"""
Base Strategy interfaces for data export.

This module provides the base Strategy Pattern interfaces for exporting DAT files
to various formats.
"""

from abc import ABC, abstractmethod
from typing import Any

from PyPoE.poe.file.dat import DatFile


class ExportStrategy(ABC):
    """
    Base strategy interface for exporting DAT files.

    This follows the Strategy Pattern, allowing different export formats
    to be implemented as separate strategies that can be swapped at runtime.

    Example::

        class JsonExportStrategy(ExportStrategy):
            def export(self, dat_file: DatFile, output_path: str, **options) -> None:
                # Export to JSON format
                ...

        strategy = JsonExportStrategy()
        strategy.export(dat_file, "output.json")
    """

    @abstractmethod
    def export(
        self,
        dat_file: DatFile,
        output_path: str,
        **options: Any,
    ) -> None:
        """
        Export DAT file to the target format.

        Args:
            dat_file: DatFile instance to export
            output_path: Path to write the exported file
            **options: Additional format-specific options

        Raises:
            ValueError: If dat_file is invalid
            IOError: If output_path cannot be written
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """
        Get the name of the export format.

        Returns:
            Format name (e.g., "JSON", "CSV", "XML")
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the default file extension for this format.

        Returns:
            File extension without dot (e.g., "json", "csv", "xml")
        """
        pass

