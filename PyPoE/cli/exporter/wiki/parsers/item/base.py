"""
Base classes and helper functions for item wiki export

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/item/base.py                    |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Contains WikiCondition classes and helper functions used by item parsers.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re
import warnings

# Self
from PyPoE.cli.exporter.wiki import parser

# =============================================================================
# Functions
# =============================================================================


def _apply_column_map(infobox, column_map, list_object):
    for k, data in column_map:
        value = list_object[k]
        if data.get("condition") and not data["condition"](value):
            continue

        if data.get("format"):
            value = data["format"](value)
        infobox[data["template"]] = value


def _type_factory(data_file, data_mapping, row_index=True, function=None, fail_condition=False):
    def func(self, infobox, base_item_type):
        try:
            data = self.rr[data_file].index["BaseItemTypesKey"][
                base_item_type.rowid if row_index else base_item_type["Id"]
            ]
        except KeyError:
            warnings.warn(
                'Missing {} info for "{}"'.format(data_file, base_item_type["Name"]), stacklevel=2
            )
            return fail_condition

        _apply_column_map(infobox, data_mapping, data)

        if function:
            # Support both callable and string (method name)
            if isinstance(function, str):
                getattr(self, function)(infobox, base_item_type, data)
            else:
                function(self, infobox, base_item_type, data)

        return True

    return func


def _simple_conflict_factory(data):
    def _conflict_handler(self, infobox, base_item_type):
        appendix = data.get(base_item_type["Id"])
        if appendix is None:
            return base_item_type["Name"]
        else:
            return base_item_type["Name"] + appendix

    return _conflict_handler


# =============================================================================
# Classes
# =============================================================================


class WikiCondition(parser.WikiCondition):
    COPY_KEYS = (  # type: ignore[assignment]
        # for skills
        "radius",
        "radius_description",
        "radius_secondary",
        "radius_secondary_description",
        "radius_tertiary",
        "radius_tertiary_description",
        "has_percentage_mana_cost",
        "has_reservation_mana_cost",
        #
        # all items
        #
        "name_list",
        "quality",
        # Icons
        "inventory_icon",
        "alternate_art_inventory_icons",
        # Drop restrictions
        "drop_enabled",
        "drop_leagues",
        "drop_areas",
        "drop_text",
        "drop_monsters",
        "upgraded_from_disabled",
        "is_drop_restricted",
        "influences",
        # Item flags
        "is_corrupted",
        "is_relic",
        "can_not_be_traded_or_modified",
        "suppress_improper_modifiers_category",
        # Version information
        "release_version",
        "removal_version",
        # prophecies
        "prophecy_objective",
        "prophecy_reward",
    )
    COPY_MATCH = re.compile(  # type: ignore[assignment]
        r"^(upgraded_from_set|implicit[0-9]+_(?:text|random_list)).*", re.UNICODE
    )

    NAME = "Base item"  # type: ignore[assignment]
    INDENT = 40
    ADD_INCLUDE = False


class ItemWikiCondition(WikiCondition):
    NAME = "Base item"


class MapItemWikiCondition(WikiCondition):
    NAME = "Base item"


class UniqueMapItemWikiCondition(MapItemWikiCondition):
    NAME = "Item"
    COPY_MATCH = re.compile(  # type: ignore[assignment]
        r"^(upgraded_from_set|(ex|im)plicit[0-9]+_(?:text|random_list)).*", re.UNICODE
    )


class ProphecyWikiCondition(WikiCondition):
    NAME = "Item"


__all__ = [
    "_apply_column_map",
    "_type_factory",
    "_simple_conflict_factory",
    "WikiCondition",
    "ItemWikiCondition",
    "MapItemWikiCondition",
    "UniqueMapItemWikiCondition",
    "ProphecyWikiCondition",
]
