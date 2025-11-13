"""
Translation file reader.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/file.py                             |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Translation file reader implementation.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

from __future__ import annotations

import io
import os
import warnings
from collections.abc import Callable, Iterable
from collections.abc import Iterable as t_Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyPoE.poe.file.translations.cache import TranslationFileCache

import contextlib

from PyPoE.poe.file.shared import AbstractFileReadOnly, ParserError
from PyPoE.poe.file.translations.constants import (
    regex_id_strings,
    regex_ids,
    regex_int,
    regex_isnumber,
    regex_lang,
    regex_tokens,
    regex_translation_string,
)
from PyPoE.poe.file.translations.exceptions import (
    DuplicateIdentifierWarning,
    TranslationWarning,
)
from PyPoE.poe.file.translations.models import (
    Translation,
    TranslationLanguage,
    TranslationRange,
    TranslationString,
)
from PyPoE.poe.file.translations.results import (
    TranslationResult,
    TranslationReverseResult,
)

# =============================================================================
# Globals
# =============================================================================

__all__ = ["TranslationFile"]

# =============================================================================
# Classes
# =============================================================================


class TranslationFile(AbstractFileReadOnly):
    """
    Translation file reader.

    This class implements the following Protocol interfaces:
    - IReadable: Provides read() method (inherited from AbstractFileReadOnly)
    - IBufferable: Provides get_read_buffer() method (inherited)

    Translation files can be found in the following folder in the content.ggpk:

    Metadata/StatDescriptions/xxx_descriptions.txt

    Attributes
    ----------
    translations : list[Translation]
        List of parsed :class:`Translation` instances (in order)
    translations_hash   : dict[str, list[Translation]]
        Mapping of parsed :class:`Translation` instances with their id(s) as
        key.

        Each value is a list of :class:`Translation` instances, even if there
        is only one.
    """

    __slots__ = ["translations", "translations_hash", "_base_dir", "_parent"]

    def __init__(
        self,
        file_path: t_Iterable[str] | str | None = None,
        base_dir: str | None = None,
        parent: TranslationFileCache | None = None,
    ):
        """
        Creates a new TranslationFile instance from the given translation
        file(s).

        file_path can be specified to initialize the file(s) right away. It
        takes the same arguments as :meth:`TranslationFile.read`.

        Some translation files have an "include" tag which includes the
        translation strings of another translation file automatically. By
        default that behaviour is ignored and a warning is raised.
        To enable the automatic include, specify either of the base_dir or
        parent variables.

        .. note::
            the inclusion paths for other translation files are relative to
            root of the content.ggpk and if using a file system it is expected
            to mirror this behaviour

        Parameters
        ----------
        file_path : Iterable or str or None
            The file to read. Can also accept an iterable of files to read
            which will all be merged into one file. Also see
            :meth:`read`
        base_dir : str or None
            Base directory from where other translation files that contain the
            "include" tag will be included
        parent : :class:`TranslationFileCache` or None
            parent :class:`TranslationFileCache` that will be used for inclusion

        Raises
        ------
        ValueError
            if both parent and base_dir are specified
        TypeError
            if parent is not a :class:`TranslationFileCache`
        """
        self.translations: list[Translation] = []
        self.translations_hash: dict[str, list[Translation]] = {}
        self._base_dir: str | None = base_dir

        if parent is not None:
            # Check class name instead of isinstance to avoid circular import at runtime
            if parent.__class__.__name__ != "TranslationFileCache":
                raise TypeError("Parent must be a TranslationFileCache.")
            if base_dir is not None:
                raise ValueError("Set either parent or base_dir, but not both.")

        self._parent: TranslationFileCache | None = parent

        # Note str must be first since strings are iterable as well
        if isinstance(file_path, (str, bytes, io.BytesIO)):
            self.read(file_path)
        elif isinstance(file_path, Iterable):
            for path in file_path:
                self.merge(TranslationFile(path))

    def _read(self, buffer: Any, *args: Any, **kwargs: Any) -> None:
        """
        Read and parse translation file from buffer.

        Parses translation file format, extracting translations, IDs, languages,
        and strings. Handles includes and headers.

        Args:
            buffer: File buffer to read from
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)

        Raises:
            ValueError: If file structure is invalid
            ParserError: If translation string is malformed
        """
        self.translations = []
        data = buffer.read().decode("utf-16")

        # starts with bom?
        offset = 0
        match = regex_tokens.search(data, offset)
        while match is not None:
            offset = match.end()
            match_next = regex_tokens.search(data, offset)
            offset_max = match_next.start() if match_next else len(data)
            if match.group("description"):
                translation = Translation(identifier=match.group("identifier"))

                # Parse the IDs for the translations
                id_count_match = regex_int.search(data, offset, offset_max)
                if id_count_match is None:
                    raise ValueError(
                        f"Couldn't find id count between offset {offset} and {offset_max}"
                    )
                offset = id_count_match.end()
                id_count = int(id_count_match.group())

                id_string = regex_ids.search(data, offset, offset_max)
                if id_string is None:
                    raise ValueError(
                        f"Couldn't find id count between offset {offset} and {offset_max}"
                    )

                # Actually extract the individual ids
                translation.ids = regex_id_strings.findall(id_string.group(0))

                if len(translation.ids) != id_count:
                    print(data[offset:offset_max])
                    raise ValueError(
                        f"Mismatched number of id strings found ({len(translation.ids)} found vs {id_count} "
                        f"expected) between offset {offset} and {offset_max}"
                    )

                offset = id_string.end()

                t = True
                language = "English"
                while t:
                    tl = TranslationLanguage(language, parent=translation)
                    tcount_match = regex_int.search(data, offset, offset_max)
                    if tcount_match is None:
                        raise ValueError(
                            f"Couldn't find translation count between offset {offset} and {offset_max}"
                        )
                    offset = tcount_match.end()
                    tcount = int(tcount_match.group())
                    language_match = regex_lang.search(data, offset, offset_max)

                    if language_match is None:
                        offset_next_lang = offset_max
                        t = False
                    else:
                        offset_next_lang = language_match.start()
                        language = language_match.group("language")

                    for _i in range(0, tcount):
                        ts_match = regex_translation_string.search(data, offset, offset_next_lang)
                        if not ts_match:
                            raise ParserError(
                                "Malformed translation string near line {} @ ids {}: {}".format(
                                    data.count("\n", 0, offset),
                                    translation.ids,
                                    data[offset : offset_next_lang + 1],
                                )
                            )

                        offset = ts_match.end()

                        ts = TranslationString(parent=tl)

                        # Min/Max limiter
                        limiter = ts_match.group("minmax").strip().split()
                        for j in range(0, id_count):
                            matchstr = limiter[j]
                            if matchstr.startswith("!"):
                                matchstr = matchstr[1:]
                                negated = True
                            else:
                                negated = False

                            if matchstr == "#":
                                TranslationRange(None, None, parent=ts, negated=negated)
                            elif regex_isnumber.match(matchstr):
                                value = int(matchstr)
                                TranslationRange(value, value, parent=ts, negated=negated)
                            elif "|" in matchstr:
                                minmax = matchstr.split("|")
                                min = int(minmax[0]) if minmax[0] != "#" else None
                                max = int(minmax[1]) if minmax[1] != "#" else None
                                TranslationRange(min, max, parent=ts, negated=negated)
                            else:
                                TranslationRange(None, None, parent=ts, negated=negated)
                                warnings.warn(
                                    'Malformed quantifier string "{}" near index {} (parent {}). Assuming # instead.'.format(
                                        matchstr, ts_match.start("minmax"), translation.ids
                                    ),
                                    TranslationWarning,
                                    stacklevel=2,
                                )

                        ts._set_string(ts_match.group("description"))

                        ts.quantifier.register_from_string(
                            ts_match.group("quantifier"),
                        )

                    offset = offset_next_lang

                self.translations.append(translation)
                for translation_id in translation.ids:
                    self._add_translation_hashed(translation_id, translation)

            elif match.group("no_description"):
                pass
            elif match.group("include"):
                if self._parent:
                    self.merge(self._parent.get_file(match.group("include")))
                elif self._base_dir:
                    real_path = os.path.join(self._base_dir, match.group("include"))
                    self.merge(TranslationFile(real_path, base_dir=self._base_dir))
                else:
                    warnings.warn(
                        "Translation file includes other file, but no base_dir "
                        "or parent specified. Skipping.",
                        TranslationWarning,
                        stacklevel=2,
                    )
            elif match.group("header"):
                pass

            # Done, search next
            match = match_next

    def __eq__(self, other: Any) -> bool:
        """
        Check equality of TranslationFile instances.

        Args:
            other: Other object to compare with

        Returns:
            True if translations and translations_hash are equal
        """
        if not isinstance(other, TranslationFile):
            return False

        for attr in ("translations", "translations_hash"):
            if getattr(self, attr) != getattr(other, attr):
                return False

        return True

    def _add_translation_hashed(self, translation_id: str, translation: Translation) -> None:
        """
        Add translation to hash dictionary.

        Handles duplicate IDs by either ignoring identical translations,
        updating if IDs match, or warning and appending if different.

        Args:
            translation_id: Translation ID string
            translation: Translation instance to add
        """
        if translation_id in self.translations_hash:
            for old_translation in self.translations_hash[translation_id]:
                # Identical, ignore
                if translation == old_translation:
                    return

                # Identical ids, but more recent - update
                if translation.ids == old_translation.ids:
                    self.translations_hash[translation_id] = [
                        translation,
                    ]
                    # Attempt to remove the old one if it exists
                    with contextlib.suppress(ValueError):
                        self.translations.remove(old_translation)

                    return

                """print('Diff for id: %s' % translation_id)
                translation.diff(other)
                print('')"""

                warnings.warn(
                    f'Duplicate id "{translation_id}"', DuplicateIdentifierWarning, stacklevel=2
                )
                self.translations_hash[translation_id].append(translation)
        else:
            self.translations_hash[translation_id] = [
                translation,
            ]

    def copy(self) -> "TranslationFile":
        """
        Create a shallow copy of this TranslationFile.

        Note that the same translation objects will still be referenced.

        Returns:
            Shallow copy of this TranslationFile
        """
        t = TranslationFile()
        for name in self.__slots__:
            setattr(t, name, getattr(self, name))

        return t

    def merge(self, other: "TranslationFile") -> None:
        """
        Merge the current translation file with another translation file.

        All translations from other file are added to this file, with
        duplicate ID handling via _add_translation_hashed.

        Args:
            other: TranslationFile object to merge with

        Raises:
            TypeError: If other is not a TranslationFile instance
        """

        if not isinstance(other, TranslationFile):
            raise TypeError(f"Wrong type: {type(other)}")
        self.translations += other.translations
        for trans_id in other.translations_hash:
            for trans in other.translations_hash[trans_id]:
                self._add_translation_hashed(trans_id, trans)

        # self.translations_hash.update(other.translations_hash)

    def get_translation(
        self,
        tags: list[str] | str,
        values: list[int] | list[tuple[int, int]],
        lang: str = "English",
        full_result: bool = False,
        use_placeholder: bool | Callable[[int], str] = False,
        only_values: bool = False,
    ) -> list[int] | list[str] | TranslationResult:
        """
        Retrieve translation from loaded translation file.

        Args:
            tags: List of identifiers for the tags (or single string)
            values: List of integer values to use for translations. Can also
                be list of tuples (min, max) for range formatting
            lang: Language to use (default: "English", falls back if not found)
            full_result: If True, returns TranslationResult object
            use_placeholder: If True, uses placeholders (x, y, z) instead of values.
                If callable, calls with index to get placeholder string
            only_values: If True, returns only handled values instead of strings

        Returns:
            List of translation strings (or TranslationResult if full_result=True,
            or list of values if only_values=True). May be empty if none found
        """
        # A single translation might have multiple references
        # I.e. the case for always_freeze

        if isinstance(tags, str):
            tags = [
                tags,
            ]

        trans_found: list[Translation] = []
        trans_missing: list[str] = []
        trans_missing_values: list[int | tuple[int, int]] = []
        trans_found_values: list[int | tuple[int, int]] = []
        for i, tag in enumerate(tags):
            # stats that are zero are not displayed
            value = values[i]
            try:
                if isinstance(value, tuple) and value[0] == 0 and value[1] == 0:  # type: ignore[index]
                    continue
            except TypeError:
                if value == 0:
                    continue

            if tag not in self.translations_hash:
                trans_missing.append(tag)
                trans_missing_values.append(values[i])
                continue

            # tr = self.translations_hash[tag][-1]
            for tr in self.translations_hash[tag]:
                index = tr.ids.index(tag)
                if tr in trans_found:
                    tf_index = trans_found.index(tr)
                    trans_found_values[tf_index][index] = values[i]  # type: ignore[index]
                else:
                    trans_found.append(tr)
                    # Used to identify invalid translations later
                    v: list[int | tuple[int, int]] = [0xFFFFFFFF for i in range(0, len(tr.ids))]  # type: ignore[assignment]
                    v[index] = values[i]  # type: ignore[assignment]
                    trans_found_values.append(v)  # type: ignore[arg-type]

        # It seems that partial matches for the tags are indeed allowed and not
        # invalid.
        # Cases are base_chance_to_freeze_% and always_freeze for example
        partial: list[Translation] = []
        for i, found_values in enumerate(trans_found_values):
            for j, value in enumerate(found_values):  # type: ignore[arg-type]
                if value == 0xFFFFFFFF:
                    # Assume 0 as default.
                    found_values[j] = 0  # type: ignore[index]
                    partial.append(trans_found[i])

        if partial:
            warnings.warn(
                "Partial tag match for {}".format(", ".join([str(p) for p in partial])),
                TranslationWarning,
                stacklevel=2,
            )

        trans_lines = []
        trans_found_lines = []
        unused = []
        values_parsed = []
        extra_strings = []
        string_instances = []
        for i, tr in enumerate(trans_found):
            tl = tr.get_language(lang)
            ts, short_values, is_range = tl.get_string(trans_found_values[i])  # type: ignore[arg-type]
            if ts:
                string_instances.append(ts)
                result = ts.format_string(
                    short_values,  # type: ignore[arg-type]
                    is_range,  # type: ignore[arg-type]
                    use_placeholder,
                    only_values,  # type: ignore[arg-type]
                )
                trans_lines.append(result[0])
                trans_found_lines.append(result[0])
                values_parsed.append(result[2])
                if full_result:
                    unused.append(result[1])
                    extra_strings.append(result[3])

            else:
                trans_found_lines.append("")
                values_parsed.append([])

        if full_result:
            return TranslationResult(
                found=trans_found,
                found_lines=trans_found_lines,
                lines=trans_lines,
                missing=trans_missing,
                missing_values=trans_missing_values,
                values=trans_found_values,
                values_parsed=values_parsed,
                partial=partial,
                unused=unused,
                source_ids=tags,
                source_values=values,
                extra_strings=extra_strings,
                string_instances=string_instances,
            )
        if only_values:
            return values_parsed  # type: ignore[return-value]
        else:
            return trans_lines  # type: ignore[return-value]

    def reverse_translation(self, string: str, lang: str = "English") -> TranslationReverseResult:
        """
        Reverse a translation string to find probable candidates and values.

        Warning:
            During translation there is a loss of information, and it may be
            impossible to reconstruct the original string in some cases.

        Warning:
            This method only works with **exact** translation strings. Minor
            differences may result in failure. Strings from previous versions
            of Path of Exile may not work.

        Args:
            string: The translation string to reverse
            lang: The language the string is in (default: "English")

        Returns:
            TranslationReverseResult containing found translation instances
            and their values
        """
        translations_found = []
        values_found = []

        for tr in self.translations:
            tl = tr.get_language(lang)
            values = tl.reverse_string(string)
            if values is not None:
                translations_found.append(tr)
                values_found.append(values)

        return TranslationReverseResult(translations_found, values_found)
