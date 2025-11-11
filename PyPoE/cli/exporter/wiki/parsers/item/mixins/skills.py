"""
SkillsMixin for ItemsParser.

Contains skills-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

import warnings
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from PyPoE.cli.core import Msg, console
from PyPoE.poe.sim.formula import GemTypes, gem_stat_requirement

# =============================================================================
# Classes
# =============================================================================


class SkillsMixin:
    """Mixin providing skills methods for ItemsParser."""

    # Type hints for attributes from parent ItemsParser class
    if TYPE_CHECKING:
        rr: Any
        _LANG: dict[str, dict[str, str]]
        _language: str
        _parsed_args: Any
        _attribute_map: Any
        _conflict_active_skill_gems_map: Any

        def _skill(self, *args: Any, **kwargs: Any) -> bool: ...

    def _skill_gem(self, infobox, base_item_type):
        try:
            skill_gem = self.rr["SkillGems.dat"].index["BaseItemTypesKey"][base_item_type.rowid]
        except KeyError:
            return False

        # SkillGems.dat
        for attr_short, attr_long in self._attribute_map.items():
            if not skill_gem[attr_short]:
                continue
            infobox[attr_long + "_percent"] = skill_gem[attr_short]

        infobox["gem_tags"] = ", ".join([gt["Tag"] for gt in skill_gem["GemTagsKeys"] if gt["Tag"]])

        # No longer used
        #

        # TODO: Maybe catch empty stuff here?
        exp = 0
        exp_level = []
        exp_total = []
        for row in self.rr["ItemExperiencePerLevel.dat"]:
            if row["BaseItemTypesKey"] == base_item_type:
                exp_new = row["Experience"]
                exp_level.append(exp_new - exp)
                exp_total.append(exp_new)
                exp = exp_new

        if not exp_level:
            console(
                'No experience progression found for "%s" - assuming max '
                "level 1" % base_item_type["Name"],
                msg=Msg.error,
            )
            exp_total = [0]

        max_level = len(exp_total) - 1
        ge = skill_gem["GrantedEffectsKey"]

        primary: OrderedDict[str, Any] = OrderedDict()
        self._skill(
            ge=ge,
            infobox=primary,
            parsed_args=self._parsed_args,
            msg_name=base_item_type["Name"],
            max_level=max_level,
        )

        # Some skills have a secondary skill effect.
        #
        # Currently there is no great way of handling this in the wiki, so the
        # secondary effects are just added. Skills that have their own entry
        # are excluded so we don't get vaal skill gems here.
        second = False
        if skill_gem["GrantedEffectsKey2"]:
            index = None
            try:
                index = self.rr["SkillGems.dat"].index["GrantedEffectsKey"]
            except KeyError:
                self.rr["SkillGems.dat"].build_index("GrantedEffectsKey")
                index = self.rr["SkillGems.dat"].index["GrantedEffectsKey"]

            if not index[skill_gem["GrantedEffectsKey2"]]:
                # If there is no skill granting this it's probably fine to
                # include.
                second = True

        if second:
            secondary: OrderedDict[str, Any] = OrderedDict()
            self._skill(
                ge=skill_gem["GrantedEffectsKey2"],
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
                [x for x in (primary["stat_text"], secondary["stat_text"]) if x]
            )

            # Stat merging...
            def get_stat(i, prefix, data):
                return (data["%s_stat%s_id" % (prefix, i)], data["%s_stat%s_value" % (prefix, i)])

            def set_stat(i, prefix, sid, sv):
                infobox["%s_stat%s_id" % (prefix, i)] = sid
                infobox["%s_stat%s_value" % (prefix, i)] = sv

            def cp_stats(prefix):
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
                prefix = "level%s" % lv
                try:
                    primary[prefix]
                except KeyError:
                    break

                for k in ("_stat_text",):
                    k = prefix + k
                    infobox[k] = "<br>".join([x[k] for x in (primary, secondary) if k in x])
                cp_stats(prefix)

                lv += 1
        else:
            for k, v in primary.items():
                infobox[k] = v

        # some descriptions come from active skills which are parsed in above
        # function
        if "gem_description" not in infobox:
            infobox["gem_description"] = skill_gem["Description"].replace("\n", "<br>")

        #
        # Output handling for progression
        #

        # Body
        map2 = {
            "Str": "strength_requirement",
            "Int": "intelligence_requirement",
            "Dex": "dexterity_requirement",
        }

        if base_item_type["ItemClassesKey"]["Id"] == "Active Skill Gem":
            gtype = GemTypes.active
        elif base_item_type["ItemClassesKey"]["Id"] == "Support Skill Gem":
            gtype = GemTypes.support

        # +1 for gem levels starting at 1
        # +1 for being able to corrupt gems to +1 level
        # +1 for python counting only up to, but not including the number
        for i in range(1, max_level + 3):
            prefix = "level%s_" % i
            for attr in ("Str", "Dex", "Int"):
                if skill_gem[attr]:
                    try:
                        infobox[prefix + map2[attr]] = gem_stat_requirement(
                            level=infobox[prefix + "level_requirement"],
                            gtype=gtype,
                            multi=skill_gem[attr],
                        )
                    except ValueError as e:
                        warnings.warn(str(e))
                    except KeyError:
                        print(base_item_type["Id"], base_item_type["Name"])
                        raise
            try:
                # Index starts at 0 while levels start at 1
                infobox[prefix + "experience"] = exp_total[i - 1]
            except IndexError:
                pass

        return True

    def _conflict_active_skill_gems(self, infobox, base_item_type, rr, language):
        appendix = self._conflict_active_skill_gems_map.get(base_item_type["Id"])
        if appendix is None:
            return
        else:
            return base_item_type["Name"]
