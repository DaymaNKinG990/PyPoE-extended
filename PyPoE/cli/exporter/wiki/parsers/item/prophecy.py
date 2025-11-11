"""
Prophecy wiki exporter

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/item/prophecy.py                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Contains ProphecyParser for exporting prophecies to wiki format.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from collections import OrderedDict
from functools import partialmethod

# Self
from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.wiki import parser
from PyPoE.cli.exporter.wiki.handler import ExporterResult
from PyPoE.cli.exporter.wiki.parsers.item.base import ProphecyWikiCondition

# =============================================================================
# Classes
# =============================================================================


class ProphecyParser(parser.BaseParser):
    _files = [
        "Prophecies.dat",
    ]

    _LANG = {
        "English": {
            "prophecy": " (prophecy)",
        },
        "Russian": {
            "prophecy": " (пророчество)",
        },
        "German": {
            "prophecy": " (Prophezeiung)",
        },
    }

    _conflict_resolver_prophecy_map = {
        "English": {
            "MapExtraHaku": " (Haku)",
            "MapExtraTora": " (Tora)",
            "MapExtraCatarina": " (Catarina)",
            "MapExtraVagan": " (Vagan)",
            "MapExtraElreon": " (Elreon)",
            "MapExtraVorici": " (Vorici)",
            "MapExtraZana": " (Zana)",
            "MapExtraEinhar": " (Einhar)",
            "MapExtraAlva": " (Alva)",
            "MapExtraNiko": " (Niko)",
            "MapExtraJun": " (Jun)",
            # The other one is disabled, should be fine
            "MapSpawnRogueExiles": "",
            "MysteriousInvadersFire": " (Fire)",
            "MysteriousInvadersCold": " (Cold)",
            "MysteriousInvadersLightning": " (Lightning)",
            "MysteriousInvadersPhysical": " (Physical)",
            "MysteriousInvadersChaos": " (Chaos)",
            "AreaAllRaresAreCloned": " (prophecy)",
            "HillockDropsTheAnvil": " (prophecy)",
        },
        "Russian": {
            "MapExtraHaku": " (Хаку)",
            "MapExtraTora": " (Тора)",
            "MapExtraCatarina": " (Катарина)",
            "MapExtraVagan": " (Ваган)",
            "MapExtraElreon": " (Элреон)",
            "MapExtraVorici": " (Воричи)",
            "MapExtraZana": " (Зана)",
            "MapExtraEinhar": " (Эйнар)",
            "MapExtraAlva": " (Альва)",
            "MapExtraNiko": " (Нико)",
            "MapExtraJun": " (Джун)",
            # The other one is disabled, should be fine
            "MapSpawnRogueExiles": "",
            "MysteriousInvadersFire": " (огонь)",
            "MysteriousInvadersCold": " (холод)",
            "MysteriousInvadersLightning": " (молния)",
            "MysteriousInvadersPhysical": " (физический)",
            "MysteriousInvadersChaos": " (хаос)",
            "AreaAllRaresAreCloned": " (пророчество)",
            "HillockDropsTheAnvil": " (пророчество)",
        },
        "German": {
            "MapExtraHaku": " (Haku)",
            "MapExtraTora": " (Tora)",
            "MapExtraCatarina": " (Catarina)",
            "MapExtraVagan": " (Vagan)",
            "MapExtraElreon": " (Elreon)",
            "MapExtraVorici": " (Vorici)",
            "MapExtraZana": " (Zana)",
            "MapExtraEinhar": " (Einhar)",
            "MapExtraAlva": " (Alva)",
            "MapExtraNiko": " (Niko)",
            "MapExtraJun": " (Jun)",
            # The other one is disabled, should be fine
            "MapSpawnRogueExiles": "",
            "MysteriousInvadersFire": " (Feuer)",
            "MysteriousInvadersCold": " (Kälte)",
            "MysteriousInvadersLightning": " (Blitz)",
            "MysteriousInvadersPhysical": " (Physisch)",
            "MysteriousInvadersChaos": " (Chaos)",
            "AreaAllRaresAreCloned": " (Prophezeiung)",
            "HillockDropsTheAnvil": " (Prophezeiung)",
        },
    }

    _prophecy_column_index_filter = partialmethod(
        parser.BaseParser._column_index_filter,
        dat_file_name="Prophecies.dat",
        error_msg="Several prophecies have not been found:\n%s",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = config.get_option("language")

    def by_rowid(self, parsed_args):
        return self.export(
            parsed_args,
            self.rr["Prophecies.dat"][parsed_args.start : parsed_args.end],
        )

    def by_id(self, parsed_args):
        return self.export(
            parsed_args, self._prophecy_column_index_filter(column_id="Id", arg_list=parsed_args.id)
        )

    def by_name(self, parsed_args):
        return self.export(
            parsed_args,
            self._prophecy_column_index_filter(column_id="Name", arg_list=parsed_args.name),
        )

    def export(self, parsed_args, prophecies):
        final = []
        for prophecy in prophecies:
            if not prophecy["IsEnabled"] and not parsed_args.allow_disabled:
                console('Prophecy "%s" is disabled - skipping.' % prophecy["Name"], msg=Msg.error)
                continue

            final.append(prophecy)

        self.rr["Prophecies.dat"].build_index("Name")

        r = ExporterResult()
        for prophecy in final:
            name = prophecy["Name"]

            infobox = OrderedDict()

            infobox["rarity_id"] = "normal"
            infobox["name"] = name
            infobox["class_id"] = "StackableCurrency"
            infobox["base_item_id"] = "Metadata/Items/Currency/CurrencyItemisedProphecy"
            infobox["flavour_text"] = prophecy["FlavourText"]
            infobox["prophecy_id"] = prophecy["Id"]
            infobox["prediction_text"] = prophecy["PredictionText2"] or prophecy["PredictionText"]
            infobox["seal_cost"] = prophecy["SealCost"]

            if not prophecy["IsEnabled"]:
                infobox["drop_enabled"] = False  # type: ignore[assignment]

            # handle items with duplicate name entries
            if len(self.rr["Prophecies.dat"].index["Name"][name]) > 1:
                extra = self._conflict_resolver_prophecy_map[self.lang].get(prophecy["Id"])
                if extra is None:
                    console(
                        'Unresolved ambiguous item name "%s" / id "%s". '
                        "Skipping" % (prophecy["Name"], prophecy["Id"]),
                        msg=Msg.error,
                    )
                    continue
                name += extra
            cond = ProphecyWikiCondition(
                data=infobox,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file="item_%s.txt" % name,
                wiki_page=[
                    {"page": name, "condition": cond},
                    {"page": name + self._LANG[self.lang]["prophecy"], "condition": cond},
                ],
                wiki_message="Prophecy exporter",
            )

        return r


__all__ = ["ProphecyParser"]
