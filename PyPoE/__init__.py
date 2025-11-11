"""
Library init

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/__init__.py                                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Library Init

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
import platform
import warnings

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "APP_DIR",
    "DIR",
    "DATA_DIR",
]
__version__ = "1.0.0a0"

# =============================================================================
# Functions
# =============================================================================


def _get_app_dir():
    osys = platform.system()
    if osys == "Windows":
        vars = ["APPDATA"]
        subdir = "PyPoE"
    elif osys == "Linux":
        vars = ["HOME", "PWD"]
        subdir = ".PyPoE"
    else:
        raise RuntimeError("Unsupported Operating System")

    dir = None
    from PyPoE.shared.file_utils import directory_exists, ensure_directory

    for var in vars:
        if var not in os.environ:
            continue
        dir = os.environ[var]
        if not directory_exists(dir):
            continue
        break

    if dir is None:
        raise RuntimeError("Home/user directory not found")

    dir = os.path.join(dir, subdir)
    ensure_directory(dir)

    return dir


# =============================================================================
# Init
# =============================================================================

warnings.simplefilter("default", DeprecationWarning)
APP_DIR = _get_app_dir()
DIR = os.path.join(os.path.dirname(__file__))
DATA_DIR = os.path.join(DIR, "_data")
