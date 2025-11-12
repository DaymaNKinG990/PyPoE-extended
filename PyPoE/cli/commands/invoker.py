"""
Command Invoker for executing commands.

This module provides the CommandInvoker class for executing and managing commands.
"""

from typing import Any

from PyPoE.cli.commands.base import Command


class CommandInvoker:
    """
    Invoker for executing commands.

    This class is responsible for executing commands and optionally
    maintaining command history for undo/redo operations.

    Example::

        invoker = CommandInvoker()
        command = ExportDatCommand(handler)
        exit_code = invoker.execute(command, args)
    """

    def __init__(self, enable_history: bool = False) -> None:
        """
        Initialize CommandInvoker.

        Args:
            enable_history: If True, maintain command history for undo/redo
        """
        self._enable_history = enable_history
        self._history: list[tuple[Command, Any]] = []

    def execute(self, command: Command, args: Any) -> int:
        """
        Execute a command.

        Args:
            command: Command instance to execute
            args: Parsed command-line arguments

        Returns:
            Exit code from command execution
        """
        exit_code = command.execute(args)

        if self._enable_history and exit_code == 0:
            self._history.append((command, args))

        return exit_code

    def get_history(self) -> list[tuple[Command, Any]]:
        """
        Get command execution history.

        Returns:
            List of (command, args) tuples
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear command execution history."""
        self._history.clear()

