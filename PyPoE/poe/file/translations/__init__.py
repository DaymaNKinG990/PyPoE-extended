"""
Utilities for accessing Path of Exile's translation file format.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/__init__.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utilities for parsing and using GGG translations.

The translations GGG provides are generally suffixed by _descriptions.txt and
can be found in the MetaData/StatDescriptions/ folder.

This module has been refactored into a package structure for future
modularization. Currently, all functionality is re-exported from core.py
for backward compatibility.

Future structure (planned):
- warnings.py: Warning classes
- models.py: Translation models
- quantifiers.py: Quantifier handlers
- results.py: Result classes
- file.py: File and cache classes

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Re-export everything from core for backward compatibility
# =============================================================================

from PyPoE.poe.file.translations.core import (
    # Warning classes
    TranslationWarning,
    MissingIdentifierWarning,
    UnknownIdentifierWarning,
    DuplicateIdentifierWarning,
    # Mixin
    TranslationReprMixin,
    # Core classes
    Translation,
    TranslationLanguage,
    TranslationString,
    TranslationRange,
    TranslationQuantifierHandler,
    TranslationQuantifier,
    TQReminderString,
    TranslationResult,
    TranslationReverseResult,
    TranslationFile,
    TranslationFileCache,
    # Helper functions
    get_custom_translation_file,
    set_custom_translation_file,
    install_data_dependant_quantifiers,
)

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Warning classes
    'TranslationWarning',
    'MissingIdentifierWarning',
    'UnknownIdentifierWarning',
    'DuplicateIdentifierWarning',
    # Mixin
    'TranslationReprMixin',
    # Core classes
    'Translation',
    'TranslationLanguage',
    'TranslationString',
    'TranslationRange',
    'TranslationQuantifierHandler',
    'TranslationQuantifier',
    'TQReminderString',
    'TranslationResult',
    'TranslationReverseResult',
    'TranslationFile',
    'TranslationFileCache',
    # Helper functions
    'get_custom_translation_file',
    'set_custom_translation_file',
    'install_data_dependant_quantifiers',
]

