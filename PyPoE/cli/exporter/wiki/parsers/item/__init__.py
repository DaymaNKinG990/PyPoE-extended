"""
Wiki items exporter

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/item/__init__.py                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Items exporter for Path of Exile wiki.

This module has been refactored into submodules for better organization:
- base.py: WikiCondition classes and helper functions
- handler.py: ItemsHandler for CLI
- prophecy.py: ProphecyParser
- parser.py: ItemsParser (main parser with 47 methods)

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports - Maintain backward compatibility
# =============================================================================

from PyPoE.cli.exporter.wiki.parsers.item.base import (
    ItemWikiCondition,
    MapItemWikiCondition,
    ProphecyWikiCondition,
    UniqueMapItemWikiCondition,
    # Classes
    WikiCondition,
    # Helper functions
    _apply_column_map,
    _simple_conflict_factory,
    _type_factory,
)
from PyPoE.cli.exporter.wiki.parsers.item.handler import ItemsHandler
from PyPoE.cli.exporter.wiki.parsers.item.parser import ItemsParser
from PyPoE.cli.exporter.wiki.parsers.item.prophecy import ProphecyParser

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Helper functions
    "_apply_column_map",
    "_type_factory",
    "_simple_conflict_factory",
    # WikiCondition classes
    "WikiCondition",
    "ItemWikiCondition",
    "MapItemWikiCondition",
    "UniqueMapItemWikiCondition",
    "ProphecyWikiCondition",
    # Main classes
    "ItemsHandler",
    "ProphecyParser",
    "ItemsParser",
]
