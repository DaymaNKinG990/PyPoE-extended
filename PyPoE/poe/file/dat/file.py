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

    Attributes
    ----------
    reader : DatReader
        reference to the DatReader instance once :meth:`read` has been called
    """

    def __init__(self, file_name: str | None = None) -> None:
        """
        Parameters
        ----------
        file_name : str, optional
            Name of the .dat file (can be set later)
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
        return f'DatFile<{hex(id(self))}>(file_name="{self._file_name}")'

    def _read(self, buffer: BinaryIO, *args: Any, **kwargs: Any) -> DatReader:
        """
        Read DAT file from buffer.

        Args:
            buffer: Binary file buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments (passed to DatReader)

        Returns:
            DatReader instance
        """
        # Use builder parameters if set, otherwise use kwargs
        if self._builder_caster is not None or self._builder_parser is not None or self._builder_indexer is not None:
            from PyPoE.poe.file.dat.caster import DatCaster
            from PyPoE.poe.file.dat.indexer import DatIndexer
            from PyPoE.poe.file.dat.parser import DatParser

            caster = self._builder_caster if self._builder_caster is not None else DatCaster(
                use_dat_value=self._builder_use_dat_value, x64=self._builder_x64
            )
            parser = self._builder_parser if self._builder_parser is not None else DatParser()
            indexer = self._builder_indexer if self._builder_indexer is not None else DatIndexer()

            # Get specification from kwargs or use default
            specification = kwargs.get("specification")
            if specification is None:
                raise ValueError("specification is required for DatReader")

            self.reader = DatReader(
                self._file_name or "",
                specification=specification,
                caster=caster,
                parser=parser,
                indexer=indexer,
                use_dat_value=self._builder_use_dat_value,
                x64=self._builder_x64,
            )
        else:
            # Default behavior (backward compatible)
            self.reader = DatReader(self._file_name or "", **kwargs)

        self.reader.read(buffer.read())

        return self.reader

