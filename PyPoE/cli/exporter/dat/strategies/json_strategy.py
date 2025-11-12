"""
JSON export strategy for DAT files.

This module provides JSONExportStrategy for exporting DAT files to JSON format.
"""

from json import dump
from typing import Any

from PyPoE.cli.core import console
from PyPoE.cli.exporter.dat.strategies.base import ExportStrategy
from PyPoE.poe.file.dat import DatFile


class JsonExportStrategy(ExportStrategy):
    """
    Strategy for exporting DAT files to JSON format.

    Supports various JSON export options:
    - Object format vs list format
    - Virtual fields inclusion
    - ASCII encoding
    - Record length inclusion
    """

    def export(
        self,
        dat_file: DatFile,
        output_path: str,
        **options: Any,
    ) -> None:
        """
        Export DAT file to JSON format.

        Args:
            dat_file: DatFile instance to export
            output_path: Path to write JSON file
            **options: Export options:
                - use_object_format: Export as objects instead of lists (default: False)
                - include_virtual_fields: Include virtual fields (default: False)
                - force_ascii: Force ASCII encoding (default: False)
                - include_record_length: Include record length (default: False)
                - spec: Specification dict for field metadata
        """
        if dat_file.reader is None:
            raise ValueError("DatFile must be read before export")

        use_object_format = options.get("use_object_format", False)
        include_virtual_fields = options.get("include_virtual_fields", False)
        force_ascii = options.get("force_ascii", False)
        include_record_length = options.get("include_record_length", False)
        spec_dict = options.get("spec", {})

        file_name = dat_file._file_name or "unknown.dat"
        dict_spec = spec_dict.get(file_name, {})

        # Build header
        header = [
            dict({"name": name, "rowid": index}, **props)
            for index, (name, props) in enumerate(dict_spec.get("fields", {}).items())
        ]

        virtual_header = [
            dict({"name": name, "rowid": index}, **props)
            for index, (name, props) in enumerate(
                dict_spec.get("virtual_fields", {}).items()
            )
        ]

        # Build output object
        out_obj: dict[str, Any]
        if use_object_format:
            # Get column names from table_columns (dict keys)
            columns_data = list(dat_file.reader.table_columns.keys())  # type: ignore[attr-defined]
            out_obj = {
                "filename": file_name,
                "header": {row["name"]: row for row in header},
                "data": [
                    {
                        cid: row[i]
                        for i, cid in enumerate(columns_data)
                    }
                    for row in dat_file.reader.table_data
                ],
            }

            if include_virtual_fields:
                out_obj["virtual_header"] = {row["name"]: row for row in virtual_header}
        else:
            out_obj = {
                "filename": file_name,
                "header": header,
                "data": dat_file.reader.table_data,
            }

            if include_virtual_fields:
                out_obj["virtual_header"] = virtual_header

        if include_record_length:
            record_length = dat_file.reader.table_record_length
            if record_length is not None:
                out_obj["record_length"] = int(record_length)  # type: ignore[assignment]

        # Write to file
        console(f'Dumping data to "{output_path}"...')
        with open(
            output_path, mode="w", encoding="ascii" if force_ascii else "utf-8"
        ) as f:
            dump(out_obj, f, ensure_ascii=force_ascii, indent=4)

        console("Done.")

    def get_format_name(self) -> str:
        """Get format name."""
        return "JSON"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return "json"

