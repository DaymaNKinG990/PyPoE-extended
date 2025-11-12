"""
DAT File Handler for Chain of Responsibility pattern.

This module provides DatFileHandler for processing DAT files.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.shared import AbstractFileReadOnly

from PyPoE.poe.file.handlers.base import FileHandler


class DatFileHandler(FileHandler):
    """
    Handler for DAT files.

    Processes DAT files by ensuring they are read and indexed.
    """

    def can_handle(self, file: "AbstractFileReadOnly") -> bool:
        """
        Check if file is a DatFile.

        Args:
            file: File to check

        Returns:
            True if file is DatFile, False otherwise
        """
        from PyPoE.poe.file.dat import DatFile

        return isinstance(file, DatFile)

    def handle(self, file: "AbstractFileReadOnly") -> None:
        """
        Process DAT file by ensuring it's read and indexed.

        Args:
            file: DatFile to process
        """
        if self.can_handle(file):
            # Type narrowing for MyPy
            from PyPoE.poe.file.dat import DatFile

            if isinstance(file, DatFile):
                # Ensure file is read (if not already)
                if file.reader is None:
                    # File needs to be read first - this is a no-op handler
                    # Actual reading should be done before processing
                    pass
                # Build index if auto_build_index is enabled
                elif hasattr(file.reader, "auto_build_index") and file.reader.auto_build_index:
                    if not hasattr(file.reader, "index") or not file.reader.index:
                        file.reader.indexer.build_index(file.reader.table_data, file.reader.specification)
        else:
            self._next(file)

