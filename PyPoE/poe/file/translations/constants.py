"""
Constants and regex patterns for translation file parsing.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/constants.py                        |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Regular expressions and global constants used for parsing translation files.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

import os
import re

from PyPoE import DATA_DIR

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    'CUSTOM_TRANSLATION_FILE',
    'regex_translation_string',
    'regex_ids',
    'regex_id_strings',
    'regex_strings',
    'regex_int',
    'regex_isnumber',
    'regex_lang',
    'regex_tokens',
]

# =============================================================================
# Constants
# =============================================================================

CUSTOM_TRANSLATION_FILE = os.path.join(DATA_DIR, 'custom_descriptions.txt')

# =============================================================================
# Regex Patterns
# =============================================================================

regex_translation_string = re.compile(
    r'^'
    r'[\s]*'
    r'(?P<minmax>(?:[0-9\-\|#!]+[ \t]+)+)'
    r'"(?P<description>.*\s*)"'
    r'(?P<quantifier>(?:[ \t]*[\w%]+)*)'
    r'[ \t]*[\r\n]*'
    r'$',
    re.UNICODE | re.MULTILINE
)

regex_ids = re.compile(r'\S+.*(?!\s[0-9]+)', re.UNICODE | re.MULTILINE)
regex_id_strings = re.compile(r'([\S]+)', re.UNICODE)
regex_strings = re.compile(r'(?:"(.+)")|([\S]+)+', re.UNICODE)
regex_int = re.compile(r'[0-9]+', re.UNICODE)
regex_isnumber = re.compile(r'^[0-9\-]+$', re.UNICODE)
regex_lang = re.compile(
    r'^[\s]*lang "(?P<language>[\w ]+)"[\s]*$',
    re.UNICODE | re.MULTILINE
)
regex_tokens = re.compile(
    r'(?:^"(?P<header>.*)"$)'
    r'|(?:^include "(?P<include>.*)")'
    r'|(?:^no_description (?P<no_description>[\w+%]*)$)'
    r'|(?P<description>^description[\s]*(?P<identifier>[\S]*)[\s]*$)',
    re.UNICODE | re.MULTILINE
)

