"""
Base File Handler for Chain of Responsibility pattern.

This module provides the base FileHandler class for processing files
through a chain of handlers.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.shared import AbstractFileReadOnly


class FileHandler(ABC):
    """
    Base handler for files in Chain of Responsibility pattern.

    Each handler in the chain can process a file or pass it to the next handler.
    This allows for flexible and extensible file processing.

    Example::

        class GGPKFileHandler(FileHandler):
            def can_handle(self, file: AbstractFileReadOnly) -> bool:
                return isinstance(file, GGPKFile)

            def handle(self, file: AbstractFileReadOnly) -> None:
                if self.can_handle(file):
                    file.directory_build()
                else:
                    self._next(file)
    """

    def __init__(self) -> None:
        """Initialize FileHandler."""
        self._next_handler: FileHandler | None = None

    def set_next(self, handler: "FileHandler") -> "FileHandler":
        """
        Set the next handler in the chain.

        Args:
            handler: Next FileHandler in the chain

        Returns:
            The handler that was set (for method chaining)
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def can_handle(self, file: "AbstractFileReadOnly") -> bool:
        """
        Check if this handler can process the file.

        Args:
            file: File to check

        Returns:
            True if this handler can process the file, False otherwise
        """
        pass

    @abstractmethod
    def handle(self, file: "AbstractFileReadOnly") -> None:
        """
        Process the file or pass it to the next handler.

        Args:
            file: File to process
        """
        pass

    def _next(self, file: "AbstractFileReadOnly") -> None:
        """
        Pass file to the next handler in the chain.

        Args:
            file: File to pass to next handler
        """
        if self._next_handler:
            self._next_handler.handle(file)

