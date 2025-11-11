"""
ConflictsMixin for ItemsParser.

Contains conflicts-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

import re
from typing import TYPE_CHECKING, Any

from PyPoE.cli.core import Msg, console

# =============================================================================
# Classes
# =============================================================================


class ConflictsMixin:
    """Mixin providing conflicts methods for ItemsParser."""

    # Type hints for attributes from parent ItemsParser class
    if TYPE_CHECKING:
        rr: Any
        _LANG: dict[str, dict[str, str]]
        _language: str

        def _format_map_name(self, *args: Any, **kwargs: Any) -> str: ...

    def _conflict_quest_items(self, infobox, base_item_type, rr, language):
        qid = base_item_type["Id"].replace("Metadata/Items/QuestItems/", "")
        match = re.match(r"(?:SkillBooks|Act[0-9]+)/Book-(?P<id>.*)", qid)
        if match:
            qid = match.group("id")
            ver = re.findall(r"v[0-9]$", qid)
            # Only need one of the skill books from "choice" quets
            if ver:
                if ver[0] != "v0":
                    return
                qid = qid.replace(ver[0], "")

            try:
                return base_item_type["Name"] + " ({})".format(
                    rr["Quest.dat"].index["Id"][qid]["Name"]
                )
            except KeyError:
                console(f"Quest {qid} not found", msg=Msg.error)
        else:
            # Descent skill books
            match = re.match(r"SkillBooks/Descent2_(?P<id>[0-9]+)", qid)
            if match:
                return base_item_type["Name"] + " ({} {})".format(
                    self._LANG[language]["descent"],
                    match.group("id"),
                )
            else:
                # Bandit respec
                match = re.match(r"SkillBooks/BanditRespec(?P<id>.+)", qid)
                if match:
                    return base_item_type["Name"] + " ({})".format(match.group("id"))
                else:
                    match = re.match(
                        r"Metadata/Items/QuestItems/Act7/Firefly(?P<id>[0-9]+)$",
                        base_item_type["Id"],
                    )
                    if match:
                        pageid = "{} ({})".format(
                            base_item_type["Name"],
                            self._LANG[language]["of"] % (match.group("id"), 7),
                        )
                        infobox["inventory_icon"] = pageid
                        return pageid

        return

    def _conflict_hideout_doodad(self, infobox, base_item_type, rr, language):
        try:
            ho = rr["HideoutDoodads.dat"].index["BaseItemTypesKey"][base_item_type.rowid]
        except KeyError:
            return

        # This is not perfect, but works currently.
        if ho["HideoutNPCsKey"]:
            if base_item_type["Id"].startswith("Metadata/Items/Hideout/HideoutWounded"):
                name_fmt = self._LANG[self._language]["decoration_wounded"]
            else:
                name_fmt = self._LANG[self._language]["decoration"]
            name = name_fmt % (
                base_item_type["Name"],
                ho["HideoutNPCsKey"]["Hideout_NPCsKey"]["ShortName"],
                ho["MasterLevel"],
            )
            infobox["inventory_icon"] = name
            return name
        elif base_item_type["Id"].startswith("Metadata/Items/Hideout/HideoutTotemPole"):
            # Ingore the test doodads on purpose
            if base_item_type["Id"].endswith("Test"):
                return

            return base_item_type["Name"]

    def _conflict_maps(self, infobox, base_item_type, rr, language):
        id = base_item_type["Id"].replace("Metadata/Items/Maps/", "")
        # Legacy maps
        map_series = None
        for row in rr["MapSeries.dat"]:
            if not id.startswith(row["Id"]):
                continue
            map_series = row

        name = self._format_map_name(base_item_type, map_series)

        # Each iteration of maps has it's own art
        infobox["inventory_icon"] = name
        # For betrayal map conflict handling is not used, so setting this to
        # false here should be fine
        infobox["drop_enabled"] = False

        return name

    def _conflict_map_fragments(self, infobox, base_item_type, rr, language):
        return base_item_type["Name"]

    def _conflict_divination_card(self, infobox, base_item_type, rr, language):
        return "{} ({})".format(
            base_item_type["Name"],
            base_item_type["ItemClassesKey"]["Name"].lower(),
        )

    def _conflict_labyrinth_map_item(self, infobox, base_item_type, rr, language):
        return base_item_type["Name"]

    def _conflict_misc_map_item(self, infobox, base_item_type, rr, language):
        return base_item_type["Name"]

    def _conflict_delve_socketable_currency(self, infobox, base_item_type, rr, language):
        return

    def _conflict_delve_stackable_socketable_currency(self, infobox, base_item_type, rr, language):
        return base_item_type["Name"]

    def _conflict_atlas_region_upgrade(self, infobox, base_item_type, rr, language):
        return base_item_type["Name"]
