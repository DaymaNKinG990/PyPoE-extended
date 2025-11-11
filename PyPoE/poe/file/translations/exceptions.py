"""
Warning classes for translation file parsing.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/exceptions.py                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Warning classes raised during translation file parsing and processing.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

from PyPoE.poe.file.shared import ParserWarning

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    'TranslationWarning',
    'MissingIdentifierWarning',
    'UnknownIdentifierWarning',
    'DuplicateIdentifierWarning',
]

# =============================================================================
# Warning Classes
# =============================================================================


class TranslationWarning(ParserWarning):
    """Base warning class for translation-related warnings."""
    pass


class MissingIdentifierWarning(TranslationWarning):
    """Warning raised when a required identifier is missing."""
    pass


class UnknownIdentifierWarning(TranslationWarning):
    """Warning raised when an unknown identifier is encountered."""
    pass


class DuplicateIdentifierWarning(TranslationWarning):
    """Warning raised when a duplicate identifier is found."""
    pass

