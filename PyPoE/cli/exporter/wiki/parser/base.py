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
from PyPoE.poe.file.translations import (
    MissingIdentifierWarning,
    TranslationFileCache,
    get_custom_translation_file,
    install_data_dependant_quantifiers,
)
from PyPoE.poe.sim.mods import get_translation_file_from_domain

# =============================================================================
# Globals
# =============================================================================

__all__ = ["BaseParser"]

# =============================================================================
# Classes
# =============================================================================


class BaseParser:
    """
    :ivar str base_path:

    :ivar rr:
    :type rr: RelationalReader

    :ivar tc:
    :type tc: TranslationFileCache

    :ivar custom:
    :type custom: TranslationFile
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

    def __init__(self, base_path, parsed_args):
        self.parsed_args = parsed_args

        # Load specifications using dependency injection
        factory = FileParserFactory.default(version=config.get_option("version"))
        specification = factory.get_specification()

        self.base_path = base_path
        self.file_system = FileSystem(root_path=get_content_path())

        opt = {
            "use_dat_value": False,
            "auto_build_index": True,
            "specification": specification,
        }

        # Load rr and translations which will be undoubtedly be needed for
        # parsing
        self.rr = RelationalReader(
            path_or_file_system=self.file_system,
            files=self._files,
            read_options=opt,
            raise_error_on_missing_relation=False,
            language=config.get_option("language"),
        )
        install_data_dependant_quantifiers(self.rr)
        self.tc = TranslationFileCache(path_or_file_system=self.file_system, **self._TC_KWARGS)
        for file_name in self._translations:
            self.tc[file_name]

        self.ot = OTFileCache(
            path_or_file_system=self.file_system,
        )

        self.custom = get_custom_translation_file()

        self._img_path = None
        self.lang = config.get_option("language")

    def _column_index_filter(self, dat_file_name, column_id, arg_list, error_msg=_MISSING_MSG):
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

    def _format_tr(self, tr):
        return make_inter_wiki_links(self._format_lines(tr.lines))

    def _format_lines(self, lines):
        return "<br>".join(lines).replace("\n", "<br>")

    def _format_wiki_title(self, title):
        return title.replace("_", "~").replace("~~~", "_~~_~~_")

    def _format_hidden(self, custom):
        return self._HIDDEN_FORMAT[self.lang] % make_inter_wiki_links(custom)

    def _format_detailed(self, custom, ingame):
        return self._DETAILED_FORMAT % (ingame, make_inter_wiki_links(custom))

    def _write_dds(self, data, out_path, parsed_args):
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

    def _image_init(self, parsed_args):
        if parsed_args.store_images:
            self._img_path = os.path.join(self.base_path, "img")
            if not os.path.exists(self._img_path):
                os.makedirs(self._img_path)

    def _get_stats(self, stats=None, values=None, mod=None, translation_file=None):
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

        if mod and mod["Domain"] == MOD_DOMAIN.MONSTER:
            default = self.tc["stat_descriptions.txt"].get_translation(
                result.source_ids, result.source_values, full_result=True, lang=self.lang
            )
            temp_ids = []
            temp_trans = []

            for i, tr in enumerate(default.found):
                for j, tr2 in enumerate(result.found):
                    if tr.ids != tr2.ids:
                        continue

                    r1 = tr.get_language(self.lang).format_string(default.values[i])
                    r2 = tr2.get_language(self.lang).format_string(result.values[j])
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

                r1 = tr.get_language(self.lang).format_string(default.values[i])
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
                            tr.get_language(self.lang).format_string(result.values[i])[0]
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
