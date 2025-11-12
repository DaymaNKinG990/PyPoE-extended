"""
Item Skill Handler.

Handles skill-related items (skill gems) when exporting to wiki format.
Extracted from SkillsMixin for better separation of concerns.

This class uses composition instead of inheritance, making it easier to test
and maintain.
"""

import contextlib
import warnings
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from PyPoE.cli.core import Msg, console
from PyPoE.poe.sim.formula import GemTypes, gem_stat_requirement


class ItemSkillHandler:
    """
    Handles skill-related items (skill gems).

    This class processes skill gems, extracting their properties,
    experience progression, and stat requirements.

    Attributes:
        rr: RelationalReader instance for data access
        language: Language code for translations
        attribute_map: Attribute mapping dictionary
        conflict_active_skill_gems_map: Conflict resolution map for active skill gems
    """

    def __init__(
        self,
        relational_reader: Any,
        language: str,
        attribute_map: dict[str, str],
        conflict_active_skill_gems_map: dict[str, bool],
        *,
        skill_processor: Callable[[Any, OrderedDict[str, Any], Any, str, int], bool] | None = None,
        parsed_args: Any | None = None,
    ):
        """
        Initialize skill handler.

        Args:
            relational_reader: RelationalReader instance
            language: Language code
            attribute_map: Attribute mapping dictionary
            conflict_active_skill_gems_map: Conflict resolution map for active skill gems
            skill_processor: Optional function to process skills
            parsed_args: Optional parsed command-line arguments
        """
        self.rr = relational_reader
        self.language = language
        self.attribute_map = attribute_map
        self.conflict_active_skill_gems_map = conflict_active_skill_gems_map
        self._skill = skill_processor or (lambda ge, infobox, parsed_args, msg_name, max_level: True)
        self._parsed_args = parsed_args

    def process_skill_gem(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> bool:
        """
        Process skill gem and populate infobox.

        Args:
            infobox: Infobox dictionary to populate
            base_item_type: Base item type data

        Returns:
            True if successful, False otherwise
        """
        try:
            skill_gem = self.rr["SkillGems.dat"].index["BaseItemTypesKey"][base_item_type.rowid]
        except KeyError:
            return False

        # SkillGems.dat
        for attr_short, attr_long in self.attribute_map.items():
            if not skill_gem[attr_short]:  # type: ignore[index]
                continue
            infobox[attr_long + "_percent"] = skill_gem[attr_short]  # type: ignore[index]

        infobox["gem_tags"] = ", ".join(
            [gt["Tag"] for gt in skill_gem["GemTagsKeys"] if gt["Tag"]]  # type: ignore[index]
        )

        # Experience progression
        exp = 0
        exp_level: list[int] = []
        exp_total: list[int] = []
        for row in self.rr["ItemExperiencePerLevel.dat"]:
            if row["BaseItemTypesKey"] == base_item_type:
                exp_new = row["Experience"]
                exp_level.append(exp_new - exp)
                exp_total.append(exp_new)
                exp = exp_new

        if not exp_level:
            console(
                'No experience progression found for "{}" - assuming max level 1'.format(
                    base_item_type["Name"]
                ),
                msg=Msg.error,
            )
            exp_total = [0]

        max_level = len(exp_total) - 1
        ge = skill_gem["GrantedEffectsKey"]  # type: ignore[index]

        primary: OrderedDict[str, Any] = OrderedDict()
        if self._parsed_args is None:
            console("Parsed args not set", msg=Msg.error)
            return False

        self._skill(  # type: ignore[call-arg]
            ge=ge,
            infobox=primary,
            parsed_args=self._parsed_args,
            msg_name=base_item_type["Name"],
            max_level=max_level,
        )

        # Some skills have a secondary skill effect.
        # Currently there is no great way of handling this in the wiki, so the
        # secondary effects are just added. Skills that have their own entry
        # are excluded so we don't get vaal skill gems here.
        second = False
        if skill_gem["GrantedEffectsKey2"]:  # type: ignore[index]
            index = None
            try:
                index = self.rr["SkillGems.dat"].index["GrantedEffectsKey"]
            except KeyError:
                self.rr["SkillGems.dat"].build_index("GrantedEffectsKey")
                index = self.rr["SkillGems.dat"].index["GrantedEffectsKey"]

            if not index[skill_gem["GrantedEffectsKey2"]]:  # type: ignore[index]
                # If there is no skill granting this it's probably fine to include.
                second = True

        if second:
            secondary: OrderedDict[str, Any] = OrderedDict()
            self._skill(  # type: ignore[call-arg]
                ge=skill_gem["GrantedEffectsKey2"],  # type: ignore[index]
                infobox=secondary,
                parsed_args=self._parsed_args,
                msg_name=base_item_type["Name"],
                max_level=max_level,
            )

            for k, v in list(primary.items()) + list(secondary.items()):
                # Just override the stuff if needs be.
                if "stat" not in k:
                    infobox[k] = v

            infobox["stat_text"] = "<br>".join(
                [x for x in (primary.get("stat_text"), secondary.get("stat_text")) if x]
            )

            # Stat merging...
            def get_stat(i: int, prefix: str, data: dict[str, Any]) -> tuple[str, Any]:
                return (data[f"{prefix}_stat{i}_id"], data[f"{prefix}_stat{i}_value"])

            def set_stat(i: int, prefix: str, sid: str, sv: Any) -> None:
                infobox[f"{prefix}_stat{i}_id"] = sid
                infobox[f"{prefix}_stat{i}_value"] = sv

            def cp_stats(prefix: str) -> None:
                i = 1
                while True:
                    try:
                        sid, sv = get_stat(i, prefix, primary)
                    except KeyError:
                        break
                    set_stat(i, prefix, sid, sv)
                    i += 1

                j = 1
                while True:
                    try:
                        sid, sv = get_stat(j, prefix, secondary)
                    except KeyError:
                        break
                    set_stat(j + i - 1, prefix, sid, sv)
                    j += 1

            cp_stats("static")
            lv = 1
            while True:
                prefix = f"level{lv}"
                try:
                    primary[prefix]  # type: ignore[index]
                except KeyError:
                    break

                for k in ("_stat_text",):
                    k_full = prefix + k
                    infobox[k_full] = "<br>".join(
                        [x[k_full] for x in (primary, secondary) if k_full in x]
                    )
                cp_stats(prefix)

                lv += 1
        else:
            for k, v in primary.items():
                infobox[k] = v

        # Some descriptions come from active skills which are parsed in above function
        if "gem_description" not in infobox:
            infobox["gem_description"] = skill_gem["Description"].replace("\n", "<br")  # type: ignore[index]

        # Output handling for progression
        map2 = {
            "Str": "strength_requirement",
            "Int": "intelligence_requirement",
            "Dex": "dexterity_requirement",
        }

        if base_item_type["ItemClassesKey"]["Id"] == "Active Skill Gem":  # type: ignore[index]
            gtype = GemTypes.active
        elif base_item_type["ItemClassesKey"]["Id"] == "Support Skill Gem":  # type: ignore[index]
            gtype = GemTypes.support
        else:
            gtype = GemTypes.active  # Default fallback

        # +1 for gem levels starting at 1
        # +1 for being able to corrupt gems to +1 level
        # +1 for python counting only up to, but not including the number
        for i in range(1, max_level + 3):
            prefix = f"level{i}_"
            for attr in ("Str", "Dex", "Int"):
                if skill_gem[attr]:  # type: ignore[index]
                    try:
                        infobox[prefix + map2[attr]] = gem_stat_requirement(
                            level=infobox[prefix + "level_requirement"],
                            gtype=gtype,
                            multi=skill_gem[attr],  # type: ignore[index]
                        )
                    except ValueError as e:
                        warnings.warn(str(e), stacklevel=2)
                    except KeyError:
                        print(base_item_type["Id"], base_item_type["Name"])
                        raise
                    # Index starts at 0 while levels start at 1
                    with contextlib.suppress(IndexError):
                        infobox[prefix + "experience"] = exp_total[i - 1]

        return True

    def resolve_active_skill_gem_conflict(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
    ) -> str | None:
        """
        Resolve conflict for active skill gems.

        Args:
            infobox: Infobox dictionary to update
            base_item_type: Base item type data

        Returns:
            Resolved name string or None if no conflict
        """
        appendix = self.conflict_active_skill_gems_map.get(base_item_type["Id"])  # type: ignore[index]
        if appendix is None:
            return None
        else:
            return str(base_item_type["Name"])  # type: ignore[no-any-return]

