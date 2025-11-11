"""
Utilities for accessing Path of Exile's translation file format.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/__init__.py                         |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utilities for parsing and using GGG translations.

The translation GGG provides are generally suffixed by _descriptions.txt and
can be found in the MetaData/StatDescriptions/ folder.

This module provides backward compatibility by re-exporting all public APIs
from the new modular structure.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Import all public APIs from submodules for backward compatibility
from PyPoE.poe.file.translations.cache import TranslationFileCache
from PyPoE.poe.file.translations.constants import (
    CUSTOM_TRANSLATION_FILE,
    regex_id_strings,
    regex_ids,
    regex_int,
    regex_isnumber,
    regex_lang,
    regex_strings,
    regex_tokens,
    regex_translation_string,
)
from PyPoE.poe.file.translations.exceptions import (
    DuplicateIdentifierWarning,
    MissingIdentifierWarning,
    TranslationWarning,
    UnknownIdentifierWarning,
)
from PyPoE.poe.file.translations.file import TranslationFile
from PyPoE.poe.file.translations.models import (
    TQReminderString,
    Translation,
    TranslationLanguage,
    TranslationQuantifier,
    TranslationQuantifierHandler,
    TranslationRange,
    TranslationReprMixin,
    TranslationString,
)
from PyPoE.poe.file.translations.results import (
    TranslationResult,
    TranslationReverseResult,
)
from PyPoE.poe.file.translations.utils import (
    custom_translation_file,
    get_custom_translation_file,
    install_data_dependant_quantifiers,
    set_custom_translation_file,
)

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    # Exceptions
    "TranslationWarning",
    "MissingIdentifierWarning",
    "UnknownIdentifierWarning",
    "DuplicateIdentifierWarning",
    # Constants
    "CUSTOM_TRANSLATION_FILE",
    "regex_translation_string",
    "regex_ids",
    "regex_id_strings",
    "regex_strings",
    "regex_int",
    "regex_isnumber",
    "regex_lang",
    "regex_tokens",
    # Models
    "TranslationReprMixin",
    "Translation",
    "TranslationLanguage",
    "TranslationString",
    "TranslationRange",
    "TranslationQuantifierHandler",
    "TranslationQuantifier",
    "TQReminderString",
    # Results
    "TranslationResult",
    "TranslationReverseResult",
    # File handlers
    "TranslationFile",
    "TranslationFileCache",
    # Utilities
    "get_custom_translation_file",
    "set_custom_translation_file",
    "custom_translation_file",
    "install_data_dependant_quantifiers",
]
