"""
Wiki Export Handler

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/__init__.py                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Base classes and related functions for Wiki Export Handlers.

This module has been refactored into a modular package structure:
- constants.py: Inter-wiki linking constants (_inter_wiki_map, DEFAULT_INDENT)
- base.py: BaseParser class
- tags.py: TagHandler class
- conditions.py: WikiCondition class
- utils.py: Utility functions (format_result_rows, find_template, etc.)

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Re-export everything from submodules for backward compatibility
# =============================================================================

from PyPoE.cli.exporter.wiki.parser.constants import (
    DEFAULT_INDENT,
    _inter_wiki_map,
)

from PyPoE.cli.exporter.wiki.parser.base import BaseParser

from PyPoE.cli.exporter.wiki.parser.tags import TagHandler

from PyPoE.cli.exporter.wiki.parser.conditions import WikiCondition

from PyPoE.cli.exporter.wiki.parser.utils import (
    _make_inter_wiki_re,
    find_template,
    format_result_rows,
    make_inter_wiki_links,
    parse_and_handle_description_tags,
)

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Classes
    'BaseParser',
    'WikiCondition',
    'TagHandler',
    # Functions
    '_make_inter_wiki_re',
    'find_template',
    'format_result_rows',
    'make_inter_wiki_links',
    'parse_and_handle_description_tags',
    # Constants
    'DEFAULT_INDENT',
    '_inter_wiki_map',
]

