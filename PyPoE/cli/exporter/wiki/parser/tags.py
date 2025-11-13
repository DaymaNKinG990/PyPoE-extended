"""
Wiki tag handler class.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/tags.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Tag handler for processing wiki description tags.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

from functools import partial
from typing import Any

from PyPoE.poe.constants import WORDLISTS

# =============================================================================
# Globals
# =============================================================================

__all__ = ["TagHandler"]

# =============================================================================
# Classes
# =============================================================================


class TagHandler:
    """
    Provides tag handlers for use with parse_description_tags.

    Attributes:
        _IL_FORMAT: Format string for item links
        _C_FORMAT: Format string for color tags
        rr: RelationalReader instance for item lookups
        tag_handlers: Dictionary of tag handlers keyed by tag name
    """

    _IL_FORMAT = "{{il|%s|html=}}"
    _C_FORMAT = "{{c|%s|%s}}"

    def __init__(self, rr: Any) -> None:
        """
        Initialize TagHandler with RelationalReader.

        Args:
            rr: RelationalReader instance to use when looking up whether items
                are 'real' for linking purposes
        """
        self.rr = rr
        self.rr["BaseItemTypes.dat"].build_index("Name")
        self.rr["Words.dat"].build_index("Text")

        self.tag_handlers = {}
        for key, func in self.__class__.tag_handlers.items():
            self.tag_handlers[key] = partial(func, self)  # type: ignore[misc, operator, arg-type]

    def _check_link(self, string: str) -> str:
        """
        Check if string should be formatted as a link and format it.

        Args:
            string: String to check and format

        Returns:
            Formatted string with appropriate link formatting
        """
        items = self.rr["BaseItemTypes.dat"].index["Name"][string]
        if items:
            if items[0]["ItemClassesKey"]["Name"] == "Maps":
                string = self._IL_FORMAT % string
            elif len(items) > 1:
                return f"[[{string}]]"
            else:
                string = self._IL_FORMAT % string
        return string

    def _basic_handler(self, hstr: str, parameter: str, tid: str) -> str:
        """
        Basic tag handler that formats string with color tag.

        Args:
            hstr: String to format
            parameter: Parameter (unused)
            tid: Tag ID for color formatting

        Returns:
            Formatted string with color tag
        """
        return self._C_FORMAT % (tid, hstr)

    def _default_handler(self, hstr: str, parameter: str, tid: str) -> str:
        """
        Default tag handler that checks link and formats with color tag.

        Args:
            hstr: String to format
            parameter: Parameter (unused)
            tid: Tag ID for color formatting

        Returns:
            Formatted string with link check and color tag
        """
        return self._C_FORMAT % (tid, self._check_link(hstr))

    def _link_handler(self, hstr: str, parameter: str, tid: str) -> str:
        """
        Link handler that formats string as wiki link with color tag.

        Args:
            hstr: String to format as link
            parameter: Parameter (unused)
            tid: Tag ID for color formatting

        Returns:
            Formatted string with wiki link and color tag
        """
        return self._C_FORMAT % (tid, f"[[{hstr}]]")

    def _unique_handler(self, hstr: str, parameter: str) -> str:
        """
        Unique item handler that formats unique items appropriately.

        Args:
            hstr: String to format
            parameter: Parameter (unused)

        Returns:
            Formatted string with unique item formatting
        """
        words = self.rr["Words.dat"].index["Text"][hstr]
        if words and words[0]["WordlistsKey"] == WORDLISTS.UNIQUE_ITEM:
            # Check whether unique item name clashes with base item name
            items = self.rr["BaseItemTypes.dat"].index["Name"][hstr]
            hstr = f"[[{hstr}]]" if len(items) > 0 else self._IL_FORMAT % hstr
        else:
            hstr = self._check_link(hstr)
        return self._C_FORMAT % ("unique", hstr)

    def _currency_handler(self, hstr: str, parameter: str) -> str:
        """
        Currency handler that formats currency items with quantity support.

        Args:
            hstr: String to format (may contain "x " for quantity)
            parameter: Parameter (unused)

        Returns:
            Formatted string with currency formatting
        """
        if "x " in hstr:
            s = hstr.split("x ", maxsplit=1)
            return self._C_FORMAT % ("currency", f"{s[0]}x {self._check_link(s[1])}")
        else:
            return self._default_handler(hstr, parameter, "currency")

    def _pass_through_handler(self, hstr: str, parameter: str) -> str:
        """
        Pass-through handler that returns string unchanged.

        Args:
            hstr: String to return
            parameter: Parameter (unused)

        Returns:
            Original string unchanged
        """
        return hstr

    tag_handlers = {
        "normal": partial(_default_handler, tid="normal"),
        "default": partial(_default_handler, tid="default"),
        "augmented": partial(_default_handler, tid="augmented"),
        "enchanted": partial(_default_handler, tid="enchanted"),
        "size": _pass_through_handler,
        "smaller": _pass_through_handler,
        "gemitem": partial(_default_handler, tid="gem"),
        "currencyitem": _currency_handler,
        "whiteitem": partial(_default_handler, tid="white"),
        "magicitem": partial(_default_handler, tid="magic"),
        "rareitem": partial(_default_handler, tid="rare"),
        "uniqueitem": _unique_handler,
        "divination": partial(_default_handler, tid="divination"),
        "prophecy": partial(_default_handler, tid="prophecy"),
        "corrupted": partial(_link_handler, tid="corrupted"),
    }
