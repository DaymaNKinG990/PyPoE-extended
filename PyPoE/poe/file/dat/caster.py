"""
Type casting for DAT files.

This module handles conversion of binary data to Python types according to
DAT file specifications.
"""

import struct
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from PyPoE.poe.file.dat.value import DatValue

if TYPE_CHECKING:
    from PyPoE.poe.file.dat.reader import DatReader


class CastTypes(IntEnum):
    """Types of casts for DAT file values."""

    VALUE = 1
    STRING = 2
    POINTER_LIST = 3
    POINTER = 4
    POINTER_SELF = 5


class DatCaster:
    """
    Handles type casting for DAT file values.

    This class is responsible for converting binary data to Python types
    according to DAT file specifications.
    """

    _cast_table = {
        "bool": ["?", 1],
        "byte": ["b", 1],
        "ubyte": ["B", 1],
        "short": ["h", 2],
        "ushort": ["H", 2],
        "int": ["i", 4],
        "uint": ["I", 4],
        "long": ["q", 8],
        "ulong": ["Q", 8],
        "float": ["f", 4],
        "double": ["d", 8],
    }

    def __init__(self, use_dat_value: bool = True, x64: bool = False) -> None:
        """
        Initialize DatCaster.

        Args:
            use_dat_value: Whether to use DatValue instances or raw values
            x64: Whether to use 64-bit mode for dat64 files
        """
        self.use_dat_value = use_dat_value
        self.x64 = x64
        self.data_parsed: list[int] = []

    def parse_cast_string(self, caststr: str) -> tuple[str, tuple[CastTypes, int, str]]:
        """
        Parse a cast string and return cast type information.

        Args:
            caststr: Cast string from specification (e.g., "int", "ref|string", "ref|list|int")

        Returns:
            Tuple of (remainder, (cast_type, size, struct_format))
        """
        size: int | None = None
        cast: str | None = None
        remainder = ""
        cast_type: CastTypes

        if caststr in self._cast_table:
            cast_type = CastTypes.VALUE
            table_entry = self._cast_table[caststr]
            size = table_entry[1]  # type: ignore[assignment]
            cast = table_entry[0]  # type: ignore[assignment]
        elif caststr == "string":
            cast_type = CastTypes.STRING
        elif caststr.startswith("ref|list|"):
            cast_type = CastTypes.POINTER_LIST
            if self.x64:
                size = 16
                cast = "QQ"
            else:
                size = 8
                cast = "II"
            remainder = caststr[9:]
        elif caststr.startswith("ref|"):
            if self.x64:
                size = 8
                cast = "Q"
            else:
                size = 4
                cast = "I"
            if caststr.startswith("ref|generic"):
                cast_type = CastTypes.POINTER_SELF
            else:
                cast_type = CastTypes.POINTER
                remainder = caststr[4:]
        else:
            raise ValueError(f"Unknown cast type: {caststr}")

        if size is None or cast is None:
            raise ValueError(f"Invalid cast type: {caststr}")

        return remainder, (cast_type, size, cast)

    def cast_from_spec(
        self,
        file_raw: bytes,
        data_offset: int,
        specification: Any,
        casts: list[tuple[CastTypes, int, str]],
        parent: "DatReader | DatValue | None" = None,
        offset: int | None = None,
        data: tuple | None = None,
    ) -> Any:
        """
        Cast a value from specification.

        Args:
            file_raw: Raw file bytes
            data_offset: Offset to data section
            specification: Field specification
            casts: List of cast tuples (cast_type, size, struct_format)
            parent: Parent DatValue (for nested structures)
            offset: Byte offset in file
            data: Pre-unpacked data (optional)

        Returns:
            Casted value (DatValue or raw Python type)
        """
        if casts[0][0] in (CastTypes.VALUE, CastTypes.POINTER_SELF):
            if offset is None:
                raise ValueError("offset is required for VALUE/POINTER_SELF casts")
            ivalue = (
                data[0]
                if data
                else struct.unpack("<" + casts[0][2], file_raw[offset : offset + casts[0][1]])[0]
            )

            # Handle special null values
            if ivalue in (
                -0x1010102,
                0xFEFEFEFE,
                -0x101010101010102,
                0xFEFEFEFEFEFEFEFE,
                0xFFFFFFFF,
            ):
                ivalue = None

            if self.use_dat_value:
                return DatValue(ivalue, offset, casts[0][1], parent, specification)  # type: ignore[arg-type]
            else:
                return ivalue
        elif casts[0][0] == CastTypes.STRING:
            if offset is None:
                raise ValueError("offset is required for STRING casts")
            # Beginning of the sequence, +1 to adjust for it
            offset_new = file_raw.find(b"\x00\x00\x00\x00", offset)
            # Account for 0 size strings
            if offset == offset_new:
                string = ""
            else:
                # It's possible that a string ends in \x00 and the next starts
                # with \x00
                # UTF-16 must be at least a multiple of 2
                while (offset_new - offset) % 2:
                    offset_new = file_raw.find(b"\x00\x00\x00\x00", offset_new + 1)
                string = file_raw[offset:offset_new].decode("utf-16")
            # Store the offset including the null terminator
            if self.use_dat_value:
                return DatValue(
                    string, offset, offset_new - offset + 4, parent, specification  # type: ignore[arg-type]
                )
            else:
                return string
        elif casts[0][0] in (CastTypes.POINTER_LIST, CastTypes.POINTER):
            if offset is None:
                raise ValueError("offset is required for POINTER/POINTER_LIST casts")
            data = (
                data
                if data
                else struct.unpack("<" + casts[0][2], file_raw[offset : offset + casts[0][1]])
            )
            data_offset_actual = data[-1] + data_offset

            # Instance..
            if self.use_dat_value:
                result = DatValue(
                    data[0] if casts[0][0] == CastTypes.POINTER_LIST else data,
                    offset,
                    casts[0][1],
                    parent,
                    specification,  # type: ignore[arg-type]
                )

                if casts[0][0] == CastTypes.POINTER_LIST:
                    result.children = []
                    for i in range(0, data[0]):
                        result.children.append(
                            self.cast_from_spec(
                                file_raw,
                                data_offset,
                                specification,
                                casts[1:],
                                result,
                                data_offset_actual + i * casts[1:][0][1],
                            )
                        )
                elif casts[0][0] == CastTypes.POINTER:
                    result.child = self.cast_from_spec(
                        file_raw, data_offset, specification, casts[1:], result, data_offset_actual
                    )
                self.data_parsed.append(result)  # type: ignore[arg-type]
            else:
                if casts[0][0] == CastTypes.POINTER_LIST:
                    result_list: Any = []
                    for i in range(0, data[0]):
                        result_list.append(
                            self.cast_from_spec(
                                file_raw,
                                data_offset,
                                specification,
                                casts[1:],
                                None,
                                data_offset_actual + i * casts[1:][0][1],
                            )
                        )
                    result = result_list
                elif casts[0][0] == CastTypes.POINTER:
                    result = self.cast_from_spec(
                        file_raw, data_offset, specification, casts[1:], None, data_offset_actual
                    )
                else:
                    result = None
        else:
            raise ValueError(f"Unknown cast type: {casts[0][0]}")

        return result

