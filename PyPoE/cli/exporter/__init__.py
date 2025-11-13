"""
GGPK User Interface Classes

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/__init__.py                                   |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Creates a qt User Interface to browse GGPK files.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
import warnings

# self
from PyPoE import APP_DIR
from PyPoE.cli.config import ConfigHelper
from PyPoE.cli.core import OutputHook

# =============================================================================
# Globals
# =============================================================================

__all__ = ["CONFIG_PATH", "config"]

CONFIG_PATH = os.path.join(APP_DIR, "exporter.conf")

# Create config file if it doesn't exist
if not os.path.exists(CONFIG_PATH):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    # Create empty config file
    with open(CONFIG_PATH, "w") as f:
        f.write("")

config = ConfigHelper(infile=CONFIG_PATH)

# =============================================================================
# Init
# =============================================================================

OutputHook(warnings.showwarning)
