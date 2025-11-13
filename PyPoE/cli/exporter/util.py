"""
Utility functions for exporters

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/util.py                                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utility functions for exporters.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re

from PyPoE.cli.config import SetupError
from PyPoE.cli.exporter import config

# self
from PyPoE.poe.path import PoEPath

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "get_content_path",
    "fix_path",
]

# =============================================================================
# Functions
# =============================================================================


def get_content_path() -> str:
    """
    Get path to the current content.ggpk based on config variables.

    Uses version and distributor from config, or falls back to auto-detection
    via PoEPath if ggpk_path is not set.

    Returns:
        Path to the content.ggpk file

    Raises:
        SetupError: If no valid path was found
    """
    path = config.get_option("ggpk_path")
    if path == "":
        args = config.get_option("version"), config.get_option("distributor")
        paths = PoEPath(*args).get_installation_paths()

        if not paths:
            raise SetupError("No PoE Installation found.")

        return paths[0]
    else:
        return path


def fix_path(path: str) -> str:
    """
    Fix Windows path format for use in file systems that don't support colons.

    Replaces colons in Windows absolute paths (e.g., "C:") with underscores
    after the drive letter.

    Args:
        path: Path string to fix

    Returns:
        Fixed path string with colons replaced by underscores (except drive letter)
    """
    if re.match("[a-zA-Z]:.*", path):
        return path[:2] + re.sub(r":", "_", path[2:])
    else:
        return path
