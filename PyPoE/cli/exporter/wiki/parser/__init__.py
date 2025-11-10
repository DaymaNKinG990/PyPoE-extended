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

This module has been refactored into a package structure with planned future
modularization. Currently, all functionality is re-exported from core.py
for backward compatibility.

Future structure (planned):
- interwiki.py: Inter-wiki linking functionality (_inter_wiki_map)
- base.py: BaseParser class
- tags.py: TagHandler class
- condition.py: WikiCondition class
- utils.py: Utility functions (format_result_rows, find_template, etc.)

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Re-export everything from core for backward compatibility
# =============================================================================

from PyPoE.cli.exporter.wiki.parser.core import (
    # Classes
    BaseParser,
    WikiCondition,
    TagHandler,
    # Functions
    find_template,
    format_result_rows,
    make_inter_wiki_links,
    parse_and_handle_description_tags,
    # Constants
    DEFAULT_INDENT,
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
    'find_template',
    'format_result_rows',
    'make_inter_wiki_links',
    'parse_and_handle_description_tags',
    # Constants
    'DEFAULT_INDENT',
]

