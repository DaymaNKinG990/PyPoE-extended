"""
Translation result models.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/results.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Result models for translation operations including TranslationResult
and TranslationReverseResult classes.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================


from PyPoE.poe.file.translations.models import (
    Translation,
    TranslationReprMixin,
    TranslationString,
)

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "TranslationResult",
    "TranslationReverseResult",
]

# =============================================================================
# Classes
# =============================================================================


class TranslationResult(TranslationReprMixin):
    """
    Translation result of :meth:`TranslationFile:get_translation`.

    Attributes
    ----------
    found
        List of found :class:`Translation` instances (in order)
    found_lines
        List of related translated strings (in order)L
    lines
        List of translated strings (minus missing ones)
    missing_ids
        List of missing identifier tags
    missing_values
        List of missing identifier values
    partial
        List of partial matches of translation tags (in order)
    values
        List of values (in order)
    values_unused
        List of unused values
    values_parsed
        List of parsed values (i.e. with quantifier applied)
    source_ids
        List of the original tags passed before the translation occurred
    source_values
        List of the original values passed before the translation occurred
    extra_strings
        List of dictionary containing extra strings returned.
        The key is the quantifier id used and the value is the string returned.
    """

    __slots__ = [
        "found",
        "found_lines",
        "lines",
        "missing_ids",
        "missing_values",
        "partial",
        "values",
        "values_unused",
        "values_parsed",
        "source_ids",
        "source_values",
        "extra_strings",
        "string_instances",
    ]

    def __init__(
        self,
        found,
        found_lines,
        lines,
        missing,
        missing_values,
        partial,
        values,
        unused,
        values_parsed,
        source_ids,
        source_values,
        extra_strings,
        string_instances,
    ):
        self.found: list[Translation] = found
        self.found_lines: list[str] = found_lines
        self.lines: list[str] = lines
        self.missing_ids: list[str] = missing
        self.missing_values: list[int] = missing_values
        self.partial: list[Translation] = partial
        self.values: list[int] = values
        self.values_unused: list[int] = unused
        self.values_parsed: list[str] = values_parsed
        self.source_ids: list[str] = source_ids
        self.source_values: list[int] | list[tuple[int, int]] = source_values
        self.extra_strings: list[dict[str, str]] = extra_strings
        self.string_instances: list[TranslationString] = string_instances

    def _get_found_ids(self) -> list[list[str]]:
        """
        Generates a list of found ids and returns it.

        Returns
        -------
        list[list[str]]
            List of found ids
        """
        return [tr.ids for tr in self.found]

    found_ids = property(fget=_get_found_ids)

    @property
    def missing(self):
        """
        Zips :attr:`missing_ids` and :attr:`missing_values`.

        Returns
        -------
        zip
        """
        return zip(self.missing_ids, self.missing_values)


class TranslationReverseResult(TranslationReprMixin):
    """
    Result of :meth:`TranslationFile.reverse_translation`

    Attributes
    ----------
    translations
        List of :class:`Translation` instances
    values
        List of values
    """

    __slots__ = [
        "translations",
        "values",
    ]

    def __init__(
        self, translations: list[Translation], values: list[int | float] | list[list[int]]
    ):
        self.translations: list[Translation] = translations
        self.values: list[int | float] | list[list[int]] = values
