"""
Base Command interface for CLI commands.

This module provides the base Command interface following the Command Pattern.
"""

from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    """
    Base interface for CLI commands.

    This follows the Command Pattern, encapsulating a request as an object,
    allowing for parameterization, queuing, logging, and undo operations.

    Example::

        class ExportDatCommand(Command):
            def __init__(self, handler: DatExportHandler):
                self._handler = handler

            def validate(self, args: Any) -> bool:
                return hasattr(args, 'files') and args.files

            def execute(self, args: Any) -> int:
                if not self.validate(args):
                    return 1
                self._handler.handle(args)
                return 0
    """

    @abstractmethod
    def execute(self, args: Any) -> int:
        """
        Execute the command.

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass

    @abstractmethod
    def validate(self, args: Any) -> bool:
        """
        Validate command arguments.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if arguments are valid, False otherwise
        """
        pass

    def get_description(self) -> str:
        """
        Get command description.

        Returns:
            Command description string
        """
        return self.__class__.__name__

