"""
Item Conflict Resolver.

Handles conflict resolution for items when exporting to wiki format.
Extracted from ConflictsMixin for better separation of concerns.

This class uses composition instead of inheritance, making it easier to test
and maintain.
"""

import re
from collections.abc import Callable
from typing import Any

from PyPoE.cli.core import Msg, console


class ItemConflictResolver:
    """
    Resolves conflicts between items when exporting to wiki.

    This class handles special cases where items may conflict with each other
    or need special formatting (e.g., quest items, maps, divination cards).

    Attributes:
        rr: RelationalReader instance for data access
        language: Language code for translations
        lang_map: Language mapping dictionary
    """

    def __init__(
        self,
        relational_reader: Any,
        language: str,
        lang_map: dict[str, dict[str, str]],
        format_map_name: Callable[[Any, Any | None], str] | None = None,
    ):
        """
        Initialize conflict resolver.

        Args:
            relational_reader: RelationalReader instance
            language: Language code
            lang_map: Language mapping dictionary
            format_map_name: Optional function to format map names
        """
        self.rr = relational_reader
        self.language = language
        self.lang_map = lang_map
        self._format_map_name = format_map_name or self._default_format_map_name

    def resolve_conflict(
        self,
        item_type: str,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """
        Resolve conflict for given item type.

        Args:
            item_type: Item type (e.g., "QuestItem", "Map", "DivinationCard")
            infobox: Infobox dictionary to update
            base_item_type: Base item type data

        Returns:
            Resolved name string or None if no conflict
        """
        resolver_map = {
            "Active Skill Gem": self._resolve_active_skill_gems,
            "QuestItem": self._resolve_quest_items,
            "HideoutDoodad": self._resolve_hideout_doodad,
            "Map": self._resolve_maps,
            "MapFragment": self._resolve_map_fragments,
            "DivinationCard": self._resolve_divination_card,
            "LabyrinthMapItem": self._resolve_labyrinth_map_item,
            "MiscMapItem": self._resolve_misc_map_item,
            "DelveSocketableCurrency": self._resolve_delve_socketable_currency,
            "DelveStackableSocketableCurrency": self._resolve_delve_stackable_socketable_currency,
            "AtlasRegionUpgradeItem": self._resolve_atlas_region_upgrade,
        }

        resolver = resolver_map.get(item_type)
        if resolver:
            return resolver(infobox, base_item_type)

        return None

    def _default_format_map_name(self, base_item_type: Any, map_series: Any | None) -> str:
        """Default implementation of format_map_name."""
        # This should be implemented by the caller or injected
        return base_item_type["Name"]

    def _resolve_quest_items(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for quest items."""
        qid = base_item_type["Id"].replace("Metadata/Items/QuestItems/", "")
        match = re.match(r"(?:SkillBooks|Act[0-9]+)/Book-(?P<id>.*)", qid)
        if match:
            qid = match.group("id")
            ver = re.findall(r"v[0-9]$", qid)
            # Only need one of the skill books from "choice" quests
            if ver:
                if ver[0] != "v0":
                    return None
                qid = qid.replace(ver[0], "")

            try:
                return str(base_item_type["Name"])  # type: ignore[no-any-return] + " ({})".format(
                    self.rr["Quest.dat"].index["Id"][qid]["Name"]
                )
            except KeyError:
                console(f"Quest {qid} not found", msg=Msg.error)
                return None
        else:
            # Descent skill books
            match = re.match(r"SkillBooks/Descent2_(?P<id>[0-9]+)", qid)
            if match:
                return str(base_item_type["Name"])  # type: ignore[no-any-return] + " ({} {})".format(
                    self.lang_map[self.language]["descent"],
                    match.group("id"),
                )
            else:
                # Bandit respec
                match = re.match(r"SkillBooks/BanditRespec(?P<id>.+)", qid)
                if match:
                    return str(base_item_type["Name"]) + " ({})".format(match.group("id"))  # type: ignore[no-any-return]
                else:
                    match = re.match(
                        r"Metadata/Items/QuestItems/Act7/Firefly(?P<id>[0-9]+)$",
                        base_item_type["Id"],
                    )
                    if match:
                        pageid = "{} ({})".format(
                            base_item_type["Name"],
                            self.lang_map[self.language]["of"] % (match.group("id"), 7),
                        )
                        infobox["inventory_icon"] = pageid
                        return pageid

        return None

    def _resolve_hideout_doodad(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for hideout doodads."""
        try:
            ho = self.rr["HideoutDoodads.dat"].index["BaseItemTypesKey"][base_item_type.rowid]
        except KeyError:
            return None

        # This is not perfect, but works currently.
        if ho["HideoutNPCsKey"]:
            if base_item_type["Id"].startswith("Metadata/Items/Hideout/HideoutWounded"):
                name_fmt = self.lang_map[self.language]["decoration_wounded"]
            else:
                name_fmt = self.lang_map[self.language]["decoration"]
            name = name_fmt % (
                base_item_type["Name"],
                ho["HideoutNPCsKey"]["Hideout_NPCsKey"]["ShortName"],
                ho["MasterLevel"],
            )
            infobox["inventory_icon"] = name
            return name
        elif base_item_type["Id"].startswith("Metadata/Items/Hideout/HideoutTotemPole"):
            # Ignore the test doodads on purpose
            if base_item_type["Id"].endswith("Test"):
                return None

            return str(base_item_type["Name"])  # type: ignore[no-any-return]

        return None

    def _resolve_maps(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for maps."""
        map_id = base_item_type["Id"].replace("Metadata/Items/Maps/", "")
        # Legacy maps
        map_series = None
        for row in self.rr["MapSeries.dat"]:
            if not map_id.startswith(row["Id"]):
                continue
            map_series = row

        name = self._format_map_name(base_item_type, map_series)

        # Each iteration of maps has it's own art
        infobox["inventory_icon"] = name
        # For betrayal map conflict handling is not used, so setting this to
        # false here should be fine
        infobox["drop_enabled"] = False

        return name

    def _resolve_map_fragments(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for map fragments."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def _resolve_divination_card(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for divination cards."""
        return "{} ({})".format(
            base_item_type["Name"],
            base_item_type["ItemClassesKey"]["Name"].lower(),
        )

    def _resolve_labyrinth_map_item(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for labyrinth map items."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def _resolve_misc_map_item(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for misc map items."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def _resolve_delve_socketable_currency(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for delve socketable currency."""
        return None

    def _resolve_delve_stackable_socketable_currency(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for delve stackable socketable currency."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def _resolve_atlas_region_upgrade(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for atlas region upgrade items."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def _resolve_active_skill_gems(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """Resolve conflict for active skill gems."""
        # Implementation from ConflictsMixin (if exists)
        return None

