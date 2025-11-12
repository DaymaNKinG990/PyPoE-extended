"""
GGPK File Handler for Chain of Responsibility pattern.

This module provides GGPKFileHandler for processing GGPK files.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.shared import AbstractFileReadOnly

from PyPoE.poe.file.handlers.base import FileHandler


class GGPKFileHandler(FileHandler):
    """
    Handler for GGPK files.

    Processes GGPK files by building directory structure.
    """

    def can_handle(self, file: "AbstractFileReadOnly") -> bool:
        """
        Check if file is a GGPKFile.

        Args:
            file: File to check

        Returns:
            True if file is GGPKFile, False otherwise
        """
        from PyPoE.poe.file.ggpk import GGPKFile

        return isinstance(file, GGPKFile)

    def handle(self, file: "AbstractFileReadOnly") -> None:
        """
        Process GGPK file by building directory structure.

        Args:
            file: GGPKFile to process
        """
        if self.can_handle(file):
            # Type narrowing for MyPy
            from PyPoE.poe.file.ggpk import GGPKFile

            if isinstance(file, GGPKFile) and file.directory is None:
                # Build directory structure if not already built
                file.directory_build()
        else:
            self._next(file)

