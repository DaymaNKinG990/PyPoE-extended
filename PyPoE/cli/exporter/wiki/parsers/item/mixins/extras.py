"""
ExtrasMixin for ItemsParser.

Contains extras-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

from typing import TYPE_CHECKING, Any, Dict
from collections import OrderedDict

from PyPoE.cli.exporter.wiki import parser
from PyPoE.cli.exporter.wiki.parsers.item.base import _apply_column_map

# =============================================================================
# Classes
# =============================================================================


class ExtrasMixin:
    """Mixin providing extras methods for ItemsParser."""
    
    # Type hints for attributes from parent ItemsParser class
    if TYPE_CHECKING:
        rr: Any
        tc: Any
        _LANG: Dict[str, Dict[str, str]]
        _language: str
        _parsed_args: Any
        
        def _get_stats(self, *args: Any, **kwargs: Any) -> Any: ...

    def _currency_extra(self, infobox, base_item_type, currency):
        # Add the "shift click to unstack" stuff to currency-ish items
        if currency["Stacks"] > 1 and infobox["class_id"] not in ("Microtransaction",):
            if "help_text" in infobox:
                infobox["help_text"] += "<br>"
            else:
                infobox["help_text"] = ""

            infobox["help_text"] += self.rr["ClientStrings.dat"].index["Id"][
                "ItemDisplayStackDescription"
            ]["Text"]

        if infobox.get("description"):
            infobox["description"] = parser.parse_and_handle_description_tags(
                rr=self.rr,
                text=infobox["description"],
            )

        return True

    def _maps_extra(self, infobox, base_item_type, maps):
        if maps["Shaped_AreaLevel"] > 0:
            infobox["map_area_level"] = maps["Shaped_AreaLevel"]
        else:
            infobox["map_area_level"] = maps["Regular_WorldAreasKey"]["AreaLevel"]

        """# Regular items are handled in the main function
        if maps['Tier'] < 17:
            self._process_purchase_costs(
                self.rr['MapPurchaseCosts.dat'].index['Tier'][maps['Tier']],
                infobox
            )"""

    def _map_fragment_extra(self, infobox, base_item_type, map_fragment_mods):
        if map_fragment_mods["ModsKeys"]:
            i = 1
            while infobox.get("implicit%s" % i) is not None:
                i += 1
            for mod in map_fragment_mods["ModsKeys"]:
                infobox["implicit%s" % i] = mod["Id"]
                i += 1

    def _essence_extra(self, infobox, base_item_type, essence):
        infobox["is_essence"] = True

        #
        # Essence description
        #
        get_str = lambda k: self.rr["ClientStrings.dat"].index["Id"]["EssenceCategory%s" % k][
            "Text"
        ]

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

        out = []

        if essence["ItemLevelRestriction"] != 0:
            out.append(
                self.rr["ClientStrings.dat"]
                .index["Id"]["EssenceModLevelRestriction"]["Text"]
                .replace("{0}", str(essence["ItemLevelRestriction"]))
            )
            out[-1] += "<br />"

        def add_line(text, mod):
            nonlocal out
            out.append("%s: %s" % (text, "".join(self._get_stats(mod=mod))))

        item_mod = essence["Display_Items_ModsKey"]

        for category, rows in essence_categories.items():
            if category is None:
                category_mod = None
            else:
                category_mod = essence["Display_%s_ModsKey" % category]

            cur = len(out)
            for row_key in rows:
                mod = essence["Display_%s_ModsKey" % row_key]
                if mod is None:
                    continue
                if mod == category_mod:
                    continue
                if mod == item_mod:
                    continue

                add_line(get_str(row_key), mod)

            if category_mod is not None and category_mod != item_mod:
                text = get_str(category)
                if cur != len(out):
                    text = get_str("Other").replace("{0}", text)
                add_line(text, category_mod)

        if item_mod:
            # TODO: Can't find items in clientstrings
            add_line(get_str("Other").replace("{0}", "Items"), item_mod)

        infobox["description"] += "<br />" + "<br />".join(out)

        return True

    def _harvest_seed_extra(self, infobox, base_item_type, harvest_object):
        if not self.rr["HarvestSeedTypes.dat"].index.get("HarvestObjectsKey"):
            self.rr["HarvestSeedTypes.dat"].build_index("HarvestObjectsKey")

        harvest_seed = self.rr["HarvestSeedTypes.dat"].index["HarvestObjectsKey"][
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
                        "format": lambda v: ",".join([k["Id"] for k in v]),
                        "condition": lambda v: v,
                    },
                ),
            ),
            harvest_seed,
        )

        return True

    def _harvest_plant_booster_extra(self, infobox, base_item_type, harvest_object):
        if not self.rr["HarvestSeedTypes.dat"].index.get("HarvestObjectsKey"):
            self.rr["HarvestSeedTypes.dat"].build_index("HarvestObjectsKey")

        harvest_plant_booster = self.rr["HarvestPlantBoosters.dat"].index["HarvestObjectsKey"][
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
