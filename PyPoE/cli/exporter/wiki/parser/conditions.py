"""
Wiki condition class.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/conditions.py                    |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Wiki condition class for conditional output in wiki templates.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

import contextlib
from typing import Any

from PyPoE.cli.exporter.wiki.parser.utils import find_template, format_result_rows

# =============================================================================
# Globals
# =============================================================================

__all__ = ["WikiCondition"]

# =============================================================================
# Classes
# =============================================================================


class WikiCondition:
    """
    Base class for wiki condition handlers.

    Handles conditional output in wiki templates by finding and processing
    template arguments from wiki pages.

    Attributes:
        COPY_KEYS: Tuple of keys to copy from template arguments
        COPY_MATCH: Regex pattern for matching keys to copy
        NAME: Template name (must be set by subclasses)
        MATCH: Alternative template name to match (optional)
        INDENT: Number of spaces for indentation (default: 33)
        ADD_INCLUDE: Whether to add <onlyinclude> tags (default: False)
        data: Data dictionary for template output
        cmdargs: Command-line arguments
        handler: Custom handler function (optional)
        template_arguments: Parsed template arguments (cached)
    """

    COPY_KEYS = ()
    COPY_MATCH = None

    NAME = NotImplemented
    MATCH = None
    INDENT = 33
    ADD_INCLUDE = False

    def __init__(self, data: dict[str, Any], cmdargs: Any, handler: Any = None) -> None:
        """
        Initialize WikiCondition.

        Args:
            data: Data dictionary for template output
            cmdargs: Command-line arguments
            handler: Custom handler function (default: uses _handler)
        """
        self.data = data
        self.cmdargs = cmdargs
        if handler is None:
            self.handler = self._handler
        self.template_arguments = None

    def __call__(self, *args: Any, **kwargs: Any) -> str | bool:
        """
        Process wiki condition when called.

        Can be used as both a condition checker (returns bool) and a text
        formatter (returns str) depending on whether page is provided.

        Args:
            *args: Positional arguments (unused)
            **kwargs: Keyword arguments, may include:
                - page: Wiki page object (optional)

        Returns:
            bool: If page is provided and template found, returns True/False
            str: If page is provided and template found, returns formatted text
            str: If page is not provided, returns formatted text
        """
        page = kwargs.get("page")

        if page is not None:
            # Abuse this so it can be called as "text" and "condition"
            if self.template_arguments is None:
                self.template_arguments = find_template(page.text(), self.MATCH or self.NAME)
                if len(self.template_arguments["texts"]) == 1:
                    self.template_arguments = None
                    return False

                return True

            k: str
            for k in self.COPY_KEYS:
                with contextlib.suppress(KeyError):
                    self.data[k] = self.template_arguments["kwargs"][k]

            if self.COPY_MATCH:
                for k, v in self.template_arguments["kwargs"].items():
                    if self.COPY_MATCH.match(k):
                        self.data[k] = v

            prefix = ""
            if self.ADD_INCLUDE and "<onlyinclude></onlyinclude>" not in page.text():
                prefix = "<onlyinclude></onlyinclude>"

            return self.handler(
                prefix
                + self.template_arguments["texts"][0]
                + self._get_text()
                + "".join(self.template_arguments["texts"][1:])
            )
        else:
            return self.handler(self._get_text())

    def _handler(self, text: str) -> str:
        """
        Default handler that returns text unchanged.

        Args:
            text: Text to process

        Returns:
            Text unchanged
        """
        return text

    def _get_text(self) -> str:
        """
        Get formatted text for template output.

        Returns:
            Formatted string using format_result_rows
        """
        return format_result_rows(
            parsed_args=self.cmdargs,
            template_name=self.NAME,
            indent=self.INDENT,
            ordered_dict=self.data,
        )


# =============================================================================
# Functions
# =============================================================================
