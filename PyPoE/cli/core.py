"""
CLI Core

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/core.py                                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

CLI core utility classes and functions.

Agreement
===============================================================================

See PyPoE/LICENSE

TODO-List
===============================================================================

- Virtual Terminal?
- console output formatting/linebreaks

Documentation
===============================================================================

Classes
-------------------------------------------------------------------------------

.. autoclass:: Msg

.. autoclass:: OutputHook

Functions
-------------------------------------------------------------------------------

.. autofunction:: run

.. autofunction:: console
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import sys
import traceback
import warnings
from enum import Enum
from time import strftime
from typing import Any

# 3rd Party
from rich.console import Console

# Rich console instance
_console = Console()

# =============================================================================
# Globals
# =============================================================================

__all__ = ["Msg", "OutputHook", "run", "console"]

# =============================================================================
# Classes
# =============================================================================


class Msg(Enum):
    """
    Message types for console output.

    Used for :py:func:`console` function to specify message styling.

    Attributes:
        default: Default message style (no special formatting)
        warning: Yellow warning message style
        error: Red error message style
    """

    default = ""
    error = "bold red"
    warning = "bold yellow"


class OutputHook:
    """
    Warning hook to reformat / restyle warning messages properly.

    Intercepts Python warnings and formats them using the console function
    with appropriate styling.
    """

    def __init__(self, show_warning: Any) -> None:
        """
        Initialize output hook.

        Args:
            show_warning: Original show_warning function to preserve
        """
        self._orig_show_warning = show_warning
        self._orig_format_warning = warnings.formatwarning
        warnings.formatwarning = self.format_warning
        warnings.showwarning = self.show_warning

    def format_warning(
        self, message: str, category: type[Warning], filename: str, lineno: int, line: str | None = None
    ) -> str:
        """
        Format warning message with styling.

        Args:
            message: Warning message text
            category: Warning category class
            filename: Source filename
            lineno: Line number
            line: Source line (optional)

        Returns:
            Formatted warning message string
        """
        kwargs = {
            "message": message,
            "category": category.__name__,
            "filename": filename,
            "lineno": lineno,
            "line": line,
        }
        f = "{filename}:{lineno}:\n{category}: {message}\n".format(**kwargs)
        return console(f, msg=Msg.warning, rtr=True)

    def show_warning(self, *args: Any, **kwargs: Any) -> None:
        """
        Show warning using original function.

        Args:
            *args: Positional arguments for show_warning
            **kwargs: Keyword arguments for show_warning
        """
        self._orig_show_warning(*args, **kwargs)


# =============================================================================
# Functions
# =============================================================================


def run(parser: Any, config: Any) -> None:
    """
    Run the CLI application with the given parser and config.

    It will take care of handling parsing the arguments and calling the
    appropriate function and print any tracebacks that occurred during the call.

    Saves config and exits the python client.

    Warning:
        This function will exit the python client on completion

    Args:
        parser: Assembled argument parser for argument handling
        config: Config object to use for the CLI application wide config
    """
    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            code = args.func(args)
        except Exception:
            console(traceback.format_exc(), msg=Msg.error)
            code = -1
    else:
        parser.print_help()
        code = 0

    config.validate(config.validator)
    config.write()
    sys.exit(code)


def console(message: str, msg: Msg = Msg.default, rtr: bool = False, raw: bool = False) -> str | None:
    """
    Send the specified message to console.

    Formats and prints (or returns) a message with optional styling and timestamp.

    Args:
        message: Message to send
        msg: Message type for styling (default: Msg.default)
        rtr: Return message instead of printing (default: False)
        raw: Skip timestamp/colour formatting (default: False)

    Returns:
        Formatted message string if rtr is True, None otherwise
    """
    if raw:
        f = message
    else:
        timestamp = strftime("%X ")
        f = f"[{msg.value}]{timestamp}{message}[/]" if msg.value else f"{timestamp}{message}"
    if rtr:
        return f
    else:
        _console.print(f, markup=True, highlight=False)
