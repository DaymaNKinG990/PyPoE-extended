"""
Parser for DAT file binary format.

This module handles parsing of binary DAT file data into structured format.
"""

import struct
from collections import OrderedDict
from io import BytesIO
from typing import Any

from PyPoE.poe.file.dat.caster import CastTypes, DatCaster
from PyPoE.poe.file.dat.record import DatRecord
from PyPoE.poe.file.specification.errors import SpecificationError

DAT_FILE_MAGIC_NUMBER = b"\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb"
_TABLE_OFFSET = 4


class DatParser:
    """
    Handles parsing of binary DAT file data.

    This class is responsible for:
    - Reading file structure (table and data sections)
    - Parsing rows from table section
    - Coordinating with DatCaster for type conversion
    """

    def __init__(
        self,
        file_name: str,
        specification: Any,
        caster: DatCaster,
        x64: bool = False,
    ) -> None:
        """
        Initialize DatParser.

        Args:
            file_name: Name of the DAT file
            specification: File specification
            caster: DatCaster instance for type conversion
            x64: Whether to use 64-bit mode for dat64 files
        """
        self.file_name = file_name
        self.specification = specification
        self.caster = caster
        self.x64 = x64

        # Prepare casts from specification
        self.table_columns = OrderedDict()
        self.cast_size = 0
        self.cast_spec: list[tuple[Any, list[tuple[CastTypes, int, str]]]] = []
        self.cast_row: list[str] = []

        for i, key in enumerate(specification.columns_data):  # type: ignore[union-attr]
            k = specification.fields[key]  # type: ignore[union-attr]
            self.table_columns[key] = {"index": i, "section": k}
            casts = []
            remainder = k.type
            while remainder:
                remainder, cast_type = self.caster.parse_cast_string(remainder)
                casts.append(cast_type)
            self.cast_size += casts[0][1]

            self.cast_spec.append((k, casts))
            self.cast_row.append(casts[0][2])

        self.cast_row = "<" + "".join(self.cast_row)  # type: ignore[assignment]

    def parse_file(self, raw: bytes | BytesIO) -> tuple[bytes, int, int, int, int]:
        """
        Parse file header and return file structure information.

        Args:
            raw: Raw file bytes or BytesIO

        Returns:
            Tuple of (file_raw, file_length, data_offset, table_rows, table_record_length)

        Raises:
            ValueError: If magic number not found or invalid file structure
        """
        if isinstance(raw, bytes):
            file_raw = raw
        elif isinstance(raw, BytesIO):
            file_raw = raw.read()
        else:
            raise TypeError(f"Raw must be bytes or BytesIO instance, got {type(raw)}")

        file_length = len(file_raw)

        data_offset = file_raw.find(DAT_FILE_MAGIC_NUMBER)

        if data_offset == -1:
            raise ValueError(f'Did not find data magic number in "{self.file_name}"')

        table_rows = struct.unpack("<I", file_raw[0:4])[0]
        table_length = data_offset - _TABLE_OFFSET

        if table_rows > 0:
            table_record_length = table_length // table_rows
        elif table_rows == 0 and table_length == 0:
            table_record_length = 0
        else:
            raise ValueError("Invalid file structure: table_rows and table_length mismatch")

        # Validate row size
        if self.cast_size != table_record_length:
            raise SpecificationError(
                SpecificationError.ERRORS.RUNTIME_ROWSIZE_MISMATCH,
                f'"{self.file_name}": Specification row size {self.cast_size} vs real size {table_record_length}',
            )

        return file_raw, file_length, data_offset, table_rows, table_record_length

    def parse_row(
        self,
        file_raw: bytes,
        data_offset: int,
        rowid: int,
        table_record_length: int,
        parent: Any,
    ) -> DatRecord:
        """
        Parse a single row from the table section.

        Args:
            file_raw: Raw file bytes
            data_offset: Offset to data section
            rowid: Row index
            table_record_length: Length of each table record
            parent: Parent DatReader instance

        Returns:
            DatRecord instance
        """
        offset = _TABLE_OFFSET + rowid * table_record_length
        row_data = DatRecord(parent, rowid)
        data_raw = file_raw[offset : offset + table_record_length]

        # We don't have any data, return early
        if len(data_raw) == 0:
            return row_data

        # Unpacking the entire row in one go will help breaking down the
        # function calls significantly
        row_unpacked = struct.unpack(self.cast_row, data_raw)  # type: ignore[arg-type]
        i = 0
        for spec, casts in self.cast_spec:
            if casts[0][0] == CastTypes.POINTER_LIST:
                cell_data = row_unpacked[i : i + 2]
                i += 1
            else:
                cell_data = (row_unpacked[i],)
            row_data.append(
                self.caster.cast_from_spec(
                    file_raw, data_offset, spec, casts, data=cell_data, offset=offset
                )
            )
            offset += casts[0][1]
            i += 1

        return row_data

