"""
Bundle File Handler for Chain of Responsibility pattern.

This module provides BundleHandler for processing Bundle files.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.shared import AbstractFileReadOnly

from PyPoE.poe.file.handlers.base import FileHandler


class BundleHandler(FileHandler):
    """
    Handler for Bundle files.

    Processes Bundle files by extracting their contents.
    """

    def can_handle(self, file: "AbstractFileReadOnly") -> bool:
        """
        Check if file is a Bundle.

        Args:
            file: File to check

        Returns:
            True if file is Bundle, False otherwise
        """
        from PyPoE.poe.file.bundle import Bundle

        return isinstance(file, Bundle)

    def handle(self, file: "AbstractFileReadOnly") -> None:
        """
        Process Bundle file.

        Args:
            file: Bundle to process
        """
        if self.can_handle(file):
            # Type narrowing for MyPy
            from PyPoE.poe.file.bundle import Bundle

            if isinstance(file, Bundle):
                # Bundle files are typically already processed when read
                # This handler can be extended for additional processing
                pass
        else:
            self._next(file)

