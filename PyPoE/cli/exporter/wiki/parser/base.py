"""
Base wiki parser class.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/base.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Base parser class for wiki export handlers.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

import os
import warnings
from typing import Any

from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import fix_path, get_content_path
from PyPoE.cli.exporter.wiki.parser.utils import make_inter_wiki_links
from PyPoE.poe.constants import MOD_DOMAIN, MOD_STATS_RANGE
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.specification.fields import Specification
from PyPoE.poe.file.translations import (
    MissingIdentifierWarning,
    TranslationFile,
    TranslationFileCache,
    get_custom_translation_file,
    install_data_dependant_quantifiers,
)
from PyPoE.poe.sim.mods import get_translation_file_from_domain
from PyPoE.shared.di import DIContainer

# =============================================================================
# Globals
# =============================================================================

__all__ = ["BaseParser"]

# =============================================================================
# Classes
# =============================================================================


class BaseParser:
    """
    Base parser class for wiki export handlers.

    This class provides common functionality for all wiki parsers, including:
    - File system access
    - Relational data reading
    - Translation file caching
    - Image handling
    - Wiki formatting utilities

    Attributes:
        base_path: Base path for output files
        parsed_args: Parsed command-line arguments
        rr: RelationalReader instance for data access
        tc: TranslationFileCache instance for translations
        custom: Custom TranslationFile instance
        file_system: FileSystem instance for file operations
        lang: Language code for translations
        _img_path: Path for storing images (if enabled)
    """

    _DETAILED_FORMAT = '<abbr title="%s">%s</abbr>'

    _HIDDEN_FORMAT = {
        "English": "%s (Hidden)",
        "German": "%s (nicht sichtbar)",
        "Russian": "%s (скрытый)",
    }
    _MISSING_MSG = "Several arguments have not been found:\n%s"

    _TC_KWARGS: dict[str, str] = {}

    _files: list[str] = []
    _translations: list[str] = []
    _img_path: str | None = None

    def __init__(
        self,
        base_path: str,
        parsed_args: Any,
        *,
        # Dependency injection parameters (optional)
        file_system: FileSystem | None = None,
        specification: Specification | None = None,
        relational_reader: RelationalReader | None = None,
        translation_cache: TranslationFileCache | None = None,
        ot_cache: OTFileCache | None = None,
        custom_translation: TranslationFile | None = None,
        language: str | None = None,
    ):
        """
        Initialize BaseParser.

        Args:
            base_path: Base path for output files
            parsed_args: Parsed command-line arguments
            file_system: FileSystem instance (optional, created if None)
            specification: Specification instance (optional, loaded if None)
            relational_reader: RelationalReader instance (optional, created if None)
            translation_cache: TranslationFileCache instance (optional, created if None)
            ot_cache: OTFileCache instance (optional, created if None)
            custom_translation: Custom TranslationFile (optional, loaded if None)
            language: Language code (optional, from config if None)

        Note:
            All dependency injection parameters are optional for backward compatibility.
            If not provided, dependencies are created as before.
        """
        self.parsed_args = parsed_args
        self.base_path = base_path

        # Dependency injection: use provided or create defaults
        self.lang = language if language is not None else config.get_option("language")

        # FileSystem
        if file_system is not None:
            self.file_system = file_system
        else:
            self.file_system = FileSystem(root_path=get_content_path())

        # Specification
        if specification is not None:
            spec = specification
        else:
            factory = FileParserFactory.default(version=config.get_option("version"))
            spec = factory.get_specification()

        # RelationalReader
        if relational_reader is not None:
            self.rr = relational_reader
        else:
            opt = {
                "use_dat_value": False,
                "auto_build_index": True,
                "specification": spec,
            }
            self.rr = RelationalReader(
                path_or_file_system=self.file_system,
                files=self._files,
                read_options=opt,
                raise_error_on_missing_relation=False,
                language=self.lang,
            )
            install_data_dependant_quantifiers(self.rr)

        # TranslationFileCache
        if translation_cache is not None:
            self.tc = translation_cache
        else:
            self.tc = TranslationFileCache(path_or_file_system=self.file_system, **self._TC_KWARGS)
            for file_name in self._translations:
                self.tc[file_name]

        # OTFileCache
        if ot_cache is not None:
            self.ot = ot_cache
        else:
            self.ot = OTFileCache(path_or_file_system=self.file_system)

        # Custom translation file
        if custom_translation is not None:
            self.custom = custom_translation
        else:
            self.custom = get_custom_translation_file()

        self._img_path = None

    @classmethod
    def with_factory(
        cls,
        base_path: str,
        parsed_args: Any,
        container: DIContainer,
        *,
        language: str | None = None,
    ) -> "BaseParser":
        """
        Create BaseParser instance using dependency injection container.

        Args:
            base_path: Base path for output files
            parsed_args: Parsed command-line arguments
            container: DI container with registered dependencies
            language: Language code (optional, from config if None)

        Returns:
            BaseParser instance with injected dependencies

        Example:
            >>> from PyPoE.shared.di import DIContainer
            >>> from PyPoE.poe.providers import register_core_providers
            >>>
            >>> container = DIContainer()
            >>> register_core_providers(container)
            >>> parser = BaseParser.with_factory(
            ...     base_path="output",
            ...     parsed_args=args,
            ...     container=container,
            ... )
        """
        from PyPoE.poe.file.dat import RelationalReader
        from PyPoE.poe.file.file_system import FileSystem
        from PyPoE.poe.file.ot import OTFileCache
        from PyPoE.poe.file.specification.fields import Specification
        from PyPoE.poe.file.translations import TranslationFile, TranslationFileCache

        # Resolve dependencies from container (if registered)
        file_system = container.resolve(FileSystem) if container.is_registered(FileSystem) else None
        specification = (
            container.resolve(Specification) if container.is_registered(Specification) else None
        )
        relational_reader = (
            container.resolve(RelationalReader)
            if container.is_registered(RelationalReader)
            else None
        )
        translation_cache = (
            container.resolve(TranslationFileCache)
            if container.is_registered(TranslationFileCache)
            else None
        )
        ot_cache = (
            container.resolve(OTFileCache) if container.is_registered(OTFileCache) else None
        )
        custom_translation = (
            container.resolve(TranslationFile)
            if container.is_registered(TranslationFile)
            else None
        )

        return cls(
            base_path=base_path,
            parsed_args=parsed_args,
            file_system=file_system,
            specification=specification,
            relational_reader=relational_reader,
            translation_cache=translation_cache,
            ot_cache=ot_cache,
            custom_translation=custom_translation,
            language=language,
        )

    def _column_index_filter(
        self, dat_file_name: str, column_id: str, arg_list: list[str], error_msg: str = _MISSING_MSG
    ) -> list[Any]:
        """
        Filter rows from a DAT file by column index.

        Builds an index for the specified column and returns matching rows
        for the given arguments. Warns about missing arguments.

        Args:
            dat_file_name: Name of the DAT file to query
            column_id: Column name to index and filter by
            arg_list: List of values to filter by
            error_msg: Error message format for missing arguments

        Returns:
            List of matching rows (DatRecord instances or lists)
        """
        self.rr[dat_file_name].build_index(column_id)

        rows: list[Any] = []
        missing = []

        func = rows.append if column_id in self.rr[dat_file_name].columns_unique else rows.extend

        for argument in arg_list:
            if argument in self.rr[dat_file_name].index[column_id]:
                func(self.rr[dat_file_name].index[column_id][argument])
            else:
                missing.append(argument)

        if missing:
            console(self._MISSING_MSG % "\n".join(missing), msg=Msg.warning)

        return rows

    def _format_tr(self, tr: Any) -> str:
        """
        Format translation result for wiki output.

        Converts translation lines to wiki format with inter-wiki links.

        Args:
            tr: TranslationResult object with lines attribute

        Returns:
            Formatted string with wiki links
        """
        return make_inter_wiki_links(self._format_lines(tr.lines))

    def _format_lines(self, lines: list[str]) -> str:
        """
        Format lines for wiki output.

        Joins lines with <br> tags and replaces newlines with <br>.

        Args:
            lines: List of strings to format

        Returns:
            Formatted string with HTML line breaks
        """
        return "<br>".join(lines).replace("\n", "<br>")

    def _format_wiki_title(self, title: str) -> str:
        """
        Format title for wiki output.

        Replaces underscores with tildes for wiki formatting.

        Args:
            title: Title string to format

        Returns:
            Formatted title string
        """
        return title.replace("_", "~").replace("~~~", "_~~_~~_")

    def _format_hidden(self, custom: str) -> str:
        """
        Format hidden text for wiki output.

        Wraps text with language-specific "hidden" marker.

        Args:
            custom: Text to mark as hidden

        Returns:
            Formatted string with hidden marker
        """
        return self._HIDDEN_FORMAT[self.lang] % make_inter_wiki_links(custom)

    def _format_detailed(self, custom: str, ingame: str) -> str:
        """
        Format detailed text with tooltip for wiki output.

        Creates an abbreviation with tooltip showing in-game text.

        Args:
            custom: Custom text to display
            ingame: In-game text for tooltip

        Returns:
            Formatted HTML string with tooltip
        """
        return self._DETAILED_FORMAT % (ingame, make_inter_wiki_links(custom))

    def _write_dds(self, data: bytes, out_path: str, parsed_args: Any) -> None:
        """
        Write DDS image data to file.

        Extracts DDS data, writes to file, and optionally converts to PNG.

        Args:
            data: Raw DDS image data
            out_path: Output file path
            parsed_args: Parsed arguments (may contain convert_images flag)
        """
        out_path = fix_path(out_path)
        with open(out_path, "wb") as f:
            f.write(self.file_system.extract_dds(data))

            console(f'Wrote "{out_path}"')

        if not parsed_args.convert_images:
            return

        os.system(
            'magick convert "{}" "{}"'.format(
                out_path,
                out_path.replace(".dds", ".png"),
            )
        )
        os.remove(out_path)

        console(f'Converted "{out_path}" to png')

    def _image_init(self, parsed_args: Any) -> None:
        """
        Initialize image storage directory.

        Creates image directory if image storage is enabled.

        Args:
            parsed_args: Parsed arguments (may contain store_images flag)
        """
        from PyPoE.shared.file_utils import ensure_directory

        if parsed_args.store_images:
            self._img_path = os.path.join(self.base_path, "img")
            ensure_directory(self._img_path)

    def _get_stats(
        self,
        stats: list[str] | None = None,
        values: list[tuple[int, int]] | None = None,
        mod: Any | None = None,
        translation_file: str | None = None,
    ) -> list[str]:
        """
        Get formatted stat descriptions for wiki output.

        Retrieves and formats stat descriptions from translation files.
        Handles special cases for monster domain stats.

        Args:
            stats: List of stat IDs (extracted from mod if None)
            values: List of (min, max) value tuples (extracted from mod if None)
            mod: Mod data object (required if stats/values not provided)
            translation_file: Translation file name (auto-determined if None)

        Returns:
            List of formatted stat description strings

        Raises:
            ValueError: If mod is required but not provided
        """
        if translation_file is None:
            if mod is None:
                raise ValueError(
                    "Can not automatically determine translation file if mod is not set"
                )
            else:
                translation_file = get_translation_file_from_domain(mod["Domain"])
        if stats is None or values is None:
            if mod is None:
                raise ValueError("Mod must be set if any of stats or values aren't set")
            else:
                stats = []
                values = []
                for i in MOD_STATS_RANGE:
                    k = mod[f"StatsKey{i}"]
                    if k is None:
                        continue

                    stat = k["Id"]
                    value = mod[f"Stat{i}Min"], mod[f"Stat{i}Max"]

                    if value[0] == 0 and value[1] == 0:
                        continue

                    stats.append(stat)
                    values.append(value)

        result = self.tc[translation_file].get_translation(
            stats, values, full_result=True, lang=self.lang
        )

        # Type narrowing: when full_result=True, get_translation returns TranslationResult
        from PyPoE.poe.file.translations.results import TranslationResult

        if not isinstance(result, TranslationResult):
            raise TypeError(f"Expected TranslationResult, got {type(result)}")

        if mod and mod["Domain"] == MOD_DOMAIN.MONSTER:
            default_result = self.tc["stat_descriptions.txt"].get_translation(
                result.source_ids, result.source_values, full_result=True, lang=self.lang
            )
            if not isinstance(default_result, TranslationResult):
                raise TypeError(f"Expected TranslationResult, got {type(default_result)}")
            default = default_result
            temp_ids = []
            temp_trans = []

            for i, tr in enumerate(default.found):
                for j, tr2 in enumerate(result.found):
                    if tr.ids != tr2.ids:
                        continue

                    r1 = tr.get_language(self.lang).format_string([default.values[i]])
                    r2 = tr2.get_language(self.lang).format_string([result.values[j]])
                    if r1 and r2 and r1[0] != r2[0]:
                        temp_trans.append(self._format_detailed(r1[0], r2[0]))
                    elif r2 and r2[0]:
                        temp_trans.append(self._format_hidden(r2[0]))
                    temp_ids.append(tr.ids)

                is_missing = False
                for tid in tr.ids:
                    if tid in result.missing_ids:
                        is_missing = True
                        break

                if not is_missing:
                    continue

                r1 = tr.get_language(self.lang).format_string([default.values[i]])
                if r1 and r1[0]:
                    temp_trans.append(self._format_hidden(r1[0]))
                    temp_ids.append(tr.ids)

                for tid in tr.ids:
                    try:
                        i = result.missing_ids.index(tid)
                    except ValueError:
                        continue
                    del result.missing_ids[i]
                    del result.missing_values[i]

            index = 0
            for i, tr in enumerate(result.found):
                try:
                    index = temp_ids.index(tr.ids)
                except ValueError:
                    temp_ids.insert(index, tr.ids)
                    temp_trans.insert(
                        index,
                        make_inter_wiki_links(
                            tr.get_language(self.lang).format_string([result.values[i]])[0]
                        ),
                    )
                else:
                    pass

            out = temp_trans
        else:
            out = [make_inter_wiki_links(line) for line in result.lines]

        if result.missing_ids:
            custom_result = self.custom.get_translation(
                result.missing_ids,
                result.missing_values,
                full_result=True,
                lang=self.lang,
            )

        if custom_result.missing_ids:  # type: ignore[union-attr]
            warnings.warn(
                f"Missing translation for ids {custom_result.missing_ids} and values {custom_result.missing_values}",  # type: ignore[union-attr]
                MissingIdentifierWarning,
                stacklevel=2,
            )

        for line in custom_result.lines:  # type: ignore[union-attr]
            if line:
                out.append(self._HIDDEN_FORMAT[self.lang] % line)

        finalout = []
        for line in out:
            if "\n" in line:
                # By request differentiate between breaks from the source file
                # and different stats
                finalout.append("<br />".join(line.split("\n")))
            else:
                finalout.append(line)

        return finalout
