"""
DatFile class for representing DAT files.

This module contains the DatFile class which is the main interface for
working with DAT files.
"""

from typing import Any, BinaryIO

from PyPoE.poe.file.dat.reader import DatReader
from PyPoE.poe.file.shared import AbstractFileReadOnly


class DatFile(AbstractFileReadOnly):
    """
    Representation of a .dat file.

    This class implements the following Protocol interfaces:
    - IReadable: Provides read() method (inherited from AbstractFileReadOnly)
    - IBufferable: Provides get_read_buffer() method (inherited)
    - IWritable: Provides write() method (supports writing)

    Attributes:
        reader: DatReader instance (set after read() is called)
        _file_name: Name of the DAT file
    """

    def __init__(self, file_name: str | None = None) -> None:
        """
        Initialize DatFile.

        Args:
            file_name: Name of the .dat file (can be set later)
        """
        self._file_name: str | None = file_name
        self.reader: DatReader | None = None
        # Builder parameters (set by DatFileBuilder)
        self._builder_caster = None  # type: ignore[var-annotated]
        self._builder_parser = None  # type: ignore[var-annotated]
        self._builder_indexer = None  # type: ignore[var-annotated]
        self._builder_use_dat_value: bool = True
        self._builder_x64: bool = False

    def __repr__(self) -> str:
        """
        Return string representation of DatFile.

        Returns:
            String representation with file name
        """
        return f'DatFile<{hex(id(self))}>(file_name="{self._file_name}")'

    def _read(self, buffer: BinaryIO, *args: Any, **kwargs: Any) -> DatReader:
        """
        Read DAT file from buffer.

        Args:
            buffer: Binary file buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments (specification is required)

        Returns:
            DatReader instance

        Raises:
            ValueError: If specification is not provided
        """

        # Get specification from kwargs
        specification = kwargs.get("specification")
        if specification is None:
            raise ValueError("specification is required for DatReader")

        # DatReader creates its own components (caster, parser, indexer) internally
        # Builder pattern is not supported for DatReader
        self.reader = DatReader(
            self._file_name or "",
            specification=specification,
            use_dat_value=self._builder_use_dat_value,
            x64=self._builder_x64,
        )

        self.reader.read(buffer.read())

        return self.reader

