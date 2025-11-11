"""
Translation utility functions.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/utils.py                            |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utility functions for translation file handling including custom translation
file management and data-dependent quantifier installation.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================


from PyPoE.poe.file.translations.constants import CUSTOM_TRANSLATION_FILE
from PyPoE.poe.file.translations.file import TranslationFile
from PyPoE.poe.file.translations.models import TQReminderString

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "get_custom_translation_file",
    "set_custom_translation_file",
    "custom_translation_file",
    "install_data_dependant_quantifiers",
]

_custom_translation_file = None

# =============================================================================
# Functions
# =============================================================================


def get_custom_translation_file() -> TranslationFile:
    """
    Returns the custom translation file.

    If no custom file has been set, it will attempt to load the default
    custom translation file.

    Returns
    -------
    TranslationFile
        The custom translation file instance
    """
    global _custom_translation_file
    if _custom_translation_file is None:
        _custom_translation_file = TranslationFile()
        _custom_translation_file.read(CUSTOM_TRANSLATION_FILE)
    return _custom_translation_file


def set_custom_translation_file(file: str | None = None):
    """
    Sets the custom translation file.

    Parameters
    ----------
    file : str or None
        Path to the custom translation file. If None, resets to default.
    """
    global _custom_translation_file
    if file is None:
        _custom_translation_file = None
    else:
        _custom_translation_file = TranslationFile()
        _custom_translation_file.read(file)


# Alias for backward compatibility
custom_translation_file = get_custom_translation_file


def install_data_dependant_quantifiers(relational_reader):
    """
    Installs data-dependent quantifiers that require access to game data files.

    Parameters
    ----------
    relational_reader
        Relational reader instance providing access to game data
    """
    TQReminderString(relational_reader)
