"""
File Processor for Chain of Responsibility pattern.

This module provides FileProcessor for processing files through a chain of handlers.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.handlers.base import FileHandler
    from PyPoE.poe.file.shared import AbstractFileReadOnly

from PyPoE.poe.file.handlers.base import FileHandler


class FileProcessor:
    """
    Processor for files using Chain of Responsibility pattern.

    This class manages a chain of file handlers and processes files through them.

    Example::

        processor = FileProcessor()
        processor.add_handler(GGPKFileHandler())
        processor.add_handler(DatFileHandler())
        processor.add_handler(BundleHandler())

        # Process a file
        ggpk_file = GGPKFile("content.ggpk")
        processor.process(ggpk_file)
    """

    def __init__(self) -> None:
        """Initialize FileProcessor."""
        self._chain: FileHandler | None = None

    def add_handler(self, handler: "FileHandler") -> None:
        """
        Add a handler to the chain.

        Args:
            handler: FileHandler to add to the chain
        """
        if self._chain is None:
            self._chain = handler
        else:
            # Find the last handler in the chain
            current = self._chain
            while current._next_handler is not None:
                current = current._next_handler
            current.set_next(handler)

    def process(self, file: "AbstractFileReadOnly") -> None:
        """
        Process a file through the chain of handlers.

        Args:
            file: File to process
        """
        if self._chain:
            self._chain.handle(file)

    def clear_chain(self) -> None:
        """Clear all handlers from the chain."""
        self._chain = None

