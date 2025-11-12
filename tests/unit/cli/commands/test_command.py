"""
Unit tests for Command Pattern implementation.
"""

from unittest.mock import MagicMock

import pytest

from PyPoE.cli.commands.base import Command
from PyPoE.cli.commands.export_dat import ExportDatCommand
from PyPoE.cli.commands.export_wiki import ExportWikiCommand
from PyPoE.cli.commands.invoker import CommandInvoker


class TestCommand:
    """Test cases for base Command interface."""

    def test_command_interface(self):
        """Test that Command is an abstract base class."""
        with pytest.raises(TypeError):
            Command()  # type: ignore[abstract]


class TestExportDatCommand:
    """Test cases for ExportDatCommand."""

    def test_validate_with_files(self):
        """Test validation with files argument."""
        command = ExportDatCommand()
        args = MagicMock()
        args.files = ["file1.dat", "file2.dat"]

        assert command.validate(args) is True

    def test_validate_without_files(self):
        """Test validation without files argument."""
        command = ExportDatCommand()
        args = MagicMock()
        args.files = []

        assert command.validate(args) is False

    def test_execute_success(self):
        """Test successful command execution."""
        handler = MagicMock()
        command = ExportDatCommand(handler)
        args = MagicMock()
        args.files = ["file1.dat"]

        exit_code = command.execute(args)

        assert exit_code == 0
        handler.handle.assert_called_once_with(args)

    def test_execute_validation_failure(self):
        """Test command execution with validation failure."""
        handler = MagicMock()
        command = ExportDatCommand(handler)
        args = MagicMock()
        args.files = []

        exit_code = command.execute(args)

        assert exit_code == 1
        handler.handle.assert_not_called()

    def test_execute_exception(self):
        """Test command execution with exception."""
        handler = MagicMock()
        handler.handle.side_effect = Exception("Test error")
        command = ExportDatCommand(handler)
        args = MagicMock()
        args.files = ["file1.dat"]

        exit_code = command.execute(args)

        assert exit_code == 1


class TestExportWikiCommand:
    """Test cases for ExportWikiCommand."""

    def test_validate_with_parser(self):
        """Test validation with parser argument."""
        command = ExportWikiCommand()
        args = MagicMock()
        args.parser = "items"

        assert command.validate(args) is True

    def test_validate_without_parser(self):
        """Test validation without parser argument."""
        command = ExportWikiCommand()
        args = MagicMock()
        args.parser = None

        assert command.validate(args) is False


class TestCommandInvoker:
    """Test cases for CommandInvoker."""

    def test_execute_command(self):
        """Test executing a command through invoker."""
        invoker = CommandInvoker()
        command = MagicMock(spec=Command)
        command.execute.return_value = 0
        args = MagicMock()

        exit_code = invoker.execute(command, args)

        assert exit_code == 0
        command.execute.assert_called_once_with(args)

    def test_execute_with_history(self):
        """Test executing command with history enabled."""
        invoker = CommandInvoker(enable_history=True)
        command = MagicMock(spec=Command)
        command.execute.return_value = 0
        args = MagicMock()

        invoker.execute(command, args)

        history = invoker.get_history()
        assert len(history) == 1
        assert history[0] == (command, args)

    def test_execute_failed_command_no_history(self):
        """Test that failed commands are not added to history."""
        invoker = CommandInvoker(enable_history=True)
        command = MagicMock(spec=Command)
        command.execute.return_value = 1
        args = MagicMock()

        invoker.execute(command, args)

        history = invoker.get_history()
        assert len(history) == 0

    def test_clear_history(self):
        """Test clearing command history."""
        invoker = CommandInvoker(enable_history=True)
        command = MagicMock(spec=Command)
        command.execute.return_value = 0
        args = MagicMock()

        invoker.execute(command, args)
        invoker.clear_history()

        history = invoker.get_history()
        assert len(history) == 0

