"""
Export Wiki command implementation.

This module provides the ExportWikiCommand class following the Command Pattern.
"""

from typing import Any

from PyPoE.cli.commands.base import Command
from PyPoE.cli.exporter.wiki.handler import WikiHandler


class ExportWikiCommand(Command):
    """
    Command for exporting to wiki.

    Encapsulates the wiki export operation as a command object.
    """

    def __init__(self, handler: WikiHandler | None = None) -> None:
        """
        Initialize ExportWikiCommand.

        Args:
            handler: WikiHandler instance (created if None)
        """
        self._handler = handler if handler is not None else WikiHandler()

    def validate(self, args: Any) -> bool:
        """
        Validate export wiki command arguments.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if arguments are valid, False otherwise
        """
        # Wiki export validation depends on specific parser requirements
        # This is a basic check - specific parsers may have additional requirements
        return hasattr(args, "parser") and bool(args.parser)

    def execute(self, args: Any) -> int:
        """
        Execute wiki export command.

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
            from PyPoE.cli.core import console

            console.print(f"[red]Error executing wiki export: {e}[/red]")
            return 1

    def get_description(self) -> str:
        """Get command description."""
        return "Export data to wiki format"

