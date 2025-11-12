"""
Item Type Parser.

Handles parsing of different item types and their extra data.
Extracted from TypesMixin and ExtrasMixin for better separation of concerns.

This class uses composition instead of inheritance, making it easier to test
and maintain.
"""

import re
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from PyPoE.cli.exporter.wiki import parser
from PyPoE.cli.exporter.wiki.parsers.item.base import _apply_column_map


class ItemTypeParser:
    """
    Parses item types and their extra data.

    This class handles different item types (weapons, armor, currency, etc.)
    and extracts type-specific information.

    Attributes:
        rr: RelationalReader instance for data access
        tc: TranslationFileCache instance
        language: Language code for translations
        lang_map: Language mapping dictionary
    """

    def __init__(
        self,
        relational_reader: Any,
        translation_cache: Any,
        language: str,
        lang_map: dict[str, dict[str, str]],
        *,
        get_stats: Callable[[Any], Any] | None = None,
    ):
        """
        Initialize type parser.

        Args:
            relational_reader: RelationalReader instance
            translation_cache: TranslationFileCache instance
            language: Language code
            lang_map: Language mapping dictionary
            get_stats: Optional function to get stats
        """
        self.rr = relational_reader
        self.tc = translation_cache
        self.language = language
        self.lang_map = lang_map
        self._get_stats = get_stats or (lambda mod: [])

    def parse_type_level(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> bool:
        """
        Parse level requirement for item type.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data

        Returns:
            True if successful
        """
        infobox["required_level"] = base_item_type["DropLevel"]  # type: ignore[index]
        return True

    def parse_type_amulet(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> bool:
        """
        Parse amulet type (including talismans).

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data

        Returns:
            True if successful
        """
        match = re.search("Talisman([0-9])", base_item_type["Id"])  # type: ignore[index]
        if match:
            infobox["is_talisman"] = True
            infobox["talisman_tier"] = match.group(1)
        return True

    def parse_currency_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        currency: Any,
    ) -> bool:
        """
        Parse currency extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            currency: Currency data

        Returns:
            True if successful
        """
        # Add the "shift click to unstack" stuff to currency-ish items
        if currency["Stacks"] > 1 and infobox.get("class_id") not in ("Microtransaction",):  # type: ignore[index]
            if "help_text" in infobox:
                infobox["help_text"] += "<br>"
            else:
                infobox["help_text"] = ""

            infobox["help_text"] += self.rr["ClientStrings.dat"].index["Id"][  # type: ignore[index]
                "ItemDisplayStackDescription"
            ]["Text"]  # type: ignore[index]

        if infobox.get("description"):
            infobox["description"] = parser.parse_and_handle_description_tags(
                rr=self.rr,
                text=infobox["description"],
            )

        return True

    def parse_maps_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        maps: Any,
    ) -> None:
        """
        Parse maps extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            maps: Maps data
        """
        if maps["Shaped_AreaLevel"] > 0:  # type: ignore[index]
            infobox["map_area_level"] = maps["Shaped_AreaLevel"]  # type: ignore[index]
        else:
            infobox["map_area_level"] = maps["Regular_WorldAreasKey"]["AreaLevel"]  # type: ignore[index]

    def parse_map_fragment_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        map_fragment_mods: Any,
    ) -> None:
        """
        Parse map fragment extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            map_fragment_mods: Map fragment mods data
        """
        if map_fragment_mods["ModsKeys"]:  # type: ignore[index]
            i = 1
            while infobox.get(f"implicit{i}") is not None:
                i += 1
            for mod in map_fragment_mods["ModsKeys"]:  # type: ignore[index]
                infobox[f"implicit{i}"] = mod["Id"]  # type: ignore[index]
                i += 1

    def parse_essence_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        essence: Any,
    ) -> bool:
        """
        Parse essence extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            essence: Essence data

        Returns:
            True if successful
        """
        infobox["is_essence"] = True

        # Essence description
        def get_str(k: str | None) -> str:
            if k is None:
                return ""
            return str(self.rr["ClientStrings.dat"].index["Id"][f"EssenceCategory{k}"]["Text"])  # type: ignore[index,no-any-return]

        essence_categories = OrderedDict(
            (
                (
                    None,
                    ("OneHandWeapon", "TwoHandWeapon"),
                ),
                (
                    "MeleeWeapon",
                    (),
                ),
                (
                    "RangedWeapon",
                    ("Wand", "Bow"),
                ),
                (
                    "Weapon",
                    ("TwoHandMeleeWeapon",),
                ),
                ("Armour", ("Gloves", "Boots", "BodyArmour", "Helmet", "Shield")),
                ("Quiver", ()),
                ("Jewellery", ("Amulet", "Ring", "Belt")),
            )
        )

        out: list[str] = []

        if essence["ItemLevelRestriction"] != 0:  # type: ignore[index]
            out.append(
                self.rr["ClientStrings.dat"]  # type: ignore[index]
                .index["Id"]["EssenceModLevelRestriction"]["Text"]  # type: ignore[index]
                .replace("{0}", str(essence["ItemLevelRestriction"]))  # type: ignore[index]
            )
            out[-1] += "<br />"

        def add_line(text: str, mod: Any) -> None:
            nonlocal out
            out.append("{}: {}".format(text, "".join(self._get_stats(mod=mod))))  # type: ignore[call-arg]

        item_mod = essence["Display_Items_ModsKey"]  # type: ignore[index]

        for category, rows in essence_categories.items():
            category_mod = (
                None if category is None else essence[f"Display_{category}_ModsKey"]  # type: ignore[index]
            )

            cur = len(out)
            for row_key in rows:
                mod = essence[f"Display_{row_key}_ModsKey"]  # type: ignore[index]
                if mod is None:
                    continue
                if mod == category_mod:
                    continue
                if mod == item_mod:
                    continue

                add_line(get_str(row_key), mod)

            if category_mod is not None and category_mod != item_mod:
                text = get_str(category) if category is not None else ""
                if cur != len(out):
                    text = get_str("Other").replace("{0}", text)
                add_line(text, category_mod)

        if item_mod:
            # TODO: Can't find items in clientstrings
            add_line(get_str("Other").replace("{0}", "Items"), item_mod)

        infobox["description"] += "<br />" + "<br />".join(out)  # type: ignore[assignment]

        return True

    def parse_harvest_seed_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        harvest_object: Any,
    ) -> bool:
        """
        Parse harvest seed extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            harvest_object: Harvest object data

        Returns:
            True if successful
        """
        if not self.rr["HarvestSeedTypes.dat"].index.get("HarvestObjectsKey"):  # type: ignore[index]
            self.rr["HarvestSeedTypes.dat"].build_index("HarvestObjectsKey")

        harvest_seed = self.rr["HarvestSeedTypes.dat"].index["HarvestObjectsKey"][  # type: ignore[index]
            harvest_object.rowid
        ]

        _apply_column_map(
            infobox,
            (
                (
                    "Text",
                    {
                        "template": "seed_effect",
                    },
                ),
                (
                    "Tier",
                    {
                        "template": "seed_tier",
                    },
                ),
                (
                    "GrowthCycles",
                    {
                        "template": "seed_growth_cycles",
                    },
                ),
                (
                    "RequiredNearbySeed_Tier",
                    {
                        "template": "seed_required_nearby_seed_tier",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "RequiredNearbySeed_Amount",
                    {
                        "template": "seed_required_nearby_seed_amount",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "WildLifeforceConsumedPercentage",
                    {
                        "template": "seed_consumed_wild_lifeforce_percentage",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "VividLifeforceConsumedPercentage",
                    {
                        "template": "seed_consumed_vivid_lifeforce_percentage",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "PrimalLifeforceConsumedPercentage",
                    {
                        "template": "seed_consumed_primal_lifeforce_percentage",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "HarvestCraftOptionsKeys",
                    {
                        "template": "seed_granted_craft_option_ids",
                        "format": lambda v: ",".join([k["Id"] for k in v]),  # type: ignore[index]
                        "condition": lambda v: v,
                    },
                ),
            ),
            harvest_seed,
        )

        return True

    def parse_harvest_plant_booster_extra(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        harvest_object: Any,
    ) -> bool:
        """
        Parse harvest plant booster extra data.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data
            harvest_object: Harvest object data

        Returns:
            True if successful
        """
        if not self.rr["HarvestSeedTypes.dat"].index.get("HarvestObjectsKey"):  # type: ignore[index]
            self.rr["HarvestSeedTypes.dat"].build_index("HarvestObjectsKey")

        harvest_plant_booster = self.rr["HarvestPlantBoosters.dat"].index["HarvestObjectsKey"][  # type: ignore[index]
            harvest_object.rowid
        ]

        _apply_column_map(
            infobox,
            (
                (
                    "Radius",
                    {
                        "template": "plant_booster_radius",
                    },
                ),
                (
                    "Lifeforce",
                    {
                        "template": "plant_booster_lifeforce",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "AdditionalCraftingOptionsChance",
                    {
                        "template": "plant_booster_additional_crafting_options",
                        "condition": lambda v: v > 0,
                    },
                ),
                (
                    "RareExtraChances",
                    {
                        "template": "plant_booster_extra_chances",
                        "condition": lambda v: v > 0,
                    },
                ),
            ),
            harvest_plant_booster,
        )

        return True

