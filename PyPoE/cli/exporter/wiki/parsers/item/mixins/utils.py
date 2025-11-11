"""
UtilsMixin for ItemsParser.

Contains utils-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

import re
from collections import OrderedDict

from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.wiki import parser
from PyPoE.poe.file.dat import RelationalReader

# =============================================================================
# Classes
# =============================================================================


class UtilsMixin:
    """Mixin providing utils methods for ItemsParser."""

    """Mixin providing utils methods for ItemsParser."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parsed_args = None
        self._language = config.get_option("language")
        if self._language != "English":
            self.rr2 = RelationalReader(
                path_or_file_system=self.file_system,
                files=["BaseItemTypes.dat", "Prophecies.dat"],
                read_options={
                    "use_dat_value": False,
                    "auto_build_index": True,
                },
                raise_error_on_missing_relation=False,
                language="English",
            )
        else:
            self.rr2 = None

    def _apply_flask_buffs(self, infobox, base_item_type, flasks):
        for i, value in enumerate(flasks["BuffStatValues"], start=1):
            infobox["buff_value%s" % i] = value

        if flasks["BuffDefinitionsKey"]:
            stats = [s["Id"] for s in flasks["BuffDefinitionsKey"]["StatsKeys"]]
            tr = self.tc["stat_descriptions.txt"].get_translation(
                stats,
                flasks["BuffStatValues"],
                full_result=True,
                lang=self._language,
            )
            infobox["buff_stat_text"] = "<br>".join(
                [parser.make_inter_wiki_links(line) for line in tr.lines]
            )

    # TODO: BuffDefinitionsKey, BuffStatValues

    def _apply_master_map(self, infobox, base_item_type, hideout):
        if not hideout["IsNonMasterDoodad"]:
            _apply_column_map(infobox, self._master_hideout_doodad_map, hideout)

    def _parse_class_filter(self, parsed_args):
        if parsed_args.item_class_id:
            return [
                self.rr["ItemClasses.dat"].index["Id"][cls]["Name"]
                for cls in parsed_args.item_class_id
            ]
        elif parsed_args.item_class:
            self.rr["ItemClasses.dat"].build_index("Name")
            return [
                self.rr["ItemClasses.dat"].index["Name"][cls][0]["Name"]
                for cls in parsed_args.item_class
            ]
        else:
            return []

    def _process_purchase_costs(self, source, infobox):
        for rarity in RARITY:
            if rarity.id >= 5:
                break
            for i, (item, cost) in enumerate(source[rarity.name_upper + "Purchase"], start=1):
                prefix = "purchase_cost_%s%s" % (rarity.name_lower, i)
                infobox[prefix + "_name"] = item["Name"]
                infobox[prefix + "_amount"] = cost

    def by_rowid(self, parsed_args):
        return self._export(
            parsed_args,
            self.rr["BaseItemTypes.dat"][parsed_args.start : parsed_args.end],
        )

    def by_id(self, parsed_args):
        return self._export(
            parsed_args, self._item_column_index_filter(column_id="Id", arg_list=parsed_args.id)
        )

    def by_name(self, parsed_args):
        return self._export(
            parsed_args, self._item_column_index_filter(column_id="Name", arg_list=parsed_args.name)
        )

    def by_filter(self, parsed_args):
        if parsed_args.re_name:
            parsed_args.re_name = re.compile(parsed_args.re_name, flags=re.UNICODE)
        if parsed_args.re_id:
            parsed_args.re_id = re.compile(parsed_args.re_id, flags=re.UNICODE)

        items = []

        for item in self.rr["BaseItemTypes.dat"]:
            if parsed_args.re_name and not parsed_args.re_name.match(item["Name"]):
                continue

            if parsed_args.re_id and not parsed_args.re_id.match(item["Id"]):
                continue

            items.append(item)

        return self._export(parsed_args, items)

    def _process_base_item_type(self, base_item_type, infobox, not_new_map=True):
        m_id = base_item_type["Id"]

        infobox["rarity_id"] = "normal"

        # BaseItemTypes.dat
        infobox["name"] = base_item_type["Name"]
        infobox["class_id"] = base_item_type["ItemClassesKey"]["Id"]
        infobox["size_x"] = base_item_type["Width"]
        infobox["size_y"] = base_item_type["Height"]
        if base_item_type["FlavourTextKey"]:
            infobox["flavour_text"] = parser.parse_and_handle_description_tags(
                rr=self.rr,
                text=base_item_type["FlavourTextKey"]["Text"],
            )

        if (
            base_item_type["ItemClassesKey"]["Id"] not in self._IGNORE_DROP_LEVEL_CLASSES
            and m_id not in self._IGNORE_DROP_LEVEL_ITEMS_BY_ID
        ):
            infobox["drop_level"] = base_item_type["DropLevel"]

        base_ot = OTFile(parent_or_file_system=self.file_system)
        base_ot.read(self.file_system.get_file(base_item_type["InheritsFrom"] + ".ot"))
        try:
            ot = self.ot[m_id + ".ot"]
        except FileNotFoundError:
            pass
        else:
            base_ot.merge(ot)
        finally:
            ot = base_ot

        if "enable_rarity" in ot["Mods"]:
            infobox["drop_rarities_ids"] = ", ".join(ot["Mods"]["enable_rarity"])

        tags = [t["Id"] for t in base_item_type["TagsKeys"]]
        infobox["tags"] = ", ".join(tags + list(ot["Base"]["tag"]))

        if not_new_map:
            infobox["metadata_id"] = m_id

        description = ot["Stack"].get("function_text")
        if description:
            infobox["description"] = self.rr["ClientStrings.dat"].index["Id"][description]["Text"]

        help_text = ot["Base"].get("description_text")
        if help_text:
            infobox["help_text"] = self.rr["ClientStrings.dat"].index["Id"][help_text]["Text"]

        for i, mod in enumerate(base_item_type["Implicit_ModsKeys"]):
            infobox["implicit%s" % (i + 1)] = mod["Id"]

    def _process_name_conflicts(self, infobox, base_item_type, language):
        rr = self.rr2 if language != self._language else self.rr
        # Get the base item of other language
        base_item_type = rr["BaseItemTypes.dat"][base_item_type.rowid]

        name = base_item_type["Name"]
        cls_id = base_item_type["ItemClassesKey"]["Id"]
        m_id = base_item_type["Id"]
        appendix = self._NAME_OVERRIDE_BY_ID[language].get(m_id)

        if appendix is not None:
            name += appendix
            infobox["inventory_icon"] = name
        elif (
            cls_id == "Map"
            or len(
                rr["BaseItemTypes.dat"].index["Name"][name]
                + rr["Prophecies.dat"].index["Name"][name]
            )
            > 1
        ):
            resolver = self._conflict_resolver_map.get(cls_id)

            if resolver:
                name = resolver(self, infobox, base_item_type, rr, language)
                if name is None:
                    console(
                        'Unresolved ambiguous item "%s" with name "%s". '
                        "Skipping" % (m_id, infobox["name"]),
                        msg=Msg.error,
                    )
                    return
            else:
                console(
                    'Unresolved ambiguous item "%s" with name "%s". '
                    "Skipping" % (m_id, infobox["name"]),
                    msg=Msg.error,
                )
                console(
                    'No name conflict handler defined for item class id "%s"' % cls_id,
                    msg=Msg.error,
                )
                return

        return name

    def _export(self, parsed_args, items):
        classes = self._parse_class_filter(parsed_args)
        if classes:
            items = [item for item in items if item["ItemClassesKey"]["Name"] in classes]

        self._parsed_args = parsed_args
        console("Found %s items. Removing disabled items..." % len(items))
        items = [
            base_item_type
            for base_item_type in items
            if base_item_type["Id"] not in self._SKIP_ITEMS_BY_ID
        ]
        console("%s items left for processing." % len(items))

        console("Loading additional files - this may take a while...")
        self._image_init(parsed_args)

        r = ExporterResult()
        self.rr["BaseItemTypes.dat"].build_index("Name")
        self.rr["Prophecies.dat"].build_index("Name")
        self.rr["MapPurchaseCosts.dat"].build_index("Tier")

        if self._language != "English" and parsed_args.english_file_link:
            self.rr2["BaseItemTypes.dat"].build_index("Name")
            self.rr2["Prophecies.dat"].build_index("Name")

        console("Processing item information...")

        for base_item_type in items:
            name = base_item_type["Name"]
            cls_id = base_item_type["ItemClassesKey"]["Id"]
            m_id = base_item_type["Id"]

            infobox = OrderedDict()
            self._process_base_item_type(base_item_type, infobox)
            self._process_purchase_costs(base_item_type, infobox)

            funcs = self._cls_map.get(cls_id)
            if funcs:
                fail = False
                for f in funcs:
                    if not f(self, infobox, base_item_type):
                        fail = True
                        console(
                            'Required extra info for item "%s" with class id '
                            '"%s" not found. Skipping.' % (name, cls_id),
                            msg=Msg.error,
                        )
                        break
                if fail:
                    continue

            # handle items with duplicate name entries
            # Maps must be handled in any case due to unique naming style of
            # pages
            page = self._process_name_conflicts(infobox, base_item_type, self._language)
            if page is None:
                continue
            if self._language != "English" and parsed_args.english_file_link:
                icon = self._process_name_conflicts(infobox, base_item_type, "English")
                if cls_id == "DivinationCard":
                    key = "card_art"
                else:
                    key = "inventory_icon"

                if icon:
                    infobox[key] = icon
                else:
                    infobox[key] = self.rr2["BaseItemTypes.dat"][base_item_type.rowid]["Name"]

            # putting this last since it's usually manually added
            if m_id in self._DROP_DISABLED_ITEMS_BY_ID:
                infobox["drop_enabled"] = False

            inventory_icon = infobox.get("inventory_icon") or page
            if ":" in inventory_icon:
                infobox["inventory_icon"] = inventory_icon.replace(":", "")

            cond = ItemWikiCondition(
                data=infobox,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file="item_%s.txt" % page,
                wiki_page=[
                    {
                        "page": page,
                        "condition": cond,
                    }
                ],
                wiki_message="Item exporter",
            )

            if parsed_args.store_images:
                if not base_item_type["ItemVisualIdentityKey"]["DDSFile"]:
                    warnings.warn(
                        'Missing 2d art inventory icon for item "%s"' % base_item_type["Name"]
                    )
                    continue

                self._write_dds(
                    data=self.file_system.get_file(
                        base_item_type["ItemVisualIdentityKey"]["DDSFile"]
                    ),
                    out_path=os.path.join(
                        self._img_path,
                        (infobox.get("inventory_icon") or page) + " inventory icon.dds",
                    ),
                    parsed_args=parsed_args,
                )

        return r

    def _format_map_name(self, base_item_type, map_series, language=None):
        if language is None:
            language = self._language
        if "Harbinger" in base_item_type["Id"]:
            return "%s (%s) (%s)" % (
                base_item_type["Name"],
                self._LANG[language][re.sub(r"^.*Harbinger", "", base_item_type["Id"])],
                map_series["Name"],
            )
        else:
            return "%s (%s)" % (base_item_type["Name"], map_series["Name"])

    def _get_map_series(self, parsed_args):
        self.rr["MapSeries.dat"].build_index("Id")
        self.rr["MapSeries.dat"].build_index("Name")
        if parsed_args.map_series_id is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Id"][parsed_args.map_series_id]
            except IndexError:
                console("Invalid map series id", msg=Msg.error)
                return False
        elif parsed_args.map_series is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Name"][parsed_args.map_series][0]
            except IndexError:
                console("Invalid map series name", msg=Msg.error)
                return False
        else:
            map_series = self.rr["MapSeries.dat"][-1]
            console(
                'No map series specified. Using latest series "%s".' % (map_series["Name"],),
                msg=Msg.warning,
            )

        return map_series
