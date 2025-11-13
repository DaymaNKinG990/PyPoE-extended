"""
CSV export strategy for DAT files.

This module provides CsvExportStrategy for exporting DAT files to CSV format.
"""

import csv
from typing import Any

from PyPoE.cli.core import console
from PyPoE.cli.exporter.dat.strategies.base import ExportStrategy
from PyPoE.poe.file.dat import DatFile


class CsvExportStrategy(ExportStrategy):
    """
    Strategy for exporting DAT files to CSV format.

    Supports CSV export with:
    - Custom delimiter
    - Header row
    - Quote handling
    """

    def export(
        self,
        dat_file: DatFile,
        output_path: str,
        **options: Any,
    ) -> None:
        """
        Export DAT file to CSV format.

        Args:
            dat_file: DatFile instance to export
            output_path: Path to write CSV file
            **options: Export options:
                - delimiter: CSV delimiter (default: ',')
                - include_header: Include header row (default: True)
                - quote_all: Quote all fields (default: False)
        """
        if dat_file.reader is None:
            raise ValueError("DatFile must be read before export")

        delimiter = options.get("delimiter", ",")
        include_header = options.get("include_header", True)
        quote_all = options.get("quote_all", False)

        console(f'Exporting data to "{output_path}"...')

        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(
                f,
                delimiter=delimiter,
                quoting=csv.QUOTE_ALL if quote_all else csv.QUOTE_MINIMAL,
            )

            # Write header
            if include_header and dat_file.reader.table_columns:  # type: ignore[attr-defined]
                # Get column names from table_columns (dict keys)
                columns_data = list(dat_file.reader.table_columns.keys())  # type: ignore[attr-defined]
                writer.writerow(columns_data)

            # Write data rows
            for row in dat_file.reader.table_data:
                writer.writerow(row)

        console("Done.")

    def get_format_name(self) -> str:
        """
        Get the name of the export format.

        Returns:
            Format name ("CSV")
        """
        return "CSV"

    def get_file_extension(self) -> str:
        """
        Get the default file extension for this format.

        Returns:
            File extension without dot ("csv")
        """
        return "csv"

