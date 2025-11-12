"""
Items wiki parser

Contains ItemsParser class for exporting items to wiki format.
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re
from collections import OrderedDict
from functools import partialmethod
from typing import Any

from PyPoE.cli.exporter.wiki.parsers.item.base import (
    _type_factory,
)

# Specialized classes (composition)
from PyPoE.cli.exporter.wiki.parsers.item.conflict_resolver import ItemConflictResolver
from PyPoE.cli.exporter.wiki.parsers.item.data_extractor import ItemDataExtractor
from PyPoE.cli.exporter.wiki.parsers.item.skill_handler import ItemSkillHandler
from PyPoE.cli.exporter.wiki.parsers.item.type_parser import ItemTypeParser
from PyPoE.cli.exporter.wiki.parsers.item.wiki_exporter import ItemWikiExporter
from PyPoE.cli.exporter.wiki.parsers.skill import SkillParserShared

# Self

# =============================================================================
# Classes
# =============================================================================


class ItemsParser(SkillParserShared):  # type: ignore[misc]
    # === Class attributes from mixins ===

    # From conflicts.py
    # Note: _conflict_resolver_map is now created in __init__ after _conflict_resolver is created
    # It's initialized as empty dict here, then populated in __init__
    _conflict_resolver_map: dict[str, Any] = {}

    # From extras.py
    _type_currency = _type_factory(
        data_file="CurrencyItems.dat",
        data_mapping=(
            (
                "Stacks",
                {
                    "template": "stack_size",
                    "condition": None,
                },
            ),
            (
                "Description",
                {
                    "template": "description",
                    "condition": lambda v: v,
                },
            ),
            (
                "Directions",
                {
                    "template": "help_text",
                    "condition": lambda v: v,
                },
            ),
            (
                "CurrencyTab_StackSize",
                {
                    "template": "stack_size_currency_tab",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "CosmeticTypeName",
                {
                    "template": "cosmetic_type",
                    "condition": lambda v: v,
                },
            ),
        ),
        row_index=True,
        function="_currency_extra",
    )

    # From extras.py
    _master_hideout_doodad_map = (
        (
            "HideoutNPCsKey",
            {
                "template": "master",
                "format": lambda v: v["Hideout_NPCsKey"]["Name"],
                "condition": lambda v: v is not None,
            },
        ),
        (
            "MasterLevel",
            {
                "template": "master_level_requirement",
            },
        ),
        (
            "FavourCost",
            {
                "template": "master_favour_cost",
            },
        ),
    )

    # From extras.py
    _type_map = _type_factory(
        data_file="Maps.dat",
        data_mapping=(
            (
                "Tier",
                {
                    "template": "map_tier",
                },
            ),
            (
                "Regular_GuildCharacter",
                {
                    "template": "map_guild_character",
                    "condition": lambda v: v,
                },
            ),
            (
                "Regular_WorldAreasKey",
                {
                    "template": "map_area_id",
                    "format": lambda v: v["Id"],
                },
            ),
            (
                "Unique_GuildCharacter",
                {
                    "template": "unique_map_guild_character",
                    "condition": lambda v: v != "",
                },
            ),
            (
                "Unique_WorldAreasKey",
                {
                    "template": "unique_map_area_id",
                    "format": lambda v: v["Id"],
                    "condition": lambda v: v is not None,
                },
            ),
            (
                "Unique_WorldAreasKey",
                {
                    "template": "unique_map_area_level",
                    "format": lambda v: v["AreaLevel"],
                    "condition": lambda v: v is not None,
                },
            ),
            (
                "MapSeriesKey",
                {
                    "template": "map_series",
                    "format": lambda v: v["Name"],
                },
            ),
        ),
        row_index=True,
        function="_maps_extra",
    )

    # From extras.py
    _type_map_fragment_mods = _type_factory(
        data_file="MapFragmentMods.dat",
        data_mapping={},
        row_index=True,
        function="_map_fragment_extra",
        fail_condition=True,
    )

    # From extras.py
    _type_essence = _type_factory(
        data_file="Essences.dat",
        data_mapping=(
            (
                "DropLevelMinimum",
                {
                    "template": "drop_level",
                },
            ),
            (
                "DropLevelMaximum",
                {
                    "template": "drop_level_maximum",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "ItemLevelRestriction",
                {
                    "template": "essence_level_restriction",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "Level",
                {
                    "template": "essence_level",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "EssenceTypeKey",
                {
                    "template": "essence_type",
                    "format": lambda v: v["EssenceType"],
                },
            ),
            (
                "EssenceTypeKey",
                {
                    "template": "essence_category",
                    "format": lambda v: v["WordsKey"]["Text"],
                },
            ),
            (
                "Monster_ModsKeys",
                {
                    "template": "essence_monster_modifier_ids",
                    "format": lambda v: ", ".join([m["Id"] for m in v]),
                    "condition": lambda v: v,
                },
            ),
        ),
        row_index=True,
        function="_essence_extra",
        fail_condition=True,
    )

    # From extras.py
    _type_blight_item = _type_factory(
        data_file="BlightCraftingItems.dat",
        data_mapping=(
            (
                "Tier",
                {
                    "template": "blight_item_tier",
                },
            ),
        ),
        row_index=True,
        fail_condition=True,
    )

    # From extras.py
    _type_labyrinth_trinket = _type_factory(
        data_file="LabyrinthTrinkets.dat",
        data_mapping=(
            (
                "Buff_BuffDefinitionsKey",
                {
                    "template": "description",
                    "format": lambda v: v["Description"],
                },
            ),
        ),
        row_index=True,
    )

    # From extras.py
    _type_incubator = _type_factory(
        data_file="Incubators.dat",
        data_mapping=(
            (
                "Description",
                {
                    "template": "incubator_effect",
                    "format": lambda v: v,
                },
            ),
        ),
        row_index=True,
    )

    # From extras.py
    _type_harvest_seed = _type_factory(
        data_file="HarvestObjects.dat",
        data_mapping=(
            (
                "ObjectType",
                {
                    "template": "seed_type_id",
                    "format": lambda v: v.name.lower(),
                },
            ),
        ),
        function="_harvest_seed_extra",
        # fail_condition=True,
        row_index=True,
    )

    # From extras.py
    _type_harvest_plant_booster = _type_factory(
        data_file="HarvestObjects.dat",
        data_mapping=(),
        function="_harvest_plant_booster_extra",
        # fail_condition=True,
        row_index=True,
    )

    # From extras.py
    _type_heist_contract = _type_factory(
        data_file="HeistContracts.dat",
        data_mapping=(
            (
                "HeistAreasKey",
                {
                    "template": "heist_area_id",
                    "format": lambda v: v["Id"],
                },
            ),
        ),
        row_index=True,
    )

    # From extras.py
    _type_heist_equipment = _type_factory(
        data_file="HeistEquipment.dat",
        data_mapping=(
            (
                "RequiredJob_HeistJobsKey",
                {
                    "template": "heist_required_job_id",
                    "format": lambda v: v["Id"],
                    "condition": lambda v: v,
                },
            ),
            (
                "RequiredLevel",
                {
                    "template": "heist_required_job_level",
                    "condition": lambda v: v > 0,
                },
            ),
        ),
        row_index=True,
    )

    # From extras.py
    @property
    def _cls_map(self):
        return {
            # Jewellery
            "Amulet": (self._type_amulet,),
            # Armour types
            "Gloves": (
                self._type_level,
                self._type_attribute,
                self._type_armour,
            ),
            "Boots": (
                self._type_level,
                self._type_attribute,
                self._type_armour,
            ),
            "Body Armour": (
                self._type_level,
                self._type_attribute,
                self._type_armour,
            ),
            "Helmet": (
                self._type_level,
                self._type_attribute,
                self._type_armour,
            ),
            "Shield": (
                self._type_level,
                self._type_attribute,
                self._type_armour,
                self._type_shield,
            ),
            # Weapons
            "Claw": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Dagger": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Rune Dagger": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Wand": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "One Hand Sword": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Thrusting One Hand Sword": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "One Hand Axe": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "One Hand Mace": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Sceptre": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Bow": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Staff": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Two Hand Sword": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Two Hand Axe": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Two Hand Mace": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "Warstaff": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            "FishingRod": (
                self._type_level,
                self._type_attribute,
                self._type_weapon,
            ),
            # Flasks
            "LifeFlask": (self._type_level, self._type_flask, self._type_flask_charges),
            "ManaFlask": (self._type_level, self._type_flask, self._type_flask_charges),
            "HybridFlask": (self._type_level, self._type_flask, self._type_flask_charges),
            "UtilityFlask": (self._type_level, self._type_flask, self._type_flask_charges),
            "UtilityFlaskCritical": (self._type_level, self._type_flask, self._type_flask_charges),
            # Gems
            "Active Skill Gem": (self._skill_gem,),
            "Support Skill Gem": (self._skill_gem,),
            # Currency-like items
            "Currency": (self._type_currency,),
            "StackableCurrency": (self._type_currency, self._type_essence, self._type_blight_item),
            "DelveSocketableCurrency": (self._type_currency,),
            "DelveStackableSocketableCurrency": (self._type_currency,),
            "HideoutDoodad": (self._type_currency, self._type_hideout_doodad),
            "Microtransaction": (self._type_currency,),
            "DivinationCard": (self._type_currency,),
            "Incubator": (self._type_currency, self._type_incubator),
            "HarvestSeed": (self._type_currency, self._type_harvest_seed),
            "HarvestPlantBooster": (self._type_currency, self._type_harvest_plant_booster),
            # Labyrinth stuff
            #'LabyrinthItem': (),
            "LabyrinthTrinket": (self._type_labyrinth_trinket,),
            #'LabyrinthMapItem': (),
            # Misc
            "Map": (self._type_map,),
            "MapFragment": (self._type_map_fragment_mods,),
            "QuestItem": (),
            "AtlasRegionUpgradeItem": (),
            "MetamorphosisDNA": (),
            # heist league
            "HeistContract": (self._type_heist_contract,),
            "HeistEquipmentWeapon": (self._type_heist_equipment,),
            "HeistEquipmentTool": (self._type_heist_equipment,),
            "HeistEquipmentUtility": (self._type_heist_equipment,),
            "HeistEquipmentReward": (self._type_heist_equipment,),
            "HeistBlueprint": (),
            "Trinket": (),
            "HeistObjective": (),
        }

    # From extras.py
    _conflict_active_skill_gems_map = {
        "Metadata/Items/Gems/SkillGemArcticArmour": True,
        "Metadata/Items/Gems/SkillGemPhaseRun": True,
        "Metadata/Items/Gems/SkillGemLightningTendrils": True,
    }

    # From types.py
    _type_attribute = _type_factory(
        data_file="ComponentAttributeRequirements.dat",
        data_mapping=(
            (
                "ReqStr",
                {
                    "template": "required_strength",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "ReqDex",
                {
                    "template": "required_dexterity",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "ReqInt",
                {
                    "template": "required_intelligence",
                    "condition": lambda v: v > 0,
                },
            ),
        ),
        row_index=False,
    )

    # From types.py
    _type_armour = _type_factory(
        data_file="ComponentArmour.dat",
        data_mapping=(
            (
                "Armour",
                {
                    "template": "armour",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "Evasion",
                {
                    "template": "evasion",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "EnergyShield",
                {
                    "template": "energy_shield",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "IncreasedMovementSpeed",
                {
                    "template": "movement_speed",
                    "condition": lambda v: v != 0,
                },
            ),
        ),
        row_index=False,
    )

    # From types.py
    _type_shield = _type_factory(
        data_file="ShieldTypes.dat",
        data_mapping=(
            (
                "Block",
                {
                    "template": "block",
                },
            ),
        ),
        row_index=True,
    )

    # From utils.py
    _type_flask = _type_factory(
        data_file="Flasks.dat",
        data_mapping=(
            (
                "LifePerUse",
                {
                    "template": "flask_life",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "ManaPerUse",
                {
                    "template": "flask_mana",
                    "condition": lambda v: v > 0,
                },
            ),
            (
                "RecoveryTime",
                {
                    "template": "flask_duration",
                    "condition": lambda v: v > 0,
                    "format": lambda v: f"{v / 10:n}",
                },
            ),
            (
                "BuffDefinitionsKey",
                {
                    "template": "buff_id",
                    "condition": lambda v: v is not None,
                    "format": lambda v: v["Id"],
                },
            ),
        ),
        row_index=True,
        function="_apply_flask_buffs",
    )

    # From utils.py
    _type_flask_charges = _type_factory(
        data_file="ComponentCharges.dat",
        data_mapping=(
            (
                "MaxCharges",
                {
                    "template": "charges_max",
                },
            ),
            (
                "PerCharge",
                {
                    "template": "charges_per_use",
                },
            ),
        ),
        row_index=False,
    )

    # From utils.py
    _type_weapon = _type_factory(
        data_file="WeaponTypes.dat",
        data_mapping=(
            (
                "Critical",
                {
                    "template": "critical_strike_chance",
                    "format": lambda v: f"{v / 100:n}",
                },
            ),
            (
                "Speed",
                {
                    "template": "attack_speed",
                    "format": lambda v: f"{round(1000 / v, 2):n}",
                },
            ),
            (
                "DamageMin",
                {
                    "template": "physical_damage_min",
                },
            ),
            (
                "DamageMax",
                {
                    "template": "physical_damage_max",
                },
            ),
            (
                "RangeMax",
                {
                    "template": "weapon_range",
                },
            ),
        ),
        row_index=True,
    )

    # From utils.py
    _type_hideout_doodad = _type_factory(
        data_file="HideoutDoodads.dat",
        data_mapping=(
            (
                "IsNonMasterDoodad",
                {
                    "template": "is_master_doodad",
                    "format": lambda v: not v,
                },
            ),
            (
                "HideoutNPCsKey",
                {
                    "template": "master",
                    "format": lambda v: v["Hideout_NPCsKey"]["Name"],
                    "condition": lambda v: v,
                },
            ),
            (
                "FavourCost",
                {
                    "template": "master_favour_cost",
                    #'condition': lambda v: v,
                },
            ),
            (
                "MasterLevel",
                {
                    "template": "master_level_requirement",
                    #'condition': lambda v: v,
                },
            ),
            (
                "Variation_AOFiles",
                {
                    "template": "variation_count",
                    "format": lambda v: len(v),
                },
            ),
        ),
        row_index=True,
        function="_apply_master_map",
    )

    _regex_format = re.compile(
        r"(?P<index>x|y|z)"
        r"(?:[\W]*)"
        r"(?P<tag>%|second)",
        re.IGNORECASE,
    )
    _files = [
        "BaseItemTypes.dat",
    ]
    _translations = [
        "stat_descriptions.txt",
        "gem_stat_descriptions.txt",
        "skill_stat_descriptions.txt",
        "active_skill_gem_stat_descriptions.txt",
    ]
    _item_column_index_filter = partialmethod(
        SkillParserShared._column_index_filter,
        dat_file_name="BaseItemTypes.dat",
        error_msg="Several items have not been found:\n%s",
    )
    _MAP_COLORS = {
        "mid tier": "255,210,100",
        "high tier": "240,30,10",
    }
    _MAP_RELEASE_VERSION = {
        "Betrayal": "3.5.0",
        "Synthesis": "3.6.0",
        "Legion": "3.7.0",
        "Blight": "3.8.0",
        "Metamorphosis": "3.9.0",
        "Delirium": "3.10.0",
        "Harvest": "3.11.0",
        "Heist": "3.12.0",
    }
    _IGNORE_DROP_LEVEL_CLASSES = (
        "HideoutDoodad",
        "Microtransaction",
        "LabyrinthItem",
        "LabyrinthTrinket",
        "LabyrinthMapItem",
    )
    _IGNORE_DROP_LEVEL_ITEMS_BY_ID = {
        # Alchemy Shard
        "Metadata/Items/Currency/CurrencyUpgradeToRareShard",
        # Alteration Shard
        "Metadata/Items/Currency/CurrencyRerollMagicShard",
        "Metadata/Items/Currency/CurrencyLabyrinthEnchant",
        "Metadata/Items/Currency/CurrencyImprint",
        # Transmute Shard
        "Metadata/Items/Currency/CurrencyUpgradeToMagicShard",
        "Metadata/Items/Currency/CurrencyIdentificationShard",
    }
    _DROP_DISABLED_ITEMS_BY_ID = {
        "Metadata/Items/Quivers/Quiver1",
        "Metadata/Items/Quivers/Quiver2",
        "Metadata/Items/Quivers/Quiver3",
        "Metadata/Items/Quivers/Quiver4",
        "Metadata/Items/Quivers/Quiver5",
        "Metadata/Items/Quivers/QuiverDescent",
        "Metadata/Items/Rings/RingVictor1",
        # Eternal Orb
        "Metadata/Items/Currency/CurrencyImprintOrb",
        # Demigod items
        "Metadata/Items/Belts/BeltDemigods1",
        "Metadata/Items/Rings/RingDemigods1",
    }
    _NAME_OVERRIDE_BY_ID = {
        "English": {
            # =================================================================
            # One Hand Axes
            # =================================================================
            "Metadata/Items/Weapons/OneHandWeapons/OneHandAxes/OneHandAxe22": "",
            # =================================================================
            # Boots
            # =================================================================
            "Metadata/Items/Armours/Boots/BootsInt4": "",
            # Legion Boots
            "Metadata/Items/Armours/Boots/BootsStrInt7": "",
            "Metadata/Items/Armours/Boots/BootsAtlas1": " (Cold and Lightning Resistance)",
            "Metadata/Items/Armours/Boots/BootsAtlas2": " (Fire and Cold Resistance)",
            "Metadata/Items/Armours/Boots/BootsAtlas3": " (Fire and Lightning Resistance)",
            # =================================================================
            # Gloves
            # =================================================================
            # Legion Gloves
            "Metadata/Items/Armours/Gloves/GlovesStrInt7": "",
            # =================================================================
            # Quivers
            # =================================================================
            "Metadata/Items/Quivers/QuiverDescent": " (Descent)",
            # =================================================================
            # Rings
            # =================================================================
            "Metadata/Items/Rings/Ring12": " (ruby and topaz)",
            "Metadata/Items/Rings/Ring13": " (sapphire and topaz)",
            "Metadata/Items/Rings/Ring14": " (ruby and sapphire)",
            # =================================================================
            # Amulets
            # =================================================================
            "Metadata/Items/Amulets/Talismans/Talisman2_6_1": " (Fire Damage taken as Cold Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_2": " (Fire Damage taken as Lightning Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_3": " (Cold Damage taken as Fire Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_4": " (Cold Damage taken as Lightning Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_5": " (Lightning Damage taken as Cold Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_6": " (Lightning Damage taken as Fire Damage)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_1": "  (Power Charge on Kill)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_2": "  (Frenzy Charge on Kill)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_3": "  (Endurance Charge on Kill)",
            # =================================================================
            # Hideout Doodads
            # =================================================================
            "Metadata/Items/Hideout/HideoutLightningCoil": " (hideout doodad)",
            # =================================================================
            # Piece
            # =================================================================
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_1": " (1 of 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_2": " (2 of 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_3": " (3 of 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_4": " (4 of 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_1": " (1 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_2": " (2 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_3": " (3 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_1": " (1 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_2": " (2 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_3": " (3 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_1": " (1 of 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_2": " (2 of 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_1": " (1 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_2": " (2 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_3": " (3 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_1": " (1 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_2": " (2 of 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_3": " (3 of 3)",
            # =================================================================
            # MTX
            # =================================================================
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x1": " (1x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x2": " (1x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x3": " (1x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x4": " (1x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x1": " (2x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x2": " (2x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x3": " (2x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x4": " (2x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x2": " (3x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x3": " (3x3)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionIronMaiden": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "InfernalAxe": " (Weapon Skin)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionColossusSword": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionBoots": " (microtransaction)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionGloves": " (microtransaction)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "ScholarBoots": " (microtransaction)",
            "Metadata/Items/Pets/DemonLion": " (Pet)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionHooded"
            "Cloak": " (microtransaction)",
            # =================================================================
            # Quest items
            # =================================================================
            "Metadata/Items/QuestItems/GoldenPages/Page1": " (1 of 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page2": " (2 of 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page3": " (3 of 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page4": " (4 of 4)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_1": " (1 of 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_2": " (2 of 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_1": " (1 of 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_2": " (2 of 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_3": " (3 of 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_1": " (1 of 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_2": " (2 of 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_3": " (3 of 3)",
            # =================================================================
            # Misc
            # =================================================================
            "Metadata/Items/Heist/HeistEquipmentCloak3": "",
        },
        "Russian": {
            # =================================================================
            # Active Skill Gems
            # =================================================================
            "Metadata/Items/Gems/SkillGemPortal": " (камень умения)",
            # =================================================================
            # One Hand Axes
            # =================================================================
            "Metadata/Items/Weapons/OneHandWeapons/OneHandAxes/OneHandAxe22": "",
            # =================================================================
            # Boots
            # =================================================================
            "Metadata/Items/Armours/Boots/BootsInt4": "",
            # Legion Boots
            "Metadata/Items/Armours/Boots/BootsStrInt7": "",
            "Metadata/Items/Armours/Boots/BootsAtlas1": " (сопротивление холоду и молнии)",
            "Metadata/Items/Armours/Boots/BootsAtlas2": " (сопротивление огню и холоду)",
            "Metadata/Items/Armours/Boots/BootsAtlas3": " (сопротивление огню и молнии)",
            # =================================================================
            # Gloves
            # =================================================================
            # Legion Gloves
            "Metadata/Items/Armours/Gloves/GlovesStrInt7": "",
            # =================================================================
            # Quivers
            # =================================================================
            "Metadata/Items/Quivers/QuiverDescent": " (Спуск)",
            # =================================================================
            # Rings
            # =================================================================
            "Metadata/Items/Rings/Ring12": " (рубин и топаз)",
            "Metadata/Items/Rings/Ring13": " (сапфир и топаз)",
            "Metadata/Items/Rings/Ring14": " (рубин и сапфир)",
            # =================================================================
            # Amulets
            # =================================================================
            "Metadata/Items/Amulets/Talismans/Talisman2_6_1": " (получаемый урон от огня становится уроном от холода)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_2": " (получаемый урон от огня становится уроном от молнии)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_3": " (получаемый урон от холода становится уроном от огня)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_4": " (получаемый урон от холода становится уроном от молнии)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_5": " (получаемый урон от молнии становится уроном от холода)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_6": " (получаемый урон от молнии становится уроном от огня)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_1": " (заряд энергии при убийстве)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_2": " (заряд ярости при убийстве)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_3": " (заряд выносливости при убийстве)",
            # =================================================================
            # Hideout Doodads
            # =================================================================
            "Metadata/Items/Hideout/HideoutMalachaiHeart": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutVaalWhispySmoke": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutChestVaal": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutEncampmentFireplace": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutEncampmentLetters": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutIncaPyramid": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutDarkSoulercoaster": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutVaalMechanism": " (предмет убежища)",
            "Metadata/Items/Hideout/HideoutCharredSkeleton": " (предмет убежища)",
            "Metadata/Items/HideoutInteractables/DexIntCraftingBench": " (предмет убежища)",
            # =================================================================
            # Piece
            # =================================================================
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_1": " (1 из 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_2": " (2 из 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_3": " (3 из 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_4": " (4 из 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_1": " (1 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_2": " (2 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_3": " (3 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_1": " (1 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_2": " (2 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_3": " (3 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_1": " (1 из 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_2": " (2 из 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_1": " (1 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_2": " (2 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_3": " (3 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_1": " (1 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_2": " (2 из 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_3": " (3 из 3)",
            # =================================================================
            # MTX
            # =================================================================
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x1": " (1x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x2": " (1x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x3": " (1x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x4": " (1x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x1": " (2x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x2": " (2x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x3": " (2x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x4": " (2x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x2": " (3x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x3": " (3x3)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionIronMaiden": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "InfernalAxe": " (внешний вид оружия)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionColossusSword": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionBoots": " (микротранзакция)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionGloves": " (микротранзакция)",
            "Metadata/Items/MicrotransactionItemEffects/MasterArmour1Boots": " (микротранзакция)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "SinFootprintsEffect": " (микротранзакция)",
            "Metadata/Items/Pets/DemonLion": " (питомец)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionHeartWeapon2014": " (2014)",
            # =================================================================
            # Quest items
            # =================================================================
            "Metadata/Items/QuestItems/GoldenPages/Page1": " (1 из 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page2": " (2 из 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page3": " (3 из 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page4": " (4 из 4)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_1": " (1 из 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_2": " (2 из 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_1": " (1 из 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_2": " (2 из 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_3": " (3 из 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_1": " (1 из 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_2": " (2 из 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_3": " (3 из 3)",
            "Metadata/Items/QuestItems/RibbonSpool": " (предмет)",
            "Metadata/Items/QuestItems/Act7/SilverLocket": " (предмет)",
            "Metadata/Items/QuestItems/Act7/KisharaStar": " (предмет)",
            "Metadata/Items/QuestItems/Act8/WingsOfVastiri": " (предмет)",
            "Metadata/Items/QuestItems/Act9/StormSword": " (предмет)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_1": " (1 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_2": " (2 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_3": " (3 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_4": " (4 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_5": " (5 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_6": " (6 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_7": " (7 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade1_8": " (8 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_1": " (1 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_2": " (2 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_3": " (3 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_4": " (4 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_5": " (5 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_6": " (6 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_7": " (7 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade2_8": " (8 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_1": " (1 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_2": " (2 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_3": " (3 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_4": " (4 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_5": " (5 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_6": " (6 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_7": " (7 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade3_8": " (8 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_1": " (1 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_2": " (2 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_3": " (3 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_4": " (4 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_5": " (5 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_6": " (6 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_7": " (7 из 8)",
            "Metadata/Items/AtlasUpgrades/AtlasRegionUpgrade4_8": " (8 из 8)",
        },
        "German": {
            # =================================================================
            # One Hand Axes
            # =================================================================
            "Metadata/Items/Weapons/OneHandWeapons/OneHandAxes/OneHandAxe22": "",
            # =================================================================
            # Boots
            # =================================================================
            "Metadata/Items/Armours/Boots/BootsInt4": "",
            # Legion Boots
            "Metadata/Items/Armours/Boots/BootsStrInt7": "",
            "Metadata/Items/Armours/Boots/BootsAtlas1": " (Kälte und Blitz Resistenzen)",
            "Metadata/Items/Armours/Boots/BootsAtlas2": " (Feuer und Kälte Resistenzen)",
            "Metadata/Items/Armours/Boots/BootsAtlas3": " (Feuer und Blitz Resistenzen)",
            # =================================================================
            # Gloves
            # =================================================================
            # Legion Gloves
            "Metadata/Items/Armours/Gloves/GlovesStrInt7": "",
            # =================================================================
            # Quivers
            # =================================================================
            "Metadata/Items/Quivers/QuiverDescent": " (Descent)",
            # =================================================================
            # Rings
            # =================================================================
            "Metadata/Items/Rings/Ring12": " (Rubin und Topas)",
            "Metadata/Items/Rings/Ring13": " (Saphir und Topas)",
            "Metadata/Items/Rings/Ring14": " (Rubin und Saphir)",
            # =================================================================
            # Amulets
            # =================================================================
            "Metadata/Items/Amulets/Talismans/Talisman2_6_1": " (Feuerschaden erlitten als Kälteschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_2": " (Feuerschaden erlitten als Blitzschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_3": " (Kälteschaden erlitten als Feuerschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_4": " (Kälteschaden erlitten als Blitzschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_5": " (Blitzschaden erlitten als Kälteschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman2_6_6": " (Blitzschaden erlitten als Feuerschaden)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_1": " (Energie-Ladung bei Tötung)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_2": " (Raserei-Ladung bei Tötung)",
            "Metadata/Items/Amulets/Talismans/Talisman3_6_3": " (Widerstands-Ladung bei Tötung)",
            # =================================================================
            # Hideout Doodads
            # =================================================================
            "Metadata/Items/Hideout/HideoutLightningCoil": " (Dinge fürs Versteck)",
            # =================================================================
            # Piece
            # =================================================================
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_1": " (1 von 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_2": " (2 von 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_3": " (3 von 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueShield1_4": " (4 von 4)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_1": " (1 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_2": " (2 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueSword1_3": " (3 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_1": " (1 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_2": " (2 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueStaff1_3": " (3 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_1": " (1 von 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueBelt1_2": " (2 von 2)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_1": " (1 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_2": " (2 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueQuiver1_3": " (3 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_1": " (1 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_2": " (2 von 3)",
            "Metadata/Items/UniqueFragments/FragmentUniqueHelmet1_3": " (3 von 3)",
            # =================================================================
            # MTX
            # =================================================================
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x1": " (1x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x2": " (1x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x3": " (1x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox1x4": " (1x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x1": " (2x1)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x2": " (2x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x3": " (2x3)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox2x4": " (2x4)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x2": " (3x2)",
            "Metadata/Items/MicrotransactionCurrency/MysteryBox3x3": " (3x3)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionIronMaiden": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "InfernalAxe": " (Weapon Skin)",
            "Metadata/Items/MicrotransactionItemEffects/MicrotransactionColossusSword": "",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionBoots": " (Mikrotransaktion)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "LegionGloves": " (Mikrotransaktion)",
            "Metadata/Items/MicrotransactionItemEffects/Microtransaction"
            "ScholarBoots": " (Mikrotransaktion)",
            "Metadata/Items/Pets/DemonLion": " (Haustier)",
            # =================================================================
            # Quest items
            # =================================================================
            "Metadata/Items/QuestItems/GoldenPages/Page1": " (1 von 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page2": " (2 von 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page3": " (3 von 4)",
            "Metadata/Items/QuestItems/GoldenPages/Page4": " (4 von 4)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_1": " (1 von 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier8_2": " (2 von 2)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_1": " (1 von 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_2": " (2 von 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier9_3": " (3 von 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_1": " (1 von 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_2": " (2 von 3)",
            "Metadata/Items/QuestItems/MapUpgrades/MapUpgradeTier10_3": " (3 von 3)",
            # =================================================================
            # =================================================================
            # ==================== Germany only conflicts =====================
            # =================================================================
            # =================================================================
            # Schleifstein
            "Metadata/Items/Currency/CurrencyWeaponQuality": "",
            "Metadata/Items/HideoutInteractables/StrDexCraftingBench": " (Dinge fürs Versteck)",
        },
    }
    _LANG = {
        "English": {
            "Low": "Low Tier",
            "Mid": "Mid Tier",
            "High": "High Tier",
            "Uber": "Max Tier",
            "decoration": "%s (%s %s decoration)",
            "decoration_wounded": "%s (%s %s decoration, Wounded)",
            "of": "%s of %s",
            "descent": "Descent",
        },
        "German": {
            "Low": "Niedrige Stufe",
            "Mid": "Mittlere Stufe",
            "High": "Hohe Stufe",
            "Uber": "Maximale Stufe",
            "decoration": "%s (%s %s Dekoration)",
            "decoration_wounded": "%s (%s %s Dekoration, verletzt)",
            "of": "%s von %s",
            "descent": "Descent",
        },
        "Russian": {
            "Low": "низкий уровень",
            "Mid": "средний уровень",
            "High": "высокий уровень",
            "Uber": "максимальный уровень",
            "decoration": "%s (%s %s предмет убежища)",
            "decoration_wounded": "%s (%s %s предмет убежища, Раненый)",
            "of": "%s из %s",
            "descent": "Спуск",
        },
    }
    _SKIP_ITEMS_BY_ID = {
        #
        # Active Skill Gems
        #
        "Metadata/Items/Gems/SkillGemBackstab",
        "Metadata/Items/Gems/SkillGemBladeTrap",
        "Metadata/Items/Gems/SkillGemBlitz",
        "Metadata/Items/Gems/SkillGemBloodWhirl",
        "Metadata/Items/Gems/SkillGemBoneArmour",
        "Metadata/Items/Gems/SkillGemCaptureMonster",
        "Metadata/Items/Gems/SkillGemCoilingAssault",
        "Metadata/Items/Gems/SkillGemComboStrike",
        "Metadata/Items/Gems/SkillGemDamageInfusion",
        "Metadata/Items/Gems/SkillGemDiscorectangleSlam",
        "Metadata/Items/Gems/SkillGemElementalProjectiles",
        "Metadata/Items/Gems/SkillGemFireWeapon",
        "Metadata/Items/Gems/SkillGemHeraldOfBlood",
        "Metadata/Items/Gems/SkillGemIceFire",
        "Metadata/Items/Gems/SkillGemIcefire",
        "Metadata/Items/Gems/SkillGemIgnite",
        "Metadata/Items/Gems/SkillGemInfernalSwarm",
        "Metadata/Items/Gems/SkillGemInfernalSweep",
        "Metadata/Items/Gems/SkillGemLightningChannel",
        "Metadata/Items/Gems/SkillGemLightningCircle",
        "Metadata/Items/Gems/SkillGemLightningTendrilsChannelled",
        "Metadata/Items/Gems/SkillGemNewBladeVortex",
        "Metadata/Items/Gems/SkillGemNewPunishment",
        "Metadata/Items/Gems/SkillGemNewShockNova",
        "Metadata/Items/Gems/SkillGemProjectilePortal",
        "Metadata/Items/Gems/SkillGemQuickBlock",
        "Metadata/Items/Gems/SkillGemRendingSteel",
        "Metadata/Items/Gems/SkillGemReplicate",
        "Metadata/Items/Gems/SkillGemRighteousLightning",
        "Metadata/Items/Gems/SkillGemRiptide",
        "Metadata/Items/Gems/SkillGemSerpentStrike",
        "Metadata/Items/Gems/SkillGemShadowBlades",
        "Metadata/Items/Gems/SkillGemSlashTotem",
        "Metadata/Items/Gems/SkillGemSliceAndDice",
        "Metadata/Items/Gems/SkillGemSnipe",
        "Metadata/Items/Gems/SkillGemSpectralSpinningWeapon",
        "Metadata/Items/Gems/SkillGemStaticTether",
        "Metadata/Items/Gems/SkillGemSummonSkeletonsChannelled",
        "Metadata/Items/Gems/SkillGemTouchOfGod",
        "Metadata/Items/Gems/SkillGemVaalFireTrap",
        "Metadata/Items/Gems/SkillGemVaalFleshOffering",
        "Metadata/Items/Gems/SkillGemVaalHeavyStrike",
        "Metadata/Items/Gems/SkillGemVaalSweep",
        "Metadata/Items/Gems/SkillGemVortexMine",
        "Metadata/Items/Gems/SkillGemWandTeleport",
        "Metadata/Items/Gems/SkillGemNewPhaseRun",
        "Metadata/Items/Gems/SkillGemNewArcticArmour",
        #
        # Support Skill Gems
        #
        "Metadata/Items/Gems/SupportGemCastLinkedCursesOnCurse",
        "Metadata/Items/Gems/SupportGemHandcastRapidFire",
        "Metadata/Items/Gems/SupportGemSplit",
        "Metadata/Items/Gems/SupportGemReturn",
        "Metadata/Items/Gems/SupportGemTemporaryForTutorial",
        "Metadata/Items/Gems/SupportGemVaalSoulHarvesting",
        #
        # MTX
        #
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionSpectralThrowEbony",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionFirstBlood",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionFirstBloodWeaponEffect",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionTitanPlate",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionStatueSummonSkeletons2",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionStatueSummonSkeletons3",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionStatueSummonSkeletons4",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionAlternatePortal",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionBloodSlam",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionNewRaiseSpectre",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionNewRaiseZombie",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionNewTotem",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionPlinthWarp",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionWhiteWeapon",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionYellowWeapon",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionHeartWeapon2015",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionPortalSteam1",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionTestCharacterPortrait",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionTestCharacterPortrait2",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionAuraEffect1",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionAuraEffect2",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionAuraEffect3",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionAuraEffect4",
        "Metadata/Items/MicrotransactionSkillEffects/MicrotransactionBloodRavenSummonRagingSpirit",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionMarkOfThePhoenixPurple",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionWuqiWeaponEffect",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionBlackguardCape",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionDemonhandClaw",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionDivineShield",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionEldritchWings",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent1Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent2Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent3Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent4Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent5Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent6Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencent7Frame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge1_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge2_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge3_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge4_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge5_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge6_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge7_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge8_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge9_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentBadge10_7",
        "Metadata/Items/MicrotransactionItemEffects/MicrotransactionTencentInfernalWeapon",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory0to1",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory1to2",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory2to3",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory3to4",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory4to5",
        "Metadata/Items/MicrotransactionCurrency/MicrotransactionTencentExpandInventory5to6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame1_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame2_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame3_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame4_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame5_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame6_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame7_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame8_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame9_7",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_1",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_2",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_3",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_4",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_5",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_6",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentGradingFrame10_7",
        "Metadata/Items/MicrotrransactionCharacterEffects/MicrotransactionTencentTopPlayerFrame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentS3HideOutFrame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentS3FashionFrame",
        "Metadata/Items/MicrotransactionCharacterEffects/MicrotransactionTencentS3BDMasterFrame",
        "Metadata/Items/MicrotransactionCurrency/TradeMarketTab",
        "Metadata/Items/MicrotransactionCurrency/TradeMarketBuyoutTab",
        #
        # Hideout Doodads
        #
        # Hideout totem test variants, not needed
        "Metadata/Items/Hideout/HideoutTotemPoleTest",
        "Metadata/Items/Hideout/HideoutTotemPole2Test",
        "Metadata/Items/Hideout/HideoutTotemPole3Test",
        "Metadata/Items/Hideout/HideoutTotemPole4Test",
        "Metadata/Items/Hideout/HideoutTotemPole5Test",
        "Metadata/Items/Hideout/HideoutTotemPole6Test",
        "Metadata/Items/Hideout/HideoutTotemPole7Test",
        "Metadata/Items/Hideout/HideoutTotemPole8Test",
        "Metadata/Items/Hideout/HideoutTotemPole9Test",
        "Metadata/Items/Hideout/HideoutTotemPole10Test",
        "Metadata/Items/Hideout/HideoutTotemPole11Test",
        "Metadata/Items/Hideout/HideoutTotemPole12Test",
        "Metadata/Items/Hideout/HideoutTotemPole13Test",
        "Metadata/Items/Hideout/HideoutTotemPole14Test",
        "Metadata/Items/Hideout/HideoutTotemPole15Test",
        "Metadata/Items/Hideout/HideoutTotemPole16Test",
        "Metadata/Items/Hideout/HideoutTotemPole17Test",
        "Metadata/Items/Hideout/HideoutTotemPole18Test",
        "Metadata/Items/Hideout/HideoutTotemPole19Test",
        "Metadata/Items/Hideout/HideoutTotemPole20Test",
        "Metadata/Items/Hideout/HideoutTotemPole21Test",
        #
        # Stackable currency
        #
        # Legacy variants of items before item stash tabs
        "Metadata/Items/Delve/DelveSocketableCurrencyUpgrade1",
        "Metadata/Items/Delve/DelveSocketableCurrencyUpgrade2",
        "Metadata/Items/Delve/DelveSocketableCurrencyUpgrade3",
        "Metadata/Items/Delve/DelveSocketableCurrencyUpgrade4",
        "Metadata/Items/Delve/DelveSocketableCurrencyReroll1",
        "Metadata/Items/Delve/DelveSocketableCurrencyReroll2",
        "Metadata/Items/Delve/DelveSocketableCurrencyReroll3",
        "Metadata/Items/Delve/DelveSocketableCurrencyReroll4",
        "Metadata/Items/MapFragments/VaalFragment1_1",
        "Metadata/Items/MapFragments/VaalFragment1_2",
        "Metadata/Items/MapFragments/VaalFragment1_3",
        "Metadata/Items/MapFragments/VaalFragment1_4",
        "Metadata/Items/MapFragments/VaalFragment2_1",
        "Metadata/Items/MapFragments/VaalFragment2_2",
        "Metadata/Items/MapFragments/VaalFragment2_3",
        "Metadata/Items/MapFragments/VaalFragment2_4",
        "Metadata/Items/MapFragments/ProphecyFragment1",
        "Metadata/Items/MapFragments/ProphecyFragment2",
        "Metadata/Items/MapFragments/ProphecyFragment3",
        "Metadata/Items/MapFragments/ProphecyFragment4",
        "Metadata/Items/MapFragments/ShaperFragment1",
        "Metadata/Items/MapFragments/ShaperFragment2",
        "Metadata/Items/MapFragments/ShaperFragment3",
        "Metadata/Items/MapFragments/ShaperFragment4",
        "Metadata/Items/MapFragments/FragmentPantheonFlask",
        "Metadata/Items/MapFragments/BreachFragmentFire",
        "Metadata/Items/MapFragments/BreachFragmentCold",
        "Metadata/Items/MapFragments/BreachFragmentLightning",
        "Metadata/Items/MapFragments/BreachFragmentPhysical",
        "Metadata/Items/MapFragments/BreachFragmentChaos",
        "Metadata/Items/Labyrinth/OfferingToTheGoddess",
        #
        # Misc
        #
        "Metadata/Items/Heist/HeistEquipmentToolTest",
        "Metadata/Items/Heist/HeistEquipmentWeaponTest",
        "Metadata/Items/Heist/HeistEquipmentUtilityTest",
        "Metadata/Items/Heist/HeistEquipmentRewardTest",
    }
    _attribute_map = OrderedDict(
        (
            ("Str", "strength"),
            ("Dex", "dexterity"),
            ("Int", "intelligence"),
        )
    )

    def __init__(
        self,
        base_path: str,
        parsed_args: Any,
        *,
        # Dependency injection parameters (optional, passed to BaseParser)
        file_system: Any | None = None,
        specification: Any | None = None,
        relational_reader: Any | None = None,
        translation_cache: Any | None = None,
        ot_cache: Any | None = None,
        custom_translation: Any | None = None,
        language: str | None = None,
        relational_reader_english: Any | None = None,
    ):
        """
        Initialize ItemsParser with composition of specialized classes.

        Args:
            base_path: Base path for output files
            parsed_args: Parsed command-line arguments
            file_system: FileSystem instance (optional, created if None)
            specification: Specification instance (optional, loaded if None)
            relational_reader: RelationalReader instance (optional, created if None)
            translation_cache: TranslationFileCache instance (optional, created if None)
            ot_cache: OTFileCache instance (optional, created if None)
            custom_translation: Custom TranslationFile (optional, loaded if None)
            language: Language code (optional, from config if None)
            relational_reader_english: Optional RelationalReader for English language
        """
        # Initialize BaseParser (via SkillParserShared)
        super().__init__(
            base_path=base_path,
            parsed_args=parsed_args,
            file_system=file_system,
            specification=specification,
            relational_reader=relational_reader,
            translation_cache=translation_cache,
            ot_cache=ot_cache,
            custom_translation=custom_translation,
            language=language,
        )

        # Store parsed_args and language for use in specialized classes
        self._parsed_args = parsed_args
        self._language = self.lang  # BaseParser sets self.lang

        # Handle English RelationalReader (for cross-language links)
        if self._language != "English":
            if relational_reader_english is not None:
                self.rr2 = relational_reader_english
            else:
                # Create English RelationalReader if not provided
                from PyPoE.poe.file.dat import RelationalReader

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

        # Create specialized classes via composition
        # 1. ItemConflictResolver
        self._conflict_resolver = ItemConflictResolver(
            relational_reader=self.rr,
            language=self._language,
            lang_map=self._LANG,
            format_map_name=self._format_map_name,
        )

        # Create conflict resolver map with wrapper methods that delegate to _conflict_resolver
        # The wrapper methods match the signature expected by ItemDataExtractor:
        # resolver(self, infobox, base_item_type_lang, rr, language)
        def create_conflict_wrapper(item_type: str):
            def wrapper(
                extractor: Any,
                infobox: dict[str, Any],
                base_item_type: Any,
                rr: Any,
                language: str,
            ) -> str | None:
                return self._conflict_resolver.resolve_conflict(item_type, infobox, base_item_type)

            return wrapper

        # Override the property with actual map
        self._conflict_resolver_map = {
            "Active Skill Gem": create_conflict_wrapper("Active Skill Gem"),
            "QuestItem": create_conflict_wrapper("QuestItem"),
            "HideoutDoodad": create_conflict_wrapper("HideoutDoodad"),
            "Map": create_conflict_wrapper("Map"),
            "MapFragment": create_conflict_wrapper("MapFragment"),
            "DivinationCard": create_conflict_wrapper("DivinationCard"),
            "LabyrinthMapItem": create_conflict_wrapper("LabyrinthMapItem"),
            "MiscMapItem": create_conflict_wrapper("MiscMapItem"),
            "DelveSocketableCurrency": create_conflict_wrapper("DelveSocketableCurrency"),
            "DelveStackableSocketableCurrency": create_conflict_wrapper(
                "DelveStackableSocketableCurrency"
            ),
            "AtlasRegionUpgradeItem": create_conflict_wrapper("AtlasRegionUpgradeItem"),
        }

        # 2. ItemWikiExporter
        self._wiki_exporter = ItemWikiExporter(
            relational_reader=self.rr,
            file_system=self.file_system,
            language=self._language,
            lang_map=self._LANG,
            map_colors=self._MAP_COLORS,
            map_release_version=self._MAP_RELEASE_VERSION,
            relational_reader_english=self.rr2,
            image_init=self._image_init,
            write_dds=self._write_dds,
            format_map_name=self._format_map_name,
            get_map_series=self._get_map_series,
            process_base_item_type=self._process_base_item_type,
            process_purchase_costs=self._process_purchase_costs,
            type_map=self._type_map,
            img_path=self._img_path,
        )

        # 3. ItemSkillHandler
        self._skill_handler = ItemSkillHandler(
            relational_reader=self.rr,
            language=self._language,
            attribute_map=self._attribute_map,
            conflict_active_skill_gems_map=self._conflict_active_skill_gems_map,
            skill_processor=self._skill,
            parsed_args=self._parsed_args,
        )

        # 4. ItemTypeParser
        self._type_parser = ItemTypeParser(
            relational_reader=self.rr,
            translation_cache=self.tc,
            language=self._language,
            lang_map=self._LANG,
            get_stats=self._get_stats,
        )

        # 5. ItemDataExtractor
        self._data_extractor = ItemDataExtractor(
            relational_reader=self.rr,
            translation_cache=self.tc,
            file_system=self.file_system,
            language=self._language,
            lang_map=self._LANG,
            skip_items_by_id=self._SKIP_ITEMS_BY_ID,
            drop_disabled_items_by_id=self._DROP_DISABLED_ITEMS_BY_ID,
            ignore_drop_level_classes=self._IGNORE_DROP_LEVEL_CLASSES,
            ignore_drop_level_items_by_id=self._IGNORE_DROP_LEVEL_ITEMS_BY_ID,
            name_override_by_id=self._NAME_OVERRIDE_BY_ID,
            conflict_resolver_map=self._conflict_resolver_map,
            cls_map=self._cls_map,
            relational_reader_english=self.rr2,
            process_base_item_type=self._process_base_item_type,
            process_purchase_costs=self._process_purchase_costs,
            image_init=self._image_init,
            write_dds=self._write_dds,
            img_path=self._img_path,
        )

    # =============================================================================
    # Internal methods (used by specialized classes)
    # =============================================================================

    def _process_base_item_type(self, base_item_type: Any, infobox: dict[str, Any], not_new_map: bool = True) -> None:
        """
        Process base item type information.

        This method is used by multiple specialized classes and should remain in ItemsParser.
        """
        from PyPoE.cli.exporter.wiki import parser
        from PyPoE.poe.file.ot import OTFile

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

    def _process_purchase_costs(self, source: Any, infobox: dict[str, Any]) -> None:
        """
        Process purchase costs for items.

        This method is used by multiple specialized classes and should remain in ItemsParser.
        """
        from PyPoE.poe.constants import RARITY

        for rarity in RARITY:
            if rarity.id >= 5:  # type: ignore[attr-defined]
                break
            for i, (item, cost) in enumerate(
                source[rarity.name_upper + "Purchase"], start=1  # type: ignore[attr-defined]
            ):
                prefix = f"purchase_cost_{rarity.name_lower}{i}"  # type: ignore[attr-defined]
                infobox[prefix + "_name"] = item["Name"]
                infobox[prefix + "_amount"] = cost

    def _format_map_name(self, base_item_type: Any, map_series: Any | None, language: str | None = None) -> str:
        """
        Format map name.

        This method is used by multiple specialized classes and should remain in ItemsParser.
        """
        if language is None:
            language = self._language
        if "Harbinger" in base_item_type["Id"]:
            return "{} ({}) ({})".format(
                base_item_type["Name"],
                self._LANG[language][re.sub(r"^.*Harbinger", "", base_item_type["Id"])],
                map_series["Name"] if map_series else "",
            )
        else:
            return "{} ({})".format(base_item_type["Name"], map_series["Name"] if map_series else "")

    def _get_map_series(self, parsed_args: Any) -> Any | bool:
        """
        Get map series from parsed arguments.

        This method is used by export methods and should remain in ItemsParser.
        """
        from PyPoE.cli.core import Msg, console

        self.rr["MapSeries.dat"].build_index("Id")
        self.rr["MapSeries.dat"].build_index("Name")
        if parsed_args.map_series_id is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Id"][parsed_args.map_series_id]
            except (IndexError, KeyError):
                console("Invalid map series id", msg=Msg.error)
                return False
        elif parsed_args.map_series is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Name"][parsed_args.map_series][0]
            except (IndexError, KeyError):
                console("Invalid map series name", msg=Msg.error)
                return False
        else:
            map_series = self.rr["MapSeries.dat"][-1]
            console(
                'No map series specified. Using latest series "{}".'.format(map_series["Name"]),
                msg=Msg.warning,
            )

        return map_series

    def _type_map(self, infobox: dict[str, Any], base_item_type: Any) -> None:
        """
        Apply map-specific type information.

        This method is used by export methods and should remain in ItemsParser.
        """
        # This is a callback used by _type_map factory method
        # The actual implementation is in _type_map factory method
        pass

    # =============================================================================
    # Public methods (delegated to specialized classes)
    # =============================================================================

    def by_rowid(self, parsed_args: Any) -> Any:
        """Export items by row ID range."""
        return self._data_extractor.export_items(
            parsed_args,
            self.rr["BaseItemTypes.dat"][parsed_args.start : parsed_args.end],
        )

    def by_id(self, parsed_args: Any) -> Any:
        """Export items by ID."""
        return self._data_extractor.export_items(
            parsed_args,
            self._item_column_index_filter(column_id="Id", arg_list=parsed_args.id),
        )

    def by_name(self, parsed_args: Any) -> Any:
        """Export items by name."""
        return self._data_extractor.export_items(
            parsed_args,
            self._item_column_index_filter(column_id="Name", arg_list=parsed_args.name),
        )

    def by_filter(self, parsed_args: Any) -> Any:
        """Export items by filter (regex)."""
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

        return self._data_extractor.export_items(parsed_args, items)

    def export_map_icons(self, parsed_args: Any) -> Any:
        """Export map icons."""
        return self._wiki_exporter.export_map_icons(parsed_args)

    def export_map(self, parsed_args: Any) -> Any:
        """Export map data."""
        return self._wiki_exporter.export_map(parsed_args)

    def _skill_gem(self, infobox: dict[str, Any], base_item_type: Any) -> bool:
        """Process skill gem item."""
        return self._skill_handler.process_skill_gem(infobox, base_item_type)

    def export(self, parsed_args: Any) -> Any:
        """
        Export items (backward compatibility method).

        This method provides backward compatibility for tests and other code
        that uses the old API. It delegates to by_name() if 'item' is in parsed_args,
        or to by_id() if 'id' is in parsed_args.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            ExporterResult instance
        """
        # Backward compatibility: check for 'item' attribute (old API)
        if hasattr(parsed_args, "item") and parsed_args.item:
            # Convert to new API format
            parsed_args.name = parsed_args.item
            return self.by_name(parsed_args)
        elif hasattr(parsed_args, "id") and parsed_args.id:
            return self.by_id(parsed_args)
        elif hasattr(parsed_args, "name") and parsed_args.name:
            return self.by_name(parsed_args)
        else:
            # Fallback to by_filter if no specific method is available
            return self.by_filter(parsed_args)
