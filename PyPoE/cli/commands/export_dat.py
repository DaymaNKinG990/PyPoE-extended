"""
Export DAT command implementation.

This module provides the ExportDatCommand class following the Command Pattern.
"""

from typing import Any

from PyPoE.cli.commands.base import Command
from PyPoE.cli.exporter.dat.handler import DatExportHandler


class ExportDatCommand(Command):
    """
    Command for exporting DAT files.

    Encapsulates the DAT export operation as a command object.
    """

    def __init__(self, handler: DatExportHandler | None = None) -> None:
        """
        Initialize ExportDatCommand.

        Args:
            handler: DatExportHandler instance (created if None)
        """
        self._handler = handler if handler is not None else DatExportHandler()

    def validate(self, args: Any) -> bool:
        """
        Validate export DAT command arguments.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if arguments are valid, False otherwise
        """
        return hasattr(args, "files") and bool(args.files)

    def execute(self, args: Any) -> int:
        """
        Execute DAT export command.

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if not self.validate(args):
            return 1

        try:
            self._handler.handle(args)
            return 0
        except Exception as e:
            from PyPoE.cli.core import Msg, console

            console(f"Error executing DAT export: {e}", msg=Msg.error)
            return 1

    def get_description(self) -> str:
        """Get command description."""
        return "Export DAT files to various formats"

