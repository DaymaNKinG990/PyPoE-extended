"""
DatFile class for representing DAT files.

This module contains the DatFile class which is the main interface for
working with DAT files.
"""

from typing import Any, BinaryIO

from PyPoE.poe.file.shared import AbstractFileReadOnly
from PyPoE.poe.file.dat.reader import DatReader


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

    def __init__(self, file_name: str) -> None:
        """
        Parameters
        ----------
        file_name : str
            Name of the .dat file
        """
        self._file_name: str = file_name
        self.reader: DatReader | None = None

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
        self.reader = DatReader(self._file_name, **kwargs)
        self.reader.read(buffer.read())

        return self.reader

