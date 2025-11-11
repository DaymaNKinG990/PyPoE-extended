"""
Wiki mods exporter

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/mods.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

http://pathofexile.gamepedia.com

Agreement
===============================================================================

See PyPoE/LICENSE

TODO
===============================================================================

FIX the jewel generator (corrupted)
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from collections import OrderedDict, defaultdict
from functools import partialmethod
from typing import Any

from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.wiki.handler import ExporterHandler, ExporterResult
from PyPoE.cli.exporter.wiki.parser import BaseParser, WikiCondition

# Self
from PyPoE.poe import text
from PyPoE.poe.constants import MOD_DOMAIN, MOD_GENERATION_TYPE, MOD_SELL_PRICES, MOD_STATS_RANGE
from PyPoE.shared.decorators import deprecated

# =============================================================================
# Globals
# =============================================================================

__all__ = ["ModParser", "ModsHandler"]

# =============================================================================
# Classes
# =============================================================================


class OutOfBoundsWarning(UserWarning):
    pass


class ModWikiCondition(WikiCondition):
    COPY_KEYS = (  # type: ignore[assignment]
        "tier_text",
    )

    NAME = "Mod"  # type: ignore[assignment]


class ModsHandler(ExporterHandler):
    def __init__(self, sub_parser):
        self.parser = sub_parser.add_parser("mods", help="Mods Exporter")
        self.parser.set_defaults(func=lambda args: self.parser.print_help())
        lua_sub = self.parser.add_subparsers()

        # Mods
        mparser = lua_sub.add_parser("mods", help="Extract all mods.")
        mparser.set_defaults(func=lambda args: mparser.print_help())

        sub = mparser.add_subparsers(help="Method of extracting mods")

        self.add_default_subparser_filters(sub, cls=ModParser)

        # mods filter
        parser = sub.add_parser("filter", help="Filter mods")
        parser.add_argument(
            "--domain",
            dest="domain",
            help="Mod domain",
            choices=[k.name for k in MOD_DOMAIN],
        )

        parser.add_argument(
            "--generation-type",
            "--type",
            dest="generation_type",
            help="Mod domain",
            choices=[k.name for k in MOD_GENERATION_TYPE],
        )

        self.add_default_parsers(
            parser=parser,
            cls=ModParser,
            func=ModParser.filter,
        )

        # Tempest
        parser = lua_sub.add_parser(
            "tempest",
            help="Extract tempest stuff (DEPRECATED).",
        )
        self.add_default_parsers(
            parser=parser,
            cls=ModParser,
            func=ModParser.tempest,
            wiki=False,
        )

    def add_default_parsers(self, *args, **kwargs):
        super().add_default_parsers(*args, **kwargs)
        parser = kwargs["parser"]
        self.add_format_argument(parser)


class ModParser(BaseParser):
    # Load files in advance
    _files = [
        "Mods.dat",
        "Stats.dat",
    ]

    # Load translations in advance
    _translations = [
        "map_stat_descriptions.txt",
    ]

    _mod_column_index_filter = partialmethod(
        BaseParser._column_index_filter,
        dat_file_name="Mods.dat",
        error_msg="Several areas have not been found:\n%s",
    )

    def _append_effect(self, result, mylist, heading):
        mylist.append(heading)

        for line in result.lines:
            mylist.append(f"* {line}")
        for i, stat_id in enumerate(result.missing_ids):
            value = result.missing_values[i]
            if hasattr(value, "__iter__"):
                value = "({} to {})".format(*tuple(value))
            mylist.append(f"* {stat_id} {value}")

    def by_rowid(self, parsed_args):
        return self._export(
            parsed_args,
            self.rr["Mods.dat"][parsed_args.start : parsed_args.end],
        )

    def by_id(self, parsed_args):
        return self._export(
            parsed_args, self._mod_column_index_filter(column_id="Id", arg_list=parsed_args.id)
        )

    def by_name(self, parsed_args):
        return self._export(
            parsed_args, self._mod_column_index_filter(column_id="Name", arg_list=parsed_args.name)
        )

    def filter(self, args):
        mods = []

        filters = []
        if args.domain:
            filters.append(
                {
                    "column": "Domain",
                    "comp": getattr(MOD_DOMAIN, args.domain),
                }
            )

        if args.generation_type:
            filters.append(
                {
                    "column": "GenerationType",
                    "comp": getattr(MOD_GENERATION_TYPE, args.generation_type),
                }
            )

        for mod in self.rr["Mods.dat"]:
            for filter in filters:
                if mod[filter["column"]] != filter["comp"]:
                    break
            else:
                mods.append(mod)

        return self._export(args, mods)

    def _export(self, parsed_args, mods):
        r = ExporterResult()

        if mods:
            console(f"Found {len(mods)} mods. Processing...")
        else:
            console("No mods found for the specified parameters. Quitting.", msg=Msg.warning)
            return r

        # Needed for localizing sell prices
        self.rr["BaseItemTypes.dat"].build_index("Id")

        for mod in mods:
            data = OrderedDict()

            for k in (
                ("Id", "id"),
                ("CorrectGroup", "mod_group"),
                ("Domain", "domain"),
                ("GenerationType", "generation_type"),
                ("Level", "required_level"),
            ):
                v = mod[k[0]]
                if v:
                    data[k[1]] = v

            if mod["Name"]:
                root = text.parse_description_tags(mod["Name"])

                def handler(hstr, parameter):
                    return hstr if parameter == "MS" else ""

                data["name"] = root.handle_tags({"if": handler, "elif": handler})

            if mod["BuffDefinitionsKey"]:
                data["granted_buff_id"] = mod["BuffDefinitionsKey"]["Id"]
                data["granted_buff_value"] = mod["BuffValue"]
            # todo ID for GEPL
            if mod["GrantedEffectsPerLevelKeys"]:
                data["granted_skill"] = ", ".join(
                    [k["GrantedEffectsKey"]["Id"] for k in mod["GrantedEffectsPerLevelKeys"]]
                )
            data["mod_type"] = mod["ModTypeKey"]["Name"]

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

            data["stat_text"] = "<br>".join(self._get_stats(stats, values, mod))

            for i, (sid, (vmin, vmax)) in enumerate(zip(stats, values, strict=False), start=1):
                data[f"stat{i}_id"] = sid
                data[f"stat{i}_min"] = vmin
                data[f"stat{i}_max"] = vmax

            for i, tag in enumerate(mod["SpawnWeight_TagsKeys"]):
                j = i + 1
                data[f"spawn_weight{j}_tag"] = tag["Id"]
                data[f"spawn_weight{j}_value"] = mod["SpawnWeight_Values"][i]

            for i, tag in enumerate(mod["GenerationWeight_TagsKeys"]):
                j = i + 1
                data[f"generation_weight{j}_tag"] = tag["Id"]
                data[f"generation_weight{j}_value"] = mod["GenerationWeight_Values"][i]

            tags = ", ".join(
                [t["Id"] for t in mod["ModTypeKey"]["TagsKeys"]]
                + [t["Id"] for t in mod["TagsKeys"]]
            )
            if tags:
                data["tags"] = tags

            if mod["ModTypeKey"]:
                sell_price: Any = defaultdict(int)
                for msp in mod["ModTypeKey"]["ModSellPriceTypesKeys"]:
                    for i, (item_id, amount) in enumerate(
                        MOD_SELL_PRICES[msp["Id"]].items(), start=1
                    ):
                        data[f"sell_price{i}_name"] = self.rr["BaseItemTypes.dat"].index["Id"][
                            item_id
                        ]["Name"]
                        data[f"sell_price{i}_amount"] = amount

                # Make sure this is always the same order
                sell_price = sorted(sell_price.items(), key=lambda x: x[0])  # type: ignore[assignment]

                for i, (item_name, amount) in enumerate(sell_price, start=1):
                    data[f"sell_price{i}_name"] = item_name
                    data[f"sell_price{i}_amount"] = amount

            # 3+ tildes not allowed
            page_name = "Modifier:" + self._format_wiki_title(mod["Id"])
            cond = ModWikiCondition(data, parsed_args)

            r.add_result(
                text=cond,
                out_file="mod_{}.txt".format(data["id"]),
                wiki_page=[
                    {"page": page_name, "condition": cond},
                ],
                wiki_message="Mod updater",
            )

        return r

    @deprecated(message="Will be done in-wiki in the future - non functional")
    def tempest(self, parsed_args):
        tf = self.tc["map_stat_descriptions.txt"]
        data = []
        for mod in self.rr["Mods.dat"]:
            # Is it a tempest mod?
            if mod["CorrectGroup"] != "MapEclipse":
                continue

            # Doesn't have a name - probably not implemented
            if not mod["Name"]:
                continue

            stats = []
            for i in MOD_STATS_RANGE:
                stat = mod[f"StatsKey{i}"]
                if stat:
                    stats.append(stat)

            info = {}
            info["name"] = mod["Name"]
            effects: list[str] = []

            stat_ids = [st["Id"] for st in stats]
            stat_values = []

            for i, stat in enumerate(stats):
                j = i + 1
                values = [mod[f"Stat{j}Min"], mod[f"Stat{j}Max"]]
                if values[0] == values[1]:
                    values = values[0]
                stat_values.append(values)

            try:
                index = stat_ids.index("map_summon_exploding_buff_storms")
            except ValueError:
                pass
            else:
                # Value is incremented by 1 for some reason
                tempest = self.rr["ExplodingStormBuffs.dat"][stat_values[index] - 1]  # type: ignore[operator]

                stat_ids.pop(index)
                stat_values.pop(index)

                if tempest["BuffDefinitionsKey"]:
                    tempest_stats = tempest["BuffDefinitionsKey"]["StatKeys"]
                    tempest_values = tempest["StatValues"]
                    tempest_stat_ids = [st["Id"] for st in tempest_stats]
                    t = tf.get_translation(
                        tempest_stat_ids,
                        tempest_values,
                        full_result=True,
                        lang=config.get_option("language"),
                    )
                    self._append_effect(
                        t, effects, "The tempest buff provides the following effects:"
                    )
                # if tempest['MonsterVarietiesKey']:
                #    print(tempest['MonsterVarietiesKey'])
                #    break

            t = tf.get_translation(
                stat_ids, stat_values, full_result=True, lang=config.get_option("language")
            )
            self._append_effect(t, effects, "The area gets the following modifiers:")

            info["effect"] = "\n".join(effects)
            data.append(info)

        data.sort(key=lambda info: info["name"])

        out = []
        for info in data:
            out.append("|-\n")
            out.append("| {}\n".format(info["name"]))
            out.append("| {}\n".format(info["effect"]))
            out.append("| \n")

        r = ExporterResult()
        r.add_result(lines=out, out_file="tempest_mods.txt")

        return r
